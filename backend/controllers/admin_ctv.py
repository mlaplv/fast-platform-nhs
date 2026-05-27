"""
Admin CTV Management Controller — Elite V2.2 / Viral 2026
Endpoints: /api/v1/admin/ctv/*
Auth: Admin JWT required. Full commission management + withdrawal approval.
"""
from typing import Optional
from datetime import datetime, timezone
from litestar import Controller, Request, get, post, patch
from litestar.status_codes import HTTP_200_OK
from litestar.exceptions import NotAuthorizedException
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.database.models.affiliate import (
    AffiliateProfile, CommissionLedger, CommissionTier, WithdrawalRequest,
)
from backend.services.ctv_service import ctv_service, _create_balance_seal, _create_withdrawal_seal
from backend.utils.security import GeminiSecurity


def _require_admin(request: Request) -> dict:
    user_state = request.scope.get("state", {}).get("user")
    if not user_state:
        raise NotAuthorizedException("Yêu cầu đăng nhập")
    roles = user_state.get("roles", [])
    if "ADMIN" not in roles and "SUPER_ADMIN" not in roles:
        raise NotAuthorizedException("Yêu cầu quyền Admin")
    return user_state


class TierCreateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    min_revenue_threshold: float = Field(0.0, ge=0)
    commission_rate: float = Field(0.15, ge=0.0, le=1.0)
    bonus_rate: float = Field(0.0, ge=0.0)
    max_withdrawal_per_month: float = Field(50_000_000.0, ge=0)
    is_default: bool = False


class TierUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    min_revenue_threshold: Optional[float] = Field(None, ge=0)
    commission_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    bonus_rate: Optional[float] = Field(None, ge=0.0)
    max_withdrawal_per_month: Optional[float] = Field(None, ge=0)
    is_default: Optional[bool] = None


class StatusUpdateSchema(BaseModel):
    status: str = Field(..., pattern=r"^(ACTIVE|SUSPENDED|BANNED)$")
    note: Optional[str] = None


class TierAssignSchema(BaseModel):
    tier_id: str


class PayoutSchema(BaseModel):
    withdrawal_id: str
    amount_approved: float = Field(..., ge=0)
    note: Optional[str] = None


class AdminCtvController(Controller):
    """Admin: Full CTV management — tiers, members, withdrawals, stats."""
    path = "/api/v1/admin/ctv"
    guards = []

    # ── Commission Tiers ─────────────────────────────────────────────────────

    @get("/tiers")
    async def list_tiers(self, request: Request, db_session: AsyncSession) -> list:
        """Danh sách commission tiers."""
        _require_admin(request)
        from backend.database import current_tenant_id
        tenant = current_tenant_id.get() or "default"
        stmt = (
            select(CommissionTier)
            .where(and_(CommissionTier.tenant_id == tenant, CommissionTier.deleted_at == None))
            .order_by(CommissionTier.min_revenue_threshold)
        )
        res = await db_session.execute(stmt)
        tiers = res.scalars().all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "min_revenue_threshold": t.min_revenue_threshold,
                "commission_rate": t.commission_rate,
                "commission_rate_pct": f"{t.commission_rate * 100:.1f}%",
                "bonus_rate": t.bonus_rate,
                "max_withdrawal_per_month": t.max_withdrawal_per_month,
                "is_default": t.is_default,
            }
            for t in tiers
        ]

    @post("/tiers", status_code=HTTP_200_OK)
    async def create_tier(self, request: Request, db_session: AsyncSession, data: TierCreateSchema) -> dict:
        """Tạo commission tier mới."""
        _require_admin(request)
        import uuid
        from backend.database import current_tenant_id
        tier = CommissionTier(
            id=str(uuid.uuid4()),
            name=data.name,
            min_revenue_threshold=data.min_revenue_threshold,
            commission_rate=data.commission_rate,
            bonus_rate=data.bonus_rate,
            max_withdrawal_per_month=data.max_withdrawal_per_month,
            is_default=data.is_default,
            tenant_id=current_tenant_id.get() or "default",
        )
        db_session.add(tier)
        await db_session.commit()
        return {"ok": True, "id": tier.id, "message": f"Đã tạo tier: {tier.name}"}

    @patch("/tiers/{tier_id:str}", status_code=HTTP_200_OK)
    async def update_tier(
        self, request: Request, db_session: AsyncSession, tier_id: str, data: TierUpdateSchema
    ) -> dict:
        """Cập nhật commission tier (rate, threshold, v.v.)."""
        _require_admin(request)
        from litestar.exceptions import NotFoundException
        stmt = select(CommissionTier).where(CommissionTier.id == tier_id)
        res = await db_session.execute(stmt)
        tier = res.scalar_one_or_none()
        if not tier:
            raise NotFoundException("Tier không tồn tại")

        if data.name is not None:
            tier.name = data.name
        if data.commission_rate is not None:
            tier.commission_rate = data.commission_rate
        if data.min_revenue_threshold is not None:
            tier.min_revenue_threshold = data.min_revenue_threshold
        if data.bonus_rate is not None:
            tier.bonus_rate = data.bonus_rate
        if data.max_withdrawal_per_month is not None:
            tier.max_withdrawal_per_month = data.max_withdrawal_per_month
        if data.is_default is not None:
            tier.is_default = data.is_default

        await db_session.commit()
        return {"ok": True, "message": f"Đã cập nhật tier: {tier.name}"}

    # ── CTV Members ──────────────────────────────────────────────────────────

    @get("/members")
    async def list_members(
        self,
        request: Request,
        db_session: AsyncSession,
        page: int = 1,
        page_size: int = 30,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """Danh sách CTV toàn hệ thống — filter, search, phân trang."""
        _require_admin(request)
        from backend.database import current_tenant_id
        from backend.database.models.auth import User
        tenant = current_tenant_id.get() or "default"

        conditions = [
            AffiliateProfile.tenant_id == tenant,
            AffiliateProfile.deleted_at == None,
        ]
        if status:
            conditions.append(AffiliateProfile.status == status.upper())
        if search:
            conditions.append(AffiliateProfile.ctv_code.ilike(f"%{search}%"))

        count_res = await db_session.execute(
            select(func.count()).select_from(AffiliateProfile).where(and_(*conditions))
        )
        total = count_res.scalar() or 0

        from sqlalchemy.orm import joinedload
        stmt = (
            select(AffiliateProfile)
            .options(joinedload(AffiliateProfile.tier))
            .where(and_(*conditions))
            .order_by(desc(AffiliateProfile.total_revenue))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await db_session.execute(stmt)
        members = res.scalars().all()

        # Get default tier dynamically to prevent hardcoding fallbacks
        default_tier = await ctv_service._get_default_tier(db_session)
        default_rate = default_tier.commission_rate if default_tier else 0.15
        default_name = default_tier.name if default_tier else "Đồng"

        return {
            "items": [
                {
                    "id": m.id,
                    "ctv_code": m.ctv_code,
                    "user_id": m.user_id,
                    "status": m.status,
                    "tier_name": m.tier.name if m.tier else default_name,
                    "commission_rate_pct": f"{(m.tier.commission_rate if m.tier else default_rate) * 100:.1f}%",
                    "total_revenue": m.total_revenue,
                    "total_commission": m.total_commission,
                    "paid_commission": m.paid_commission,
                    "total_orders": m.total_orders,
                    "registered_at": m.created_at.isoformat(),
                }
                for m in members
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @patch("/members/{affiliate_id:str}/status", status_code=HTTP_200_OK)
    async def update_member_status(
        self, request: Request, db_session: AsyncSession, affiliate_id: str, data: StatusUpdateSchema
    ) -> dict:
        """Approve / Suspend / Ban CTV. Ghi AuditLog."""
        _require_admin(request)
        from litestar.exceptions import NotFoundException
        stmt = select(AffiliateProfile).where(AffiliateProfile.id == affiliate_id)
        res = await db_session.execute(stmt)
        aff = res.scalar_one_or_none()
        if not aff:
            raise NotFoundException("CTV không tồn tại")

        old_status = aff.status
        aff.status = data.status
        await db_session.commit()

        import logging
        logging.getLogger("api-gateway.ctv").info(
            f"[CTV-ADMIN] {request.scope.get('state', {}).get('user', {}).get('email')} changed status: "
            f"{aff.ctv_code} {old_status} → {data.status}. Note: {data.note}"
        )
        return {"ok": True, "message": f"Đã cập nhật trạng thái CTV {aff.ctv_code} → {data.status}"}

    @patch("/members/{affiliate_id:str}/tier", status_code=HTTP_200_OK)
    async def assign_tier(
        self, request: Request, db_session: AsyncSession, affiliate_id: str, data: TierAssignSchema
    ) -> dict:
        """Thay đổi tier thủ công cho CTV."""
        _require_admin(request)
        from litestar.exceptions import NotFoundException
        aff_res = await db_session.execute(select(AffiliateProfile).where(AffiliateProfile.id == affiliate_id))
        aff = aff_res.scalar_one_or_none()
        if not aff:
            raise NotFoundException("CTV không tồn tại")

        tier_res = await db_session.execute(select(CommissionTier).where(CommissionTier.id == data.tier_id))
        tier = tier_res.scalar_one_or_none()
        if not tier:
            raise NotFoundException("Tier không tồn tại")

        aff.commission_tier_id = tier.id
        aff.balance_seal = _create_balance_seal(aff)
        await db_session.commit()
        return {"ok": True, "message": f"Đã gán tier {tier.name} cho CTV {aff.ctv_code}"}

    # ── Withdrawals ──────────────────────────────────────────────────────────

    @get("/withdrawals")
    async def list_withdrawals(
        self,
        request: Request,
        db_session: AsyncSession,
        page: int = 1,
        page_size: int = 30,
        status: Optional[str] = None,
    ) -> dict:
        """Danh sách yêu cầu rút tiền — filter theo status."""
        _require_admin(request)
        from backend.database import current_tenant_id
        tenant = current_tenant_id.get() or "default"

        conditions = [WithdrawalRequest.tenant_id == tenant]
        if status:
            conditions.append(WithdrawalRequest.status == status.upper())

        count_res = await db_session.execute(
            select(func.count()).select_from(WithdrawalRequest).where(and_(*conditions))
        )
        total = count_res.scalar() or 0

        stmt = (
            select(WithdrawalRequest)
            .where(and_(*conditions))
            .order_by(desc(WithdrawalRequest.requested_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await db_session.execute(stmt)
        items = res.scalars().all()

        result = []
        for wr in items:
            # Decrypt bank snapshot (mask account number for display)
            bank = {}
            if wr.bank_snapshot_enc:
                raw = GeminiSecurity.decrypt(wr.bank_snapshot_enc)
                if isinstance(raw, dict):
                    acct = str(raw.get("account_no", ""))
                    bank = {
                        "bank": raw.get("bank"),
                        "account_no": f"{'*' * (len(acct) - 4)}{acct[-4:]}" if len(acct) > 4 else acct,
                        "account_name": raw.get("account_name"),
                    }
            result.append({
                "id": wr.id,
                "affiliate_id": wr.affiliate_id,
                "ctv_code": wr.affiliate.ctv_code if wr.affiliate else None,
                "amount_requested": wr.amount_requested,
                "amount_approved": wr.amount_approved,
                "bank_info": bank,
                "status": wr.status,
                "requested_at": wr.requested_at.isoformat(),
                "processed_at": wr.processed_at.isoformat() if wr.processed_at else None,
                "admin_note": wr.admin_note,
            })

        return {"items": result, "total": total, "page": page, "page_size": page_size}

    @post("/withdrawals/payout", status_code=HTTP_200_OK)
    async def process_payout(
        self, request: Request, db_session: AsyncSession, data: PayoutSchema
    ) -> dict:
        """Approve + ghi nhận đã thanh toán. Cập nhật paid_commission."""
        user_state = _require_admin(request)
        from litestar.exceptions import NotFoundException, ValidationException
        wr_res = await db_session.execute(
            select(WithdrawalRequest).where(WithdrawalRequest.id == data.withdrawal_id)
        )
        wr: Optional[WithdrawalRequest] = wr_res.scalar_one_or_none()
        if not wr:
            raise NotFoundException("Yêu cầu rút tiền không tồn tại")
        if wr.status not in ("PENDING", "APPROVED"):
            raise ValidationException(f"Yêu cầu đã ở trạng thái {wr.status}")
        
        # Verify withdrawal request integrity token (military-grade anti-tamper check)
        if wr.integrity_token:
            seal_data = GeminiSecurity.decrypt(wr.integrity_token)
            if not isinstance(seal_data, dict) or \
               seal_data.get("id") != wr.id or \
               seal_data.get("aff") != wr.affiliate_id or \
               abs(float(seal_data.get("amt", 0)) - wr.amount_requested) > 0.01:
                import logging
                logging.getLogger("api-gateway.ctv").critical(
                    f"[CTV-SECURITY-BREACH] Withdrawal request tampered! id={wr.id}"
                )
                raise ValidationException("Cảnh báo an ninh: Phát hiện yêu cầu rút tiền bị can thiệp trái phép. Từ chối phê duyệt!")

        # Atomic: Update withdrawal + affiliate paid stats
        wr.status = "PAID"
        wr.amount_approved = data.amount_approved
        wr.processed_at = datetime.now(timezone.utc)
        wr.admin_id = user_state["id"]
        wr.admin_note = data.note

        # Update commission ledger entries to PAID
        ledger_stmt = select(CommissionLedger).where(
            and_(
                CommissionLedger.affiliate_id == wr.affiliate_id,
                CommissionLedger.status == "CONFIRMED",
            )
        )
        ledger_res = await db_session.execute(ledger_stmt)
        ledgers = ledger_res.scalars().all()
        total_paid = 0.0
        for ledger in ledgers:
            ledger.status = "PAID"
            ledger.paid_at = datetime.now(timezone.utc)
            total_paid += ledger.commission_amount

        # Update affiliate paid_commission
        aff_res = await db_session.execute(
            select(AffiliateProfile).where(AffiliateProfile.id == wr.affiliate_id)
        )
        aff = aff_res.scalar_one_or_none()
        if aff:
            # Reconcile BEFORE updating stats (Military-Grade financial protection)
            if not await ctv_service.verify_financial_integrity(db_session, aff):
                raise ValidationException("Cảnh báo bảo mật hệ thống: Phát hiện tài khoản có số dư không nhất quán. Giao dịch đã bị tạm khóa để bảo vệ tài sản!")

            aff.paid_commission += data.amount_approved
            aff.balance_seal = _create_balance_seal(aff)

        await db_session.commit()
        return {
            "ok": True,
            "message": f"Đã ghi nhận thanh toán {data.amount_approved:,.0f}đ cho CTV",
        }

    # ── Global Stats ─────────────────────────────────────────────────────────

    @get("/stats")
    async def global_stats(self, request: Request, db_session: AsyncSession) -> dict:
        """Dashboard tổng quan CTV toàn hệ thống."""
        _require_admin(request)
        from backend.database import current_tenant_id
        tenant = current_tenant_id.get() or "default"

        total_ctv = await db_session.scalar(
            select(func.count()).select_from(AffiliateProfile)
            .where(and_(AffiliateProfile.tenant_id == tenant, AffiliateProfile.deleted_at == None))
        )
        active_ctv = await db_session.scalar(
            select(func.count()).select_from(AffiliateProfile)
            .where(and_(AffiliateProfile.tenant_id == tenant, AffiliateProfile.status == "ACTIVE"))
        )
        total_gmv = await db_session.scalar(
            select(func.sum(AffiliateProfile.total_revenue))
            .where(AffiliateProfile.tenant_id == tenant)
        )
        total_commission = await db_session.scalar(
            select(func.sum(AffiliateProfile.total_commission))
            .where(AffiliateProfile.tenant_id == tenant)
        )
        pending_withdrawals = await db_session.scalar(
            select(func.count()).select_from(WithdrawalRequest)
            .where(and_(WithdrawalRequest.tenant_id == tenant, WithdrawalRequest.status == "PENDING"))
        )

        # Leaderboard (ẩn danh: CTV***01)
        top_stmt = (
            select(AffiliateProfile)
            .where(and_(AffiliateProfile.tenant_id == tenant, AffiliateProfile.status == "ACTIVE"))
            .order_by(desc(AffiliateProfile.total_revenue))
            .limit(10)
        )
        top_res = await db_session.execute(top_stmt)
        top_ctv = top_res.scalars().all()

        def mask_code(code: str) -> str:
            return f"{code[:3]}***{code[-2:]}" if len(code) > 5 else f"{code[:2]}***"

        return {
            "summary": {
                "total_ctv": total_ctv or 0,
                "active_ctv": active_ctv or 0,
                "total_gmv": total_gmv or 0.0,
                "total_commission": total_commission or 0.0,
                "pending_withdrawals": pending_withdrawals or 0,
            },
            "leaderboard": [
                {
                    "rank": i + 1,
                    "ctv_code_masked": mask_code(m.ctv_code),
                    "total_revenue": m.total_revenue,
                    "total_orders": m.total_orders,
                    "tier": m.tier.name if m.tier else "Đồng",
                }
                for i, m in enumerate(top_ctv)
            ],
        }
