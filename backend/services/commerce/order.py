import logging
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, TypedDict, Union

import sqlalchemy as sa
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException, ValidationException

from backend.database.models import Order, User
from backend.database import current_tenant_id
from backend.database.models.promotion import Voucher
from backend.services.commerce.logic.identity_shield import _mask_name, _mask_address
from backend.services.event_bus import event_bus
from backend.utils.sql import escape_like
from backend.utils.uid import new_id
from backend.schemas.order import OrderResponse, OrderListResponse, OrderCreateRequest, OrderStatusUpdate, CancelOrderRequest, OrderPlanningRequest
from backend.schemas.common import SuccessResponse
from backend.services.commerce.loyalty import LoyaltyService
from backend.constants.commerce import LoyaltyConfig

# Phase 85: Strict JSON Typography
JSONType = Union[str, int, float, bool, None, List["JSONType"], Dict[str, "JSONType"]]

class OrderMetadata(TypedDict, total=False):
    user_agent: str
    client_notes: Optional[str]

class OrderHistoryItem(TypedDict):
    status: str
    timestamp: str
    actor: str
    note: str

class PreviousOrder(TypedDict):
    id: str
    created_at: str
    status: str
    total: float
    item_count: int

class OrderInsight(TypedDict):
    ltv: float
    total_orders: int
    trust_score: float
    first_order: Optional[str]
    last_order: Optional[str]
    previous_orders: List[PreviousOrder]


# ─────────────────────────────────────────────────────────────────────────────
# SECURITY CONSTANTS — Order Integrity Guards (Elite V2.2)
# ─────────────────────────────────────────────────────────────────────────────
_MIN_ORDER_AMOUNT_VND: float = 1_000.0          # Chặn đơn hàng 0đ / giá trị rác
_MAX_ORDER_AMOUNT_VND: float = 500_000_000.0    # Chặn đơn thổi phồng giá trị
_MAX_ITEMS_PER_ORDER: int = 50                  # Giới hạn item để tránh payload bombing
_MAX_QTY_PER_ITEM: int = 1_000                  # Giới hạn số lượng bất thường
_MIN_CROSS_TOTAL_RATIO: float = 0.30            # total_amount >= 30% sum(items) (bao gồm giảm giá tối đa)
_VELOCITY_ORDER_LIMIT: int = 5                  # Tối đa 5 đơn/giờ per phone hoặc IP
_VELOCITY_WINDOW_SECONDS: int = 3600            # 1 giờ
_VELOCITY_BLOCK_SECONDS: int = 7200             # Khoá 2h nếu vượt velocity
_DUPLICATE_WINDOW_SECONDS: int = 300            # Chặn đơn trùng trong 5 phút
# Regex chuẩn SĐT Việt Nam: 10 chữ số, đầu số 03/05/07/08/09
_VN_PHONE_RE = re.compile(r"^(0[3-9]\d{8})$")

logger = logging.getLogger("api-gateway")

# Module-level constant — tránh tạo lại dict mỗi lần gọi transition_status
_ORDER_VALID_TRANSITIONS: Dict[str, List[str]] = {
    "PENDING":   ["PACKED", "SHIPPING", "DELIVERED", "CANCELLED"],
    "PACKED":    ["PENDING", "SHIPPING", "DELIVERED", "CANCELLED"],
    "SHIPPING":  ["PENDING", "PACKED",  "DELIVERED", "CANCELLED"],
    "DELIVERED": ["PENDING", "PACKED",  "SHIPPING",  "CANCELLED"],
    "CANCELLED": ["PENDING", "PACKED",  "SHIPPING",  "DELIVERED"],
}



# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1: Item Integrity Validator
# ─────────────────────────────────────────────────────────────────────────────
def _validate_order_items(items: object) -> float:
    """Kiểm tra toàn vẹn danh sách items. Trả về tổng giá trị items để cross-check."""
    if not isinstance(items, list) or len(items) == 0:
        raise ValidationException("Đơn hàng phải có ít nhất 1 sản phẩm.")
    if len(items) > _MAX_ITEMS_PER_ORDER:
        raise ValidationException(f"Đơn hàng không được vượt quá {_MAX_ITEMS_PER_ORDER} sản phẩm.")

    computed_total: float = 0.0
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValidationException(f"Item #{idx + 1} không hợp lệ.")

        product_id = item.get("id") or item.get("product_id")
        if not product_id:
            raise ValidationException(f"Item #{idx + 1} thiếu product_id.")

        qty = item.get("qty") or item.get("quantity", 0)
        try:
            qty = int(qty)
        except (TypeError, ValueError):
            raise ValidationException(f"Item #{idx + 1} có số lượng không hợp lệ.")
        if qty <= 0:
            raise ValidationException(f"Item #{idx + 1} phải có số lượng > 0.")
        if qty > _MAX_QTY_PER_ITEM:
            raise ValidationException(f"Item #{idx + 1} vượt quá giới hạn số lượng {_MAX_QTY_PER_ITEM} sản phẩm/loại.")

        unit_price = item.get("unit_price") or item.get("price", 0)
        try:
            unit_price = float(unit_price)
        except (TypeError, ValueError):
            raise ValidationException(f"Item #{idx + 1} có giá không hợp lệ.")
        if unit_price < 0:
            raise ValidationException(f"Item #{idx + 1} có giá âm — dữ liệu bất hợp lệ.")

        computed_total += unit_price * qty

    return computed_total


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2: Phone Format Validator (Chuẩn SĐT Việt Nam)
# ─────────────────────────────────────────────────────────────────────────────
def _validate_vn_phone(phone: str) -> str:
    """Chuẩn hoá và validate định dạng số điện thoại Việt Nam."""
    if not phone:
        raise ValidationException("Số điện thoại khách hàng là bắt buộc.")
    # Normalize: remove spaces, dashes, +84 prefix
    cleaned = re.sub(r"[\s\-\.]", "", str(phone).strip())
    if cleaned.startswith("+84"):
        cleaned = "0" + cleaned[3:]
    elif cleaned.startswith("84") and len(cleaned) == 11:
        cleaned = "0" + cleaned[2:]
    if not _VN_PHONE_RE.match(cleaned):
        raise ValidationException("Số điện thoại không đúng định dạng Việt Nam (10 chữ số, đầu số 03/05/07/08/09).")
    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 & 4: Redis Velocity Check + Duplicate Guard
# ─────────────────────────────────────────────────────────────────────────────
async def _check_velocity_and_duplicate(
    phone: str,
    ip: str,
    items: list,
    total_amount: float,
) -> None:
    """Velocity limit (5 đơn/giờ/phone hoặc IP) + Duplicate order guard (5 phút)."""
    try:
        from backend.services.xohi_memory import xohi_memory
        redis = xohi_memory.client
        if not redis:
            return

        # --- Velocity: phone ---
        phone_key = f"order:velocity:phone:{phone}"
        block_key_phone = f"order:velocity:block:phone:{phone}"
        if await redis.exists(block_key_phone):
            raise ValidationException(
                "Tài khoản này đã đặt quá nhiều đơn trong thời gian ngắn. Vui lòng thử lại sau 2 giờ."
            )
        phone_count = await redis.incr(phone_key)
        if phone_count == 1:
            await redis.expire(phone_key, _VELOCITY_WINDOW_SECONDS)
        if phone_count > _VELOCITY_ORDER_LIMIT:
            await redis.set(block_key_phone, 1, ex=_VELOCITY_BLOCK_SECONDS)
            logger.warning(f"[ORDER-VELOCITY] Phone {phone} blocked for {_VELOCITY_BLOCK_SECONDS}s (count={phone_count})")
            raise ValidationException(
                "Hệ thống phát hiện quá nhiều đơn từ số điện thoại này. Tài khoản tạm thời bị hạn chế 2 giờ."
            )

        # --- Velocity: IP ---
        if ip and ip not in ["0.0.0.0", "127.0.0.1"]:
            safe_ip = ip.replace(":", "_")
            ip_key = f"order:velocity:ip:{safe_ip}"
            block_key_ip = f"order:velocity:block:ip:{safe_ip}"
            if await redis.exists(block_key_ip):
                raise ValidationException(
                    "IP này đã đặt quá nhiều đơn trong thời gian ngắn. Vui lòng thử lại sau 2 giờ."
                )
            ip_count = await redis.incr(ip_key)
            if ip_count == 1:
                await redis.expire(ip_key, _VELOCITY_WINDOW_SECONDS)
            if ip_count > _VELOCITY_ORDER_LIMIT:
                await redis.set(block_key_ip, 1, ex=_VELOCITY_BLOCK_SECONDS)
                logger.warning(f"[ORDER-VELOCITY] IP {ip} blocked for {_VELOCITY_BLOCK_SECONDS}s (count={ip_count})")
                raise ValidationException(
                    "Hệ thống phát hiện hành vi đặt hàng bất thường. Địa chỉ IP tạm thời bị hạn chế 2 giờ."
                )

        # --- Duplicate Order Guard ---
        try:
            items_normalized = sorted(
                [{"id": (it.get("id") or it.get("product_id") or ""), "qty": (it.get("qty") or it.get("quantity") or 0)} for it in items],
                key=lambda x: x["id"]
            )
            dedup_hash = hashlib.sha256(
                f"{phone}:{json.dumps(items_normalized, sort_keys=True)}:{int(total_amount)}".encode()
            ).hexdigest()[:32]
            dedup_key = f"order:dedup:{dedup_hash}"
            if await redis.exists(dedup_key):
                raise ValidationException(
                    "Đơn hàng trùng lặp! Bạn vừa đặt một đơn giống hệt trong vòng 5 phút. Vui lòng kiểm tra lại."
                )
            await redis.set(dedup_key, 1, ex=_DUPLICATE_WINDOW_SECONDS)
        except ValidationException:
            raise
        except Exception as e:
            logger.warning(f"[ORDER-DEDUP] Dedup hash check failed (skipping): {e}")

    except ValidationException:
        raise
    except Exception as e:
        logger.warning(f"[ORDER-SECURITY] Velocity check unavailable (Redis down?): {e}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5: G-7 — Voucher Fraud Guard
# Validate voucher_ids từ DB: tồn tại, còn hạn, còn lượt dùng, đủ min_spend
# ─────────────────────────────────────────────────────────────────────────────
async def _validate_vouchers(
    db_session: AsyncSession,
    voucher_ids: List[str],
    subtotal: float,
) -> None:
    """Chặn áp mã giảm giá ảo, hết hạn, hết lượt, không đủ điều kiện chi tiêu."""
    if not voucher_ids:
        return

    # ── Business Rule: tối đa 2 mã/đơn (1 DISCOUNT + 1 SHIPPING) ──
    if len(voucher_ids) > 2:
        raise ValidationException("Mỗi đơn hàng chỉ được áp dụng tối đa 2 mã: 1 mã giảm giá và 1 mã miễn phí vận chuyển.")

    now = datetime.now(timezone.utc)
    seen_categories: Dict[str, str] = {}

    # Batch load toàn bộ vouchers trong 1 query — tránh N+1
    v_stmt = select(Voucher).where(
        and_(Voucher.id.in_(voucher_ids), Voucher.deleted_at == None)
    )
    v_res = await db_session.execute(v_stmt)
    vouchers_map: Dict[str, Voucher] = {v.id: v for v in v_res.scalars().all()}

    for vid in voucher_ids:
        voucher: Optional[Voucher] = vouchers_map.get(vid)

        if not voucher:
            logger.warning(f"[ORDER-VOUCHER] Ghost voucher attempt: id={vid}")
            raise ValidationException(f"Mã giảm giá '{vid[:8]}...' không tồn tại hoặc đã bị xoá.")

        if not voucher.is_active:
            raise ValidationException(f"Mã giảm giá '{vid[:8]}...' đã bị vô hiệu hoá.")

        # ── Kiểm tra trùng loại mã ──
        # Nhóm DISCOUNT = DISCOUNT, FIXED, PERCENT (chỉ 1 mã/nhóm)
        # Nhóm SHIPPING = SHIPPING (chỉ 1 mã/nhóm)
        norm_cat = "SHIPPING" if voucher.category == "SHIPPING" else "DISCOUNT"
        if norm_cat in seen_categories:
            conflict_label = "miễn phí vận chuyển" if norm_cat == "SHIPPING" else "giảm giá"
            raise ValidationException(
                f"Chỉ được dùng 1 mã {conflict_label} cho mỗi đơn hàng. Vui lòng bỏ bớt 1 mã."
            )
        seen_categories[norm_cat] = vid

        # ── Kiểm tra thời hạn ──
        if voucher.start_date and voucher.start_date > now:
            raise ValidationException("Mã giảm giá chưa đến ngày có hiệu lực.")
        if voucher.end_date and voucher.end_date < now:
            raise ValidationException("Mã giảm giá đã hết hạn sử dụng.")

        # ── Kiểm tra giới hạn lượt dùng ──
        if voucher.usage_limit is not None and voucher.used_count >= voucher.usage_limit:
            logger.warning(f"[ORDER-VOUCHER] Usage limit exceeded: id={vid}, used={voucher.used_count}, limit={voucher.usage_limit}")
            raise ValidationException(f"Mã giảm giá đã đạt giới hạn lượt sử dụng ({voucher.usage_limit} lượt).")

        # ── Kiểm tra điều kiện chi tiêu tối thiểu ──
        if voucher.min_spend and subtotal < float(voucher.min_spend):
            raise ValidationException(
                f"Đơn hàng cần tối thiểu {float(voucher.min_spend):,.0f}đ để áp dụng mã giảm giá này "
                f"(hiện tại: {subtotal:,.0f}đ)."
            )

        logger.info(f"[ORDER-VOUCHER] Voucher validated OK: id={vid}, category={norm_cat}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 6: G-8 — Stock Overflow Guard
# Validate số lượng tồn kho trước khi tạo đơn (chặn vượt kho)
# ─────────────────────────────────────────────────────────────────────────────
async def _validate_stock(
    db_session: AsyncSession,
    items: List[dict],
) -> None:
    """Kiểm tra tồn kho thực tế từ DB. Chặn đặt hàng vượt số lượng tồn kho."""
    if not items:
        return

    from backend.database.models.commerce import ProductBase, ProductVariant

    # Batch load tất cả products và variants — O(1) query thay vì N+1
    product_ids = list({str(it.get("id") or it.get("product_id") or "") for it in items if (it.get("id") or it.get("product_id"))})
    variant_ids = list({str(it.get("variant_id") or "") for it in items if it.get("variant_id")})

    products_map: Dict[str, ProductBase] = {}
    if product_ids:
        p_stmt = select(ProductBase).where(ProductBase.id.in_(product_ids))
        p_res = await db_session.execute(p_stmt)
        products_map = {p.id: p for p in p_res.scalars().all()}

    variants_map: Dict[str, ProductVariant] = {}
    if variant_ids:
        v_stmt = select(ProductVariant).where(ProductVariant.id.in_(variant_ids))
        v_res = await db_session.execute(v_stmt)
        variants_map = {v.id: v for v in v_res.scalars().all()}

    for item in items:
        pid = str(item.get("id") or item.get("product_id") or "")
        vid = str(item.get("variant_id") or "")
        qty = int(item.get("qty") or item.get("quantity") or 0)
        name = item.get("name") or pid[:12]

        product = products_map.get(pid)
        if not product:
            # Product không tồn tại → đã bị validate ở G-3, chỉ log thêm
            logger.warning(f"[ORDER-STOCK] Product not found in stock check: id={pid}")
            continue

        # Nếu có variant, ưu tiên kiểm tra stock của variant
        if vid:
            variant = variants_map.get(vid)
            if variant:
                available_stock = int(variant.stock or 0)
                if available_stock <= 0:
                    raise ValidationException(
                        f"Sản phẩm '{name}' (phân loại đã chọn) đã hết hàng. Vui lòng chọn phân loại khác."
                    )
                if qty > available_stock:
                    raise ValidationException(
                        f"Sản phẩm '{name}' chỉ còn {available_stock} sản phẩm trong kho, "
                        f"không đủ cho số lượng yêu cầu ({qty} sản phẩm)."
                    )
                logger.debug(f"[ORDER-STOCK] Variant stock OK: vid={vid}, qty={qty}, stock={available_stock}")
                continue

        # Kiểm tra stock ở cấp ProductBase nếu không có variant
        available_stock = int(product.stock or 0)
        if available_stock <= 0:
            raise ValidationException(
                f"Sản phẩm '{name}' đã hết hàng. Vui lòng liên hệ hỗ trợ để cập nhật."
            )
        if qty > available_stock:
            raise ValidationException(
                f"Sản phẩm '{name}' chỉ còn {available_stock} sản phẩm trong kho, "
                f"không đủ cho số lượng yêu cầu ({qty} sản phẩm)."
            )
        logger.debug(f"[ORDER-STOCK] Product stock OK: pid={pid}, qty={qty}, stock={available_stock}")


class OrderService:
    @staticmethod
    async def create_order(db_session: AsyncSession, data: OrderCreateRequest, ip: str, ua: str, user_id: str) -> SuccessResponse:
        """Moves logic from OrderController.create_order. Emits ORDER_CREATED event via event_bus."""

        # ═══════════════════════════════════════════════════════════════════════
        # SECURITY GATE — Military-Grade Order Integrity (Elite V2.2)
        # CRITICAL: All guards must pass BEFORE any DB write / loyalty operation.
        # ═══════════════════════════════════════════════════════════════════════

        # [G-1] Zero-Order Guard — chặn đơn hàng 0đ / âm tiền / thổi phồng giá trị
        raw_total = float(data.total_amount)
        if raw_total < _MIN_ORDER_AMOUNT_VND:
            logger.error(f"[ORDER-SECURITY] Zero/Negative order blocked: total={raw_total}, phone={data.customer_phone}, ip={ip}")
            raise ValidationException(f"Giá trị đơn hàng phải tối thiểu {_MIN_ORDER_AMOUNT_VND:,.0f}đ.")
        if raw_total > _MAX_ORDER_AMOUNT_VND:
            logger.error(f"[ORDER-SECURITY] Inflated order blocked: total={raw_total}, phone={data.customer_phone}, ip={ip}")
            raise ValidationException("Giá trị đơn hàng vượt quá giới hạn cho phép. Vui lòng liên hệ hỗ trợ.")

        # [G-2] Phone Format Validator
        validated_phone = _validate_vn_phone(data.customer_phone)
        if validated_phone != data.customer_phone:
            data.customer_phone = validated_phone

        # [G-3] Item Integrity Validator — đơn ảo, item rỗng, qty/price âm
        computed_items_total: float = _validate_order_items(
            data.items if isinstance(data.items, list) else []
        )

        # [G-4] Cross-Total Validation — total_amount phải >= 30% tổng items (phòng exploit giảm giá)
        # Lưu ý: 30% để cho phép tối đa ~70% giảm giá hợp lệ (điểm + voucher + combo)
        if computed_items_total > 0 and raw_total < computed_items_total * _MIN_CROSS_TOTAL_RATIO:
            logger.error(
                f"[ORDER-SECURITY] Cross-total fraud blocked: "
                f"declared={raw_total:,.0f}, items_sum={computed_items_total:,.0f}, "
                f"phone={data.customer_phone}, ip={ip}"
            )
            raise ValidationException("Tổng giá trị đơn hàng không hợp lệ so với danh sách sản phẩm. Vui lòng tải lại trang và thử lại.")

        # [G-5 + G-6] Velocity Check (5 đơn/giờ/phone&IP) + Duplicate Guard (5 phút)
        await _check_velocity_and_duplicate(
            phone=validated_phone,
            ip=ip,
            items=data.items if isinstance(data.items, list) else [],
            total_amount=raw_total,
        )

        # [G-7] Voucher Fraud Guard — chặn mã giảm giá ảo/hết hạn/vượt lượt/không đủ min_spend
        voucher_ids: List[str] = [str(v) for v in (getattr(data, "voucher_ids", None) or []) if v]
        if voucher_ids:
            await _validate_vouchers(
                db_session=db_session,
                voucher_ids=voucher_ids,
                subtotal=computed_items_total,
            )

        # [G-8] Stock Overflow Guard — chặn đặt hàng vượt tồn kho thực tế
        await _validate_stock(
            db_session=db_session,
            items=data.items if isinstance(data.items, list) else [],
        )
        # ═══════════════════════════════════════════════════════════════════════

        new_id_val = new_id()
        history: List[OrderHistoryItem] = [{
            "status": "PENDING",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "Storefront",
            "note": "Order created via checkout"
        }]

        # --- Elite V3.0 Loyalty Redemption (Military Grade) ---
        points_redeemed = 0
        point_discount = 0.0
        
        if data.points_to_redeem:
            if not user_id:
                 raise ValidationException("Bạn phải đăng nhập để sử dụng Điểm thưởng.")
            
            # Lock the loyalty row to prevent race conditions (Elite Protocol)
            from backend.database.models.commerce import UserLoyalty, PointTransaction
            
            # ELITE V2.2: Military-Grade Integrity Verification
            if not await LoyaltyService.verify_loyalty_integrity(db_session, user_id):
                logger.critical(f"[SECURITY-ALERT] Loyalty Point Tampering Detected! User: {user_id}. Order aborted.")
                raise ValidationException("Hệ thống phát hiện bất thường về bảo mật tài khoản. Vui lòng liên hệ hỗ trợ.")
            
            loyalty_stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id).with_for_update()
            loyalty = (await db_session.execute(loyalty_stmt)).scalar_one_or_none()
            
            if not loyalty:
                raise ValidationException("Danh mục điểm thưởng không tồn tại.")
                
            pts_to_use = data.points_to_redeem
            if pts_to_use == -1: # "Dùng hết điểm" Protocol
                pts_to_use = loyalty.available_points
                
            if pts_to_use > 0:
                if loyalty.available_points < pts_to_use:
                    raise ValidationException(f"Sếp chỉ còn {loyalty.available_points} điểm, không đủ để trừ {pts_to_use} điểm ạ.")
                
                # Fetch Point Value from Centralized Config [ELITE V2.2]
                point_value = LoyaltyConfig.POINT_VALUE
                
                # Sếp Rule [ELITE V2.2]: Cap at defined percentage of total
                max_point_discount = data.total_amount * LoyaltyConfig.MAX_DISCOUNT_PERCENT 
                proposed_discount = float(pts_to_use * point_value)
                
                if proposed_discount > max_point_discount:
                    # Adjust points to match the cap
                    point_discount = max_point_discount
                    points_redeemed = int(math.ceil(point_discount / point_value))
                    # Re-verify we don't exceed available
                    points_redeemed = min(points_redeemed, loyalty.available_points)
                    point_discount = float(points_redeemed * point_value)
                else:
                    point_discount = proposed_discount
                    points_redeemed = pts_to_use

                if points_redeemed > 0:
                    loyalty.available_points -= points_redeemed
                    loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)
                    
                    # Log Transaction
                    pt = PointTransaction(
                        user_id=user_id,
                        order_id=new_id_val,
                        amount=-points_redeemed,
                        transaction_type="REDEEM_ORDER",
                        notes=f"Thanh toán đơn hàng {new_id_val} bằng điểm. (Giảm giá: {point_discount:,.0f}đ)"
                    )
                    pt.integrity_token = LoyaltyService._create_transaction_token(pt)
                    db_session.add(pt)
                    logger.info(f"[LOYALTY] User {user_id} redeemed {points_redeemed} pts for order {new_id_val}")

        tenant_id: str = current_tenant_id.get() or "default"
        final_total: float = data.total_amount - point_discount

        order = Order(
            id=new_id_val,
            user_id=user_id,
            items=data.items,
            total_amount=final_total,
            status="PENDING",
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_address=data.customer_address,
            customer_ip=ip,
            tenant_id=tenant_id,
            order_metadata=OrderMetadata(user_agent=ua),
            history=history,
            points_redeemed=points_redeemed,
            point_discount_amount=point_discount
        )

        db_session.add(order)
        await db_session.flush()

        await event_bus.emit("ORDER_CREATED", {
            "id": new_id_val,
            "user_id": user_id,
            "ip": ip,
            "user_agent": ua,
            "customer": data.customer_name,
            "phone": data.customer_phone,
            "address": data.customer_address,
            "total_amount": final_total,
            "tenant_id": tenant_id,
            "items": data.items if isinstance(data.items, list) else [],
        })

        return SuccessResponse(ok=True, id=new_id_val)

    @staticmethod
    async def list_orders(
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> OrderListResponse:
        """Moves logic from OrderController.list_orders. Uses Scalar Projection."""
        conditions = [
            Order.deleted_at == None,
            Order.tenant_id == (current_tenant_id.get() or "default")
        ]

        if status and status != "all":
            conditions.append(Order.status == status.upper())

        if search:
            safe = escape_like(search)
            conditions.append(or_(
                Order.id.ilike(f"%{safe}%"),
                Order.user.has(func.unaccent(User.name).ilike(f"%{func.unaccent(safe)}%"))
            ))

        # 1. Total Count (Zero-Hydration)
        count_stmt = select(func.count(Order.id)).where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0

        # 2. R76: Scalar Projection Fetch with Aggregate History
        # Identity match: customer_phone (if exists) OR user_id
        
        # Subqueries for stats (Performance Optimized Viral 2026)
        success_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"), # Reference outer column
                Order.status == "DELIVERED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("successful_count")
        
        cancel_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"),
                Order.status == "CANCELLED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("cancelled_count")

        stmt = select(
            Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
            Order.is_spam, Order.spam_score, Order.spam_reason,
            Order.customer_name, Order.customer_phone, Order.customer_address, Order.customer_ip,
            Order.order_metadata,
            Order.points_earned, Order.points_redeemed, Order.point_discount_amount,
            User.name.label("user_name"),
            success_sq, cancel_sq
        ).outerjoin(User, Order.user_id == User.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(Order.created_at.desc())

        result = await db_session.execute(stmt)
        data = [OrderResponse.model_validate(row) for row in result]

        return OrderListResponse(data=data, total=total)

    @staticmethod
    async def get_order(db_session: AsyncSession, order_id: str, ox_cookie: Optional[str] = None) -> OrderResponse:
        """Moves logic from OrderController.get_order. Identity Shield V3.0."""
        success_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"),
                Order.status == "DELIVERED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("successful_count")
        
        cancel_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"),
                Order.status == "CANCELLED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("cancelled_count")

        stmt = (
            select(
                Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
                Order.is_spam, Order.spam_score, Order.spam_reason,
                Order.customer_name, Order.customer_phone, Order.customer_address, Order.customer_ip,
                Order.history, Order.cancellation_reason, Order.order_metadata,
                Order.points_earned, Order.points_redeemed, Order.point_discount_amount,
                User.name.label("user_name"),
                success_sq, cancel_sq
            )
            .outerjoin(User, Order.user_id == User.id)
            .where(
                and_(
                    Order.tenant_id == (current_tenant_id.get() or "default"),
                    Order.deleted_at == None
                )
            )
        )

        # R2026: Elite Suffix Lookup Support (Support 6-12 chars)
        if len(order_id) < 36:
             stmt = stmt.where(Order.id.ilike(f"%{order_id}"))
        else:
             stmt = stmt.where(Order.id == order_id)
        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Order {order_id} not found")

        # Customer 360 Insights (Viral 2026 Deep Intelligence)
        phone = row.customer_phone
        insight: Optional[OrderInsight] = None
        if phone:
            insight_stmt = select(
                sa.func.sum(Order.total_amount).filter(Order.status == "DELIVERED").label("ltv"),
                sa.func.count(Order.id).label("total_orders"),
                # Success rate calculation (R2026: Safe Division)
                sa.func.coalesce(
                    sa.func.count(Order.id).filter(Order.status == "DELIVERED") * 100.0 / 
                    sa.func.nullif(sa.func.count(Order.id), 0),
                    0.0
                ).label("trust_score"),
                sa.func.min(Order.created_at).label("first_order"),
                sa.func.max(Order.created_at).label("last_order")
            ).where(
                and_(
                    Order.customer_phone == phone,
                    Order.tenant_id == (current_tenant_id.get() or "default")
                )
            )
            stats = (await db_session.execute(insight_stmt)).fetchone()
            
            # Fetch previous 10 orders (excluding self)
            history_stmt = select(
                Order.id, Order.created_at, Order.status, Order.total_amount, Order.items
            ).where(
                and_(
                    Order.customer_phone == phone,
                    Order.id != order_id,
                    Order.tenant_id == (current_tenant_id.get() or "default")
                )
            ).order_by(Order.created_at.desc()).limit(10)
            
            history_result = await db_session.execute(history_stmt)
            previous_orders: List[PreviousOrder] = []
            for h in history_result:
                previous_orders.append({
                    "id": h.id,
                    "created_at": h.created_at.isoformat(),
                    "status": h.status,
                    "total": float(h.total_amount),
                    "item_count": sum(it.get("quantity", 1) for it in h.items) if isinstance(h.items, list) else 0
                })

            if stats:
                insight = OrderInsight(
                    ltv=float(stats.ltv) if stats.ltv else 0.0,
                    total_orders=int(stats.total_orders) if stats.total_orders else 0,
                    trust_score=float(stats.trust_score) if stats.trust_score else 0.0,
                    first_order=stats.first_order.isoformat() if stats.first_order else None,
                    last_order=stats.last_order.isoformat() if stats.last_order else None,
                    previous_orders=previous_orders
                )

        res_dict: Dict[str, object] = dict(row._asdict())
        res_dict["insight"] = insight

        # Elite V4.0: Cookie Session Gate (Fingerprint Binding)
        stored_ox = (res_dict.get("order_metadata") or {}).get("ox_fingerprint")
        is_trusted: bool = bool(ox_cookie and ox_cookie == stored_ox)

        res_dict["is_trusted_device"] = is_trusted
        
        res_dict["name_masked"] = _mask_name(row.customer_name or "")
        res_dict["address_masked"] = _mask_address(row.customer_address or "")

        return OrderResponse.model_validate(res_dict)

    @staticmethod
    async def transition_status(
        db_session: AsyncSession,
        order_id: str,
        new_status: str,
        actor_email: str
    ) -> SuccessResponse:
        """Moves logic from OrderController.update_order_status. Implements State Machine R60 and emits ORDER_UPDATED."""
        # We need the full object to update it and its history
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        current_status = order.status.upper()
        new_status = new_status.upper()

        VALID_TRANSITIONS = _ORDER_VALID_TRANSITIONS

        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            raise ValidationException(f"Invalid transition from {current_status} to {new_status}")

        order.status = new_status

        history = list(order.history or [])
        history.append({
            "status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": "Status updated via admin"
        })
        order.history = history

        await event_bus.emit("ORDER_UPDATED", {
            "id": order_id,
            "status": new_status,
            "tenant_id": order.tenant_id
        })
        
        # Elite V2.2: Loyalty Point Accrual + CTV Commission Confirmation
        if new_status == "DELIVERED":
            try:
                await LoyaltyService.earn_order_points(db_session, order_id)
                logger.info(f"[LOYALTY] Points processed for order {order_id}")
            except Exception as e:
                logger.error(f"[LOYALTY-ERROR] Failed to process points for order {order_id}: {e}")

            # CTV Attribution: Confirm pending commission (PENDING → CONFIRMED)
            if order.ctv_code:
                try:
                    from backend.services.ctv_service import CtvService as _CtvService
                    confirmed = await _CtvService.confirm_pending_commissions(db_session, order_id)
                    if confirmed:
                        logger.info(f"[CTV] Commission CONFIRMED for order {order_id} (code={order.ctv_code})")
                    else:
                        logger.warning(f"[CTV] No pending commission to confirm for order {order_id}")
                except Exception as e:
                    logger.error(f"[CTV-ERROR] Failed to confirm commission for order {order_id}: {e}")

        # CTV Attribution: Void pending commission when order is CANCELLED
        if new_status == "CANCELLED" and order.ctv_code:
            try:
                from backend.services.ctv_service import CtvService as _CtvService
                voided = await _CtvService.void_commission(db_session, order_id)
                if voided:
                    logger.info(f"[CTV] Commission VOIDED for cancelled order {order_id} (code={order.ctv_code})")
            except Exception as e:
                logger.error(f"[CTV-ERROR] Failed to void commission for order {order_id}: {e}")

        return SuccessResponse(ok=True, id=order_id, message=f"Status updated to {new_status}")

    @staticmethod
    async def cancel_order(
        db_session: AsyncSession,
        order_id: str,
        reason: str,
        actor_email: str
    ) -> SuccessResponse:
        """Moves logic from OrderController.cancel_order. Emits ORDER_CANCELLED."""
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        current_status = order.status.upper()

        if current_status not in ["PENDING", "PACKED"]:
            raise ValidationException("Only PENDING or PACKED orders can be cancelled")

        order.status = "CANCELLED"
        order.cancellation_reason = reason

        history = list(order.history or [])
        history.append({
            "status": "CANCELLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": f"Reason: {reason}"
        })
        order.history = history

        # CTV Attribution: Void pending commission on cancellation
        if order.ctv_code:
            try:
                from backend.services.ctv_service import CtvService as _CtvService
                voided = await _CtvService.void_commission(db_session, order_id)
                if voided:
                    logger.info(f"[CTV] Commission VOIDED for cancelled order {order_id} (code={order.ctv_code})")
            except Exception as e:
                logger.error(f"[CTV-ERROR] Failed to void commission for order {order_id}: {e}")

        await event_bus.emit("ORDER_CANCELLED", {
            "id": order_id,
            "reason": reason,
            "tenant_id": order.tenant_id
        })

        return SuccessResponse(ok=True, id=order_id, message="Order cancelled")

    @staticmethod
    async def toggle_spam(
        db_session: AsyncSession,
        order_id: str,
        actor_email: str
    ) -> SuccessResponse:
        """Moves logic from OrderController.toggle_order_spam."""
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        new_spam_state = not order.is_spam
        order.is_spam = new_spam_state

        if not new_spam_state:
            order.spam_score = 0.0
            order.spam_reason = "Manual Whitelist (Admin)"
        else:
            order.spam_score = 100.0
            order.spam_reason = "Manual Blacklist (Admin)"

        history = list(order.history or [])
        history.append({
            "status": order.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": f"Manual Spam Override: {'SPAM_MARKED' if new_spam_state else 'SPAM_REMOVED'}"
        })
        order.history = history

        return SuccessResponse(
            ok=True,
            id=order_id,
            data={
                "isSpam": new_spam_state,
                "spamScore": order.spam_score,
                "spamReason": order.spam_reason
            }
        )

    @staticmethod
    async def update_planning(
        db_session: AsyncSession,
        order_id: str,
        data: OrderPlanningRequest,
        actor_email: str
    ) -> SuccessResponse:
        """Elite V2.2: Professional Logistics Planning Logic"""
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        # Update order_metadata with planning fields
        meta = dict(order.order_metadata or {})
        meta.update({
            "assigned_to": data.assigned_to,
            "scheduled_at": data.scheduled_at.isoformat() if data.scheduled_at else None,
            "priority": data.priority,
            "planning_notes": data.planning_notes
        })
        order.order_metadata = meta

        # Add trace log to history
        history = list(order.history or [])
        history.append({
            "status": order.status, # Keep current status
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": f"Planning Updated: Assigned={data.assigned_to}, Priority={data.priority}"
        })
        order.history = history

        await event_bus.emit("ORDER_PLANNING_UPDATED", {
            "id": order_id,
            "assigned_to": data.assigned_to,
            "priority": data.priority,
            "tenant_id": order.user_id
        })

        return SuccessResponse(ok=True, id=order_id, message="Planning details updated")

order_service = OrderService()
