from __future__ import annotations
import logging
from litestar import Controller, post, Request, Response
from litestar.datastructures import Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.schemas.client.checkout import (
    StealthCheckoutSchema,
    CustomerLookupSchema,
    CustomerLookupResponseSchema,
    CheckoutPreviewRequest,
)
from backend.schemas.common import SuccessResponse
from backend.schemas.pricing import PricingBreakdown, PricingInputItem
from backend.services.commerce.checkout import CheckoutService
from backend.schemas.agent import AgentErrorCode, AgentErrorResponse
from litestar.exceptions import ValidationException, NotFoundException, PermissionDeniedException
from backend.utils.uid import new_short_id

logger = logging.getLogger("api-gateway")

# ── Error code mapper — keywords trong message → AgentErrorCode ───────────
_CHECKOUT_ERROR_MAP: list[tuple[str, AgentErrorCode, bool, int | None]] = [
    # (keyword_in_detail, error_code, retry, retry_after_seconds)
    ("spam",            AgentErrorCode.SPAM_BLOCKED,      False, None),
    ("bất thường",      AgentErrorCode.SPAM_BLOCKED,      False, None),
    ("thay đổi về giá", AgentErrorCode.PRICE_MISMATCH,    True,  5),
    ("giá sản phẩm đã thay đổi", AgentErrorCode.PRICE_CHANGED, True, 5),
    ("không tồn tại",   AgentErrorCode.PRODUCT_NOT_FOUND, False, None),
    ("hết hàng",        AgentErrorCode.OUT_OF_STOCK,      False, None),
    ("tối thiểu",       AgentErrorCode.MIN_AMOUNT,        False, None),
    ("50%",             AgentErrorCode.EXTREME_DISCOUNT,  False, None),
    ("chưa được mở khóa", AgentErrorCode.VOUCHER_LOCKED,  False, None),
    ("mã giảm giá",     AgentErrorCode.VOUCHER_INVALID,   False, None),
    ("thiết quân luật", AgentErrorCode.SYSTEM_READONLY,   True,  60),
    ("phong tỏa",       AgentErrorCode.SYSTEM_READONLY,   True,  60),
    ("đã được tạo trước", AgentErrorCode.IDEMPOTENT_REPLAY, False, None),
]

def _map_error(detail: str) -> tuple[AgentErrorCode, bool, int | None]:
    dl = detail.lower()
    for kw, code, retry, after in _CHECKOUT_ERROR_MAP:
        if kw.lower() in dl:
            return code, retry, after
    return AgentErrorCode.UNKNOWN, False, None


class CheckoutController(Controller):
    path = "/api/v1/client/checkout"

    @post("/stealth", guards=[])
    async def create_stealth_order(
        self,
        request: Request,
        db_session: AsyncSession,
        data: StealthCheckoutSchema
    ) -> Response:
        """Handle stealth checkout with CTV attribution + anti-fraud integration."""
        ip = request.client.host if request.client else "unknown"
        if forwarded_for := request.headers.get("x-forwarded-for"):
            ip = forwarded_for.split(",")[0].strip()

        ua = request.headers.get("user-agent", "unknown")
        user_id = request.scope.get("state", {}).get("user", {}).get("id")

        # CTV Attribution: Cookie __ctv (priority) > payload.ctv_code (manual input)
        ctv_code: str | None = None
        attribution_source: str | None = None
        cookie_ctv = request.cookies.get("__ctv")
        payload_ctv = getattr(data, "ctv_code", None)

        if cookie_ctv:
            ctv_code = cookie_ctv.strip()
            attribution_source = "cookie"
        elif payload_ctv:
            ctv_code = payload_ctv.strip()
            attribution_source = "manual"

        from backend.services.agent_monitor import AgentMonitor
        is_agent_req = request.scope.get("state", {}).get("is_agent", False) or getattr(data, "sandbox", False)
        try:
            res = await CheckoutService.create_stealth_order(
                db_session, data, ip, ua,
                user_id=user_id,
                ctv_code=ctv_code,
                attribution_source=attribution_source,
            )
            if is_agent_req and res["ok"]:
                await AgentMonitor.record_order(is_sandbox=getattr(data, "sandbox", False))
                await AgentMonitor.record_ip(ip)
        except (ValidationException, NotFoundException, PermissionDeniedException) as exc:
            # [Phase 1 — AI Gateway] Map lỗi business → AgentErrorCode machine-readable
            detail: str = str(getattr(exc, "detail", str(exc)))
            code, retry, retry_after = _map_error(detail)
            
            if is_agent_req:
                await AgentMonitor.record_error(code.value)
                await AgentMonitor.record_ip(ip)
                
            trace_id: str = new_short_id(8)
            hint_map: dict[AgentErrorCode, str] = {
                AgentErrorCode.PRICE_CHANGED:    "Re-fetch product price and recalculate total_amount before retrying.",
                AgentErrorCode.PRICE_MISMATCH:   "Call POST /checkout/preview first, then use returned final_payable as total_amount.",
                AgentErrorCode.OUT_OF_STOCK:     "Remove out-of-stock items and retry with remaining items.",
                AgentErrorCode.VOUCHER_INVALID:  "Remove voucher_ids and retry, or call GET /vouchers to validate first.",
                AgentErrorCode.SYSTEM_READONLY:  "System is in maintenance mode. Retry after retry_after seconds.",
                AgentErrorCode.IDEMPOTENT_REPLAY: "Order already created. Extract order_id from previous response.",
            }
            body = AgentErrorResponse(
                detail=detail,
                error_code=code,
                retry=retry,
                retry_after=retry_after,
                trace_id=trace_id,
                hint=hint_map.get(code),
            )
            http_status = 422 if code == AgentErrorCode.SPAM_BLOCKED else 400
            await db_session.rollback()
            return Response(content=body.model_dump(), status_code=http_status)

        response = Response(
            content=SuccessResponse(id=res["id"], ok=res["ok"])
        )

        if res["ok"] and res["id"]:

            cookie = Cookie(
                key="__ox",
                value=res["id"],
                max_age=86400,
                httponly=True,
                secure=True,
                samesite="lax",
                path="/"
            )
            response.set_cookie(cookie)

        return response

    @post("/lookup", guards=[])
    async def lookup_customer(
        self,
        request: Request,
        db_session: AsyncSession,
        data: CustomerLookupSchema
    ) -> CustomerLookupResponseSchema:
        ox_cookie = request.cookies.get("__ox")
        user_id = request.scope.get("state", {}).get("user", {}).get("id")
        res = await CheckoutService.lookup_customer(db_session, data.phone, ox_cookie=ox_cookie, user_id=user_id)
        return CustomerLookupResponseSchema(**res)

    @post("/preview", guards=[])
    async def preview_price(
        self,
        request: Request,
        db_session: AsyncSession,
        data: CheckoutPreviewRequest,
    ) -> PricingBreakdown:
        """
        [Phase 1 — AI Gateway] Tính giá preview không tạo đơn thật.
        AI Agent gọi endpoint này để lập kế hoạch thanh toán:
        - Kiểm tra tổng tiền sau voucher/điểm tích lũy
        - Xác nhận phí ship
        - Tránh bị từ chối khi tạo đơn thật do sai giá
        """
        from backend.database.models.promotion import Voucher, ComboDeal
        from backend.services.commerce.logic.pricing_engine import PricingEngine
        from backend.constants.commerce import ShippingConfig

        # 1. Fetch DB prices — không tin giá từ payload (security)
        from backend.database.models.commerce import ProductBase, ProductVariant
        pricing_items: list[PricingInputItem] = []
        for it in data.items:
            if it.variant_id:
                row = await db_session.execute(
                    select(ProductVariant.price).where(ProductVariant.id == it.variant_id)
                )
                db_price: float | None = row.scalar_one_or_none()
            else:
                row = await db_session.execute(
                    select(ProductBase.price).where(ProductBase.id == it.product_id)
                )
                db_price = row.scalar_one_or_none()

            unit_price: float = float(db_price) if db_price is not None else it.price
            pricing_items.append(PricingInputItem(
                product_id=it.product_id,
                quantity=it.quantity,
                unit_price=unit_price,
            ))

        # 2. Fetch vouchers
        vouchers: list[Voucher] = []
        if data.voucher_ids:
            v_rows = await db_session.execute(
                select(Voucher).where(
                    and_(Voucher.id.in_(data.voucher_ids), Voucher.is_active == True)
                )
            )
            vouchers = list(v_rows.scalars().all())

        # 3. Calculate — reuse PricingEngine, không duplicate logic
        breakdown = PricingEngine.calculate(
            items=pricing_items,
            vouchers=vouchers,
            points_to_redeem=data.points_to_redeem,
            available_points=data.available_points,
            base_shipping_fee=ShippingConfig.STANDARD_FEE,
        )
        return breakdown
