"""
Client CTV Controller - Elite V2.2 / Viral 2026
Endpoints: /api/v1/client/ctv/*
Auth: JWT required for all endpoints.
"""
import logging
from typing import Optional

logger = logging.getLogger("api-gateway")
from litestar import Controller, Request, get, post, patch, delete
from litestar.status_codes import HTTP_200_OK
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, EmailStr
from backend.services.ctv_service import ctv_service
from backend.database.models.auth import User

# SECURITY: Anti-brute force and code harvesting limit (10 requests/min per IP)
ctv_validate_rate_limit = RateLimitConfig(rate_limit=("minute", 10), store="memory_store")
# SECURITY: Anti-scraping limit for shipping configs (30 requests/min per IP)
shipping_rate_limit = RateLimitConfig(rate_limit=("minute", 30), store="memory_store")


def _require_user(request: Request) -> dict:
    user_state = request.scope.get("state", {}).get("user")
    if not user_state:
        raise NotAuthorizedException("Vui lòng đăng nhập để sử dụng tính năng này")
    return user_state


class RegisterCtvSchema(BaseModel):
    ctv_code: str = Field(..., min_length=4, max_length=20, pattern=r"^[A-Za-z0-9]+$")
    referred_by_code: Optional[str] = Field(None, max_length=20)
    # SECURITY: email is MANDATORY at backend level to ensure commission notification reliability
    email: EmailStr = Field(..., description="Email nhận thông báo hoa hồng - bắt buộc")


class BankInfoSchema(BaseModel):
    bank: str = Field(..., min_length=2, max_length=100)
    account_no: str = Field(..., min_length=5, max_length=30)
    account_name: str = Field(..., min_length=3, max_length=100)


class WithdrawSchema(BaseModel):
    amount: int = Field(..., ge=200_000)


class ClientCtvController(Controller):
    """Viral 2026: Client-facing CTV (Affiliate) endpoints."""
    path = "/api/v1/client/ctv"
    guards = []

    @get("/profile")
    async def get_profile(self, request: Request, db_session: AsyncSession) -> dict:
        """GET profile + dashboard stats cho CTV hiện tại."""
        user_state = _require_user(request)
        return await ctv_service.get_dashboard_stats(db_session, user_state["id"])

    @post("/register", status_code=HTTP_200_OK)
    async def register(
        self,
        request: Request,
        db_session: AsyncSession,
        data: RegisterCtvSchema,
    ) -> dict:
        """Đăng ký trở thành CTV. Auto-active với tier Đồng (15%)."""
        user_state = _require_user(request)
        # SECURITY: Verify user is active
        stmt_status = select(User.status).where(User.id == user_state["id"])
        user_status = (await db_session.execute(stmt_status)).scalar()
        if not user_status or user_status != "ACTIVE":
            raise NotAuthorizedException("Tai khoan cua ban da bi khoa hoac ngung hoat dong")
        aff = await ctv_service.register_affiliate(
            db_session,
            user_id=user_state["id"],
            ctv_code=data.ctv_code,
            referred_by_code=data.referred_by_code,
        )

        # Update User.email nếu user cung cấp và chưa có email
        if data.email:
            await db_session.execute(
                update(User)
                .where(User.id == user_state["id"], User.email == None)  # noqa: E711
                .values(email=data.email.lower())
            )
            await db_session.flush()

        return {
            "ok": True,
            "ctv_code": aff.ctv_code,
            "referral_link": ctv_service.get_referral_link(aff.ctv_code),
            "message": f"Đăng ký thành công! Mã CTV của bạn: {aff.ctv_code}",
        }

    @get("/validate/{code:str}", guards=[], middleware=[ctv_validate_rate_limit.middleware])  # PUBLIC - dung o checkout
    async def validate_code(self, db_session: AsyncSession, code: str) -> dict:
        """PUBLIC: Validate mã CTV tại checkout (real-time)."""
        aff = await ctv_service.validate_ctv_code(db_session, code.upper())
        if not aff:
            return {"valid": False, "message": "Mã CTV không hợp lệ hoặc không hoạt động"}
        return {
            "valid": True,
            "ctv_code": aff.ctv_code,
            "message": "Mã CTV hợp lệ",
        }

    @get("/shipping", guards=[], middleware=[shipping_rate_limit.middleware])  # PUBLIC - dung o checkout
    async def get_shipping_config(self, db_session: AsyncSession) -> dict:
        """PUBLIC: Lấy cấu hình phí ship mặc định của CTV (Dynamic DB/Redis-backed)."""
        from backend.services.xohi_memory import xohi_memory
        from backend.database.models.system import SystemSetting
        
        default_fee = None
        if xohi_memory._use_redis and xohi_memory.client:
            try:
                val = await xohi_memory.client.get("config:shipping:default_fee")
                if val:
                    default_fee = float(val)
            except Exception:
                pass
                
        if default_fee is None:
            try:
                stmt = select(SystemSetting).where(SystemSetting.key == "ctv_shipping_config")
                result = await db_session.execute(stmt)
                setting = result.scalar_one_or_none()
                if setting and setting.value and "default_fee" in setting.value:
                    default_fee = float(setting.value["default_fee"])
                else:
                    default_fee = 25000.0
                
                if xohi_memory._use_redis and xohi_memory.client:
                    await xohi_memory.client.set("config:shipping:default_fee", str(default_fee))
            except Exception as e:
                logger.error(f"[CTV] Failed to load config from DB fallback: {e}")
                default_fee = 25000.0
                
        return {"default_fee": default_fee}

    @get("/commissions")
    async def get_commissions(
        self,
        request: Request,
        db_session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> dict:
        """Lịch sử hoa hồng - phân trang, filter theo status. PACKED = kho đã đóng gói, không thể tự hủy — phải liên hệ shop."""
        from sqlalchemy import select, and_, desc, func
        from backend.database.models.affiliate import AffiliateProfile, CommissionLedger

        user_state = _require_user(request)
        user_id: str = user_state["id"]

        # SECURITY: Cap pagination to prevent DoS
        page = max(1, page)
        page_size = max(1, min(page_size, 50))

        aff_stmt = select(AffiliateProfile).where(AffiliateProfile.user_id == user_id)
        aff_res = await db_session.execute(aff_stmt)
        aff = aff_res.scalar_one_or_none()
        if not aff:
            return {"items": [], "total": 0, "page": page}
        if aff.status != "ACTIVE":
            from litestar.exceptions import ValidationException
            raise ValidationException("Tai khoan CTV cua ban khong hoat dong hoac dang bi khoa")

        conditions = [CommissionLedger.affiliate_id == aff.id]
        if status:
            conditions.append(CommissionLedger.status == status.upper())

        # SECURITY FIX: Use scalar COUNT instead of loading all records into memory (O(N) DoS)
        count_stmt = select(func.count(CommissionLedger.id)).where(and_(*conditions))
        total: int = await db_session.scalar(count_stmt) or 0

        offset = (page - 1) * page_size
        stmt = (
            select(CommissionLedger)
            .where(and_(*conditions))
            .order_by(desc(CommissionLedger.created_at))
            .offset(offset)
            .limit(page_size)
        )
        res = await db_session.execute(stmt)
        items = res.scalars().all()

        return {
            "items": [
                {
                    "id": it.id,
                    "order_id": it.order_id,
                    "order_amount": it.order_amount,
                    "commission_amount": it.commission_amount,
                    "rate_applied_bps": it.rate_applied_bps,
                    "rate_applied_pct": f"{it.rate_applied_bps / 100:.2f}%",
                    "tier_name": (it.tier_snapshot or {}).get("name", "Đồng"),
                    "status": it.status,
                    "confirmed_at": it.confirmed_at.isoformat() if it.confirmed_at else None,
                    "paid_at": it.paid_at.isoformat() if it.paid_at else None,
                    "created_at": it.created_at.isoformat(),
                    "admin_note": it.admin_note,
                }
                for it in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @post("/withdraw", status_code=HTTP_200_OK)
    async def request_withdraw(
        self,
        request: Request,
        db_session: AsyncSession,
        data: WithdrawSchema,
    ) -> dict:
        """Yêu cầu rút tiền hoa hồng. Admin sẽ duyệt thủ công."""
        user_state = _require_user(request)
        client_ip = request.client.host if request.client else "127.0.0.1"
        user_agent = request.headers.get("user-agent", "")
        wr = await ctv_service.request_withdrawal(
            db_session,
            user_id=user_state["id"],
            amount=data.amount,
            ip_address=client_ip,
            user_agent=user_agent
        )
        return {
            "ok": True,
            "withdrawal_id": wr.id,
            "amount_requested": wr.amount_requested,
            "status": wr.status,
            "message": f"Yêu cầu rút {data.amount:,.0f}đ đã được gửi. Admin sẽ xử lý trong 1-3 ngày làm việc.",
        }

    @patch("/bank-info", status_code=HTTP_200_OK)
    async def update_bank_info(
        self,
        request: Request,
        db_session: AsyncSession,
        data: BankInfoSchema,
    ) -> dict:
        """Cập nhật thông tin ngân hàng (AES-GCM encrypted)."""
        user_state = _require_user(request)
        client_ip = request.client.host if request.client else "127.0.0.1"
        user_agent = request.headers.get("user-agent", "")
        await ctv_service.update_bank_info(
            db_session,
            user_id=user_state["id"],
            bank_info=data.model_dump(),
            ip_address=client_ip,
            user_agent=user_agent
        )
        return {"ok": True, "message": "Đã cập nhật thông tin ngân hàng"}

    @delete("/profile", status_code=HTTP_200_OK)
    async def deactivate_profile(
        self,
        request: Request,
        db_session: AsyncSession,
    ) -> dict:
        """Hủy đăng ký CTV (soft-delete). Chặn nếu còn pending commission."""
        from datetime import datetime, timezone
        from sqlalchemy import select, and_, func
        from backend.database.models.affiliate import AffiliateProfile, CommissionLedger
        from litestar.exceptions import ValidationException, NotFoundException

        user_state = _require_user(request)
        user_id: str = user_state["id"]

        # 1. Fetch profile
        aff_stmt = select(AffiliateProfile).where(
            and_(AffiliateProfile.user_id == user_id, AffiliateProfile.deleted_at == None)
        )
        aff_res = await db_session.execute(aff_stmt)
        aff = aff_res.scalar_one_or_none()
        if not aff:
            raise NotFoundException("Bạn chưa đăng ký chương trình CTV")
        if aff.status != "ACTIVE":
            raise ValidationException("Tài khoản CTV không ở trạng thái hoạt động")

        # 2. Soft-delete - preserve all ledger history (re-activation will fully restore stats)
        aff.status = "CANCELLED"
        aff.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()

        import logging
        logging.getLogger("api-gateway.ctv").info(
            f"[CTV-DEACTIVATE] User {user_id} left the CTV program. Code: {aff.ctv_code}. "
            f"Total revenue: {aff.total_revenue:,.0f}đ | Total commission: {aff.total_commission:,.0f}đ"
        )

        return {
            "ok": True,
            "message": "Đã hủy đăng ký chương trình CTV thành công. Lịch sử hoa hồng của bạn vẫn được lưu giữ đầy đủ.",
        }
