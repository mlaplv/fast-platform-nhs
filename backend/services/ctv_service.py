"""
CtvService - Elite V2.2 / Viral 2026
Affiliate (CTV) commission engine with AES-GCM integrity seals,
multi-tier support, anti-fraud guards, and idempotent crediting.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.affiliate import (
    AffiliateProfile, CommissionLedger, CommissionTier, WithdrawalRequest,
)
from backend.database.models.commerce import Order
from backend.constants.commerce import ShippingConfig
from backend.database import current_tenant_id
from backend.utils.security import GeminiSecurity

logger = logging.getLogger("api-gateway.ctv")

# ── Constants ─────────────────────────────────────────────────────────────────
CTV_CODE_PATTERN = re.compile(r"^[A-Z0-9]{4,20}$")
MIN_WITHDRAWAL_VND = 200_000.0
CONFIRMATION_DELAY_HOURS = 72
MAX_REFERRAL_CHAIN_DEPTH = 1  # Chống MLM fraud


# ── Security Helpers ──────────────────────────────────────────────────────────

def _create_commission_seal(ledger: CommissionLedger) -> str:
    """AES-GCM integrity seal - chống tamper DB trực tiếp."""
    return GeminiSecurity.encrypt({
        "id": ledger.id,
        "o": ledger.order_id,
        "a": str(round(ledger.commission_amount, 2)),
        "r": str(round(ledger.rate_applied, 4)),
    })


def _create_withdrawal_seal(wr: WithdrawalRequest) -> str:
    return GeminiSecurity.encrypt({
        "id": wr.id,
        "aff": wr.affiliate_id,
        "amt": str(round(wr.amount_requested, 2)),
    })


def _create_balance_seal(aff: AffiliateProfile) -> str:
    return GeminiSecurity.encrypt({
        "id": aff.id,
        "rev": str(round(aff.total_revenue, 2)),
        "com": str(round(aff.total_commission, 2)),
        "paid": str(round(aff.paid_commission, 2)),
        "ord": aff.total_orders,
    })


def _verify_commission_seal(ledger: CommissionLedger) -> bool:
    if not ledger.integrity_token:
        return True  # Legacy data - no seal yet
    data = GeminiSecurity.decrypt(ledger.integrity_token)
    if not isinstance(data, dict):
        return False
    return (
        data.get("id") == ledger.id
        and data.get("o") == ledger.order_id
        and abs(float(data.get("a", 0)) - ledger.commission_amount) < 0.01
    )


# ── CtvService ────────────────────────────────────────────────────────────────

class CtvService:

    @staticmethod
    async def _get_default_tier(db_session: AsyncSession, tenant_id: Optional[str] = None) -> Optional[CommissionTier]:
        """Get the default commission tier (is_default=True)."""
        tenant = tenant_id or current_tenant_id.get() or "default"
        stmt = select(CommissionTier).where(
            and_(CommissionTier.is_default == True, CommissionTier.tenant_id == tenant)
        ).limit(1)
        res = await db_session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def validate_ctv_code(db_session: AsyncSession, ctv_code: str) -> Optional[AffiliateProfile]:
        """
        Validate CTV code is active. Redis-cacheable at controller layer.
        Returns AffiliateProfile or None if invalid.
        """
        if not ctv_code:
            return None

        # Step 1: Try to decrypt (handles encrypted token or plain code transparently)
        raw = ctv_code.strip()
        # Auto-restore Base64 padding that may have been stripped by frontend sanitizer
        if len(raw) > 20 and len(raw) % 4 != 0:
            raw += '=' * (4 - len(raw) % 4)
        try:
            decrypted = GeminiSecurity.decrypt(raw)
            # Only use decrypted value if it's a non-empty string (not dict/list from JSON)
            if decrypted and isinstance(decrypted, str) and decrypted != raw:
                raw = decrypted.strip()
        except Exception:
            pass  # Decryption failed - treat as plain code

        # Step 2: Normalize
        raw = raw.upper()

        # Step 3: Validate format - reject garbage/tampered tokens
        if not CTV_CODE_PATTERN.match(raw):
            logger.warning(f"[CTV] Invalid code format after normalize: {raw[:20]!r}")
            return None

        stmt = select(AffiliateProfile).where(
            and_(
                AffiliateProfile.ctv_code == raw,
                AffiliateProfile.status == "ACTIVE",
                AffiliateProfile.deleted_at == None,
            )
        )
        res = await db_session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def register_affiliate(
        db_session: AsyncSession,
        user_id: str,
        ctv_code: str,
        referred_by_code: Optional[str] = None,
    ) -> AffiliateProfile:
        """
        Register a user as CTV. Auto-active. Assigns default tier.
        Anti-fraud: blocks chain depth > MAX_REFERRAL_CHAIN_DEPTH.
        """
        from litestar.exceptions import ValidationException

        # Validate code format
        code_upper = ctv_code.upper().strip()
        if not CTV_CODE_PATTERN.match(code_upper):
            raise ValidationException("Mã CTV chỉ được chứa chữ in hoa và số (4-20 ký tự)")

        # Check if user already has an affiliate profile (active or deleted)
        existing_user = await db_session.execute(
            select(AffiliateProfile).where(AffiliateProfile.user_id == user_id)
        )
        aff = existing_user.scalar_one_or_none()

        if aff and aff.deleted_at is None and aff.status != "CANCELLED":
            raise ValidationException("Tài khoản đã đăng ký chương trình CTV")

        # Check uniqueness of the desired CTV code across all profiles (excluding the current user's profile if it exists)
        code_filter = [AffiliateProfile.ctv_code == code_upper]
        if aff:
            code_filter.append(AffiliateProfile.id != aff.id)
        existing_code = await db_session.execute(
            select(AffiliateProfile).where(and_(*code_filter))
        )
        if existing_code.scalar_one_or_none():
            raise ValidationException("Mã CTV đã được sử dụng, vui lòng chọn mã khác")

        # Resolve referrer (optional)
        referred_by_id: Optional[str] = None
        chain_depth = 0
        if referred_by_code:
            referrer = await CtvService.validate_ctv_code(db_session, referred_by_code)
            if referrer:
                if referrer.referral_chain_depth >= MAX_REFERRAL_CHAIN_DEPTH:
                    logger.warning(f"[CTV] Referral chain depth exceeded for {referred_by_code}")
                else:
                    referred_by_id = referrer.id
                    chain_depth = referrer.referral_chain_depth + 1

        # Get default tier
        tenant = current_tenant_id.get() or "default"
        default_tier = await CtvService._get_default_tier(db_session, tenant_id=tenant)

        if aff:
            # REACTIVATE existing profile (Preserve stats and ledger, update status and code)
            aff.status = "ACTIVE"
            aff.deleted_at = None
            aff.ctv_code = code_upper
            aff.commission_tier_id = default_tier.id if default_tier else None
            aff.referral_chain_depth = chain_depth
            aff.referred_by_ctv_id = referred_by_id
            logger.info(f"[CTV] Reactivated affiliate profile {aff.id} with code {code_upper} for user {user_id}")
        else:
            # CREATE new profile
            aff = AffiliateProfile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                ctv_code=code_upper,
                status="ACTIVE",
                commission_tier_id=default_tier.id if default_tier else None,
                total_revenue=0.0,
                total_commission=0.0,
                paid_commission=0.0,
                total_orders=0,
                referral_chain_depth=chain_depth,
                referred_by_ctv_id=referred_by_id,
                tenant_id=tenant,
            )
            db_session.add(aff)
            logger.info(f"[CTV] New affiliate registered: {code_upper} for user {user_id}")

        await db_session.flush()

        # Seal/Re-seal balance
        aff.balance_seal = _create_balance_seal(aff)
        await db_session.commit()
        return aff

    @staticmethod
    async def get_affiliate_by_user(
        db_session: AsyncSession, user_id: str
    ) -> Optional[AffiliateProfile]:
        stmt = (
            select(AffiliateProfile)
            .where(and_(AffiliateProfile.user_id == user_id, AffiliateProfile.deleted_at == None))
        )
        res = await db_session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def verify_financial_integrity(db_session: AsyncSession, aff: AffiliateProfile) -> bool:
        """
        Military-grade Double-Entry Reconciliation Guard.
        Compares cached balance fields with live ledger aggregates.
        Suspends account and raises alert on any discrepancy.
        """
        # 1. Live sum of all earned/confirmed/paid/pending commission from ledger
        ledger_stmt = select(func.sum(CommissionLedger.commission_amount)).where(
            and_(
                CommissionLedger.affiliate_id == aff.id,
                CommissionLedger.status.in_(["PENDING", "CONFIRMED", "PAID"])
            )
        )
        ledger_res = await db_session.execute(ledger_stmt)
        real_total_com = float(ledger_res.scalar() or 0.0)

        # All paid withdrawals
        withdrawal_stmt = select(func.sum(WithdrawalRequest.amount_approved)).where(
            and_(
                WithdrawalRequest.affiliate_id == aff.id,
                WithdrawalRequest.status == "PAID"
            )
        )
        withdrawal_res = await db_session.execute(withdrawal_stmt)
        real_paid_com = float(withdrawal_res.scalar() or 0.0)

        # 2. Check cached values vs live aggregates
        if abs(real_total_com - aff.total_commission) > 0.01 or abs(real_paid_com - aff.paid_commission) > 0.01:
            logger.critical(
                f"[CTV-SECURITY-BREACH] Balance discrepancy detected for affiliate {aff.ctv_code} (ID: {aff.id})! "
                f"Cached total={aff.total_commission}, Real total={real_total_com} | "
                f"Cached paid={aff.paid_commission}, Real paid={real_paid_com}. Account SUSPENDED immediately."
            )
            # Automatic lockdown
            aff.status = "SUSPENDED"
            await db_session.commit()
            
            # Log security event in audit logs
            try:
                from backend.database.models.system import AuditLog
                audit = AuditLog(
                    actor_id="SYSTEM-RECONCILIATION-GUARD",
                    ip_address="127.0.0.1",
                    action="UPDATE",
                    target_table="affiliate_profiles",
                    target_id=aff.id,
                    changes={
                        "error": "Balance integrity mismatch",
                        "cached_total_commission": aff.total_commission,
                        "real_total_commission": real_total_com,
                        "cached_paid_commission": aff.paid_commission,
                        "real_paid_commission": real_paid_com,
                        "status": "SUSPENDED"
                    }
                )
                db_session.add(audit)
                await db_session.commit()
            except Exception as e:
                logger.error(f"[CTV-SECURITY] Failed to write AuditLog: {e}")
                
            return False

        # 3. Verify balance seal
        if aff.balance_seal:
            seal_data = GeminiSecurity.decrypt(aff.balance_seal)
            if not isinstance(seal_data, dict) or \
               abs(float(seal_data.get("com", 0)) - aff.total_commission) > 0.01 or \
               abs(float(seal_data.get("paid", 0)) - aff.paid_commission) > 0.01:
                logger.critical(f"[CTV-SECURITY-BREACH] Balance seal mismatch for affiliate {aff.id}! Account SUSPENDED.")
                aff.status = "SUSPENDED"
                await db_session.commit()
                return False
                
        return True

    @staticmethod
    async def get_dashboard_stats(db_session: AsyncSession, user_id: str) -> dict:
        """
        Returns aggregated dashboard stats for a CTV.
        Reads from pre-aggregated columns - O(1), no GROUP BY.
        """
        from litestar.exceptions import NotFoundException

        aff = await CtvService.get_affiliate_by_user(db_session, user_id)
        if not aff:
            raise NotFoundException("Bạn chưa đăng ký chương trình CTV")

        # Verify integrity seal & live reconciliation (Military-Grade financial protection)
        if not await CtvService.verify_financial_integrity(db_session, aff):
            from litestar.exceptions import ValidationException
            raise ValidationException("Cảnh báo bảo mật hệ thống: Phát hiện tài khoản có số dư không nhất quán. Giao dịch đã bị tạm khóa để bảo vệ tài sản!")

        # Pending commission (not yet CONFIRMED)
        pending_stmt = select(func.sum(CommissionLedger.commission_amount)).where(
            and_(
                CommissionLedger.affiliate_id == aff.id,
                CommissionLedger.status == "PENDING",
            )
        )
        pending_res = await db_session.execute(pending_stmt)
        pending_amount = float(pending_res.scalar() or 0.0)

        available_to_withdraw = aff.total_commission - aff.paid_commission - pending_amount

        # Decrypt bank info for authenticated owner pre-fill / display
        bank_info = None
        if aff.bank_info_enc:
            try:
                decrypted_bank = GeminiSecurity.decrypt(aff.bank_info_enc)
                if isinstance(decrypted_bank, dict):
                    bank_info = {
                        "bank": decrypted_bank.get("bank"),
                        "account_no": decrypted_bank.get("account_no"),
                        "account_name": decrypted_bank.get("account_name"),
                    }
            except Exception as e:
                logger.error(f"[CTV-BANK] Failed to decrypt bank details for affiliate {aff.id}: {e}")

        encrypted_token = GeminiSecurity.encrypt(aff.ctv_code)
        
        # Load all active tiers dynamically for the tenant to prevent frontend hardcoding
        from backend.database import current_tenant_id
        from backend.database.models.affiliate import CommissionTier
        tiers_stmt = select(CommissionTier).where(
            and_(
                CommissionTier.tenant_id == (current_tenant_id.get() or "default"),
                CommissionTier.deleted_at == None
            )
        ).order_by(CommissionTier.min_revenue_threshold)
        tiers_res = await db_session.execute(tiers_stmt)
        tiers_list = tiers_res.scalars().all()

        active_tier = aff.tier
        if not active_tier:
            try:
                active_tier = await CtvService._get_default_tier(db_session, aff.tenant_id)
            except Exception:
                pass

        return {
            "is_registered": True,
            "ctv_code": aff.ctv_code,
            "encrypted_code": encrypted_token,
            "status": aff.status,
            "bank_info": bank_info,
            "tier": {
                "name": active_tier.name if active_tier else "Đồng",
                "commission_rate": active_tier.commission_rate if active_tier else 0.05,
                "min_revenue_threshold": active_tier.min_revenue_threshold if active_tier else 0.0,
            },
            "stats": {
                "total_revenue": aff.total_revenue,
                "total_commission": aff.total_commission,
                "paid_commission": aff.paid_commission,
                "pending_commission": pending_amount,
                "available_to_withdraw": max(0.0, available_to_withdraw),
                "total_orders": aff.total_orders,
            },
            "tiers": [
                {
                    "name": t.name,
                    "commission_rate": t.commission_rate,
                    "min_revenue_threshold": t.min_revenue_threshold,
                    "bonus_rate": t.bonus_rate
                }
                for t in tiers_list
            ],
            "referral_link": f"/?ctv={encrypted_token}",
        }

    @staticmethod
    async def _get_actual_shipping_fee(order: Order) -> float:
        """
        Dynamically extracts shipping fee from order metadata (immutable snapshot).
        If not recorded or if it is 0.0 (meaning free-shipped to customer, but merchant still pays),
        fetches default standard shipping fee from dynamic Redis configuration.
        """
        shipping_fee = order.order_metadata.get("shipping_fee") if order.order_metadata else None
        if shipping_fee is not None and float(shipping_fee) > 0.0:
            return float(shipping_fee)

        fallback_ship = ShippingConfig.STANDARD_FEE
        try:
            from backend.services.xohi_memory import xohi_memory
            if xohi_memory._use_redis:
                redis_fee = await xohi_memory.client.get("config:shipping:default_fee")
                if redis_fee:
                    fallback_ship = float(redis_fee)
        except Exception as e:
            logger.error(f"[CTV] Failed to fetch dynamic shipping fee: {e}")
        return fallback_ship

    @staticmethod
    async def credit_commission(db_session: AsyncSession, order_id: str) -> bool:
        """
        Idempotent commission credit - called at checkout.
        Creates PENDING ledger entry (tiền chờ). Later when DELIVERED,
        confirm_pending_commissions() promotes PENDING -> CONFIRMED (tiền thực).

        Anti-fraud rules:
        1. Idempotency: skip if order_id already in commission_ledger
        2. Self-referral: skip if order.user_id == affiliate.user_id
        3. AES-GCM seal on each ledger entry
        """
        # 1. Load order
        order_stmt = select(Order).where(Order.id == order_id)
        order_res = await db_session.execute(order_stmt)
        order: Optional[Order] = order_res.scalar_one_or_none()

        if not order or not order.ctv_code:
            return False  # No CTV attribution

        # 2. Idempotency guard
        existing_stmt = select(CommissionLedger).where(CommissionLedger.order_id == order_id)
        existing = await db_session.execute(existing_stmt)
        if existing.scalar_one_or_none():
            logger.info(f"[CTV] Commission already credited for order {order_id} - skipping")
            return False

        # 3. Load affiliate with tier loaded
        from sqlalchemy.orm import joinedload
        aff_stmt = (
            select(AffiliateProfile)
            .options(joinedload(AffiliateProfile.tier))
            .where(
                and_(
                    AffiliateProfile.ctv_code == order.ctv_code,
                    AffiliateProfile.status == "ACTIVE",
                    AffiliateProfile.deleted_at == None,
                )
            )
        )
        aff_res = await db_session.execute(aff_stmt)
        aff: Optional[AffiliateProfile] = aff_res.scalar_one_or_none()

        if not aff:
            logger.warning(f"[CTV] Affiliate not found for code {order.ctv_code}")
            return False

        # 4. Self-referral block (silent)
        if order.user_id == aff.user_id:
            logger.warning(f"[CTV-FRAUD] Self-referral blocked: code={order.ctv_code}, order={order_id}")
            return False

        # 5. Determine commission rate from tier (database default if no tier assigned)
        default_tier = await CtvService._get_default_tier(db_session, tenant_id=aff.tenant_id)
        default_rate = default_tier.commission_rate if default_tier else 0.05
        default_name = default_tier.name if default_tier else "Đồng"

        rate = default_rate
        tier_snapshot: dict = {"name": default_name, "commission_rate": rate}
        if aff.tier:
            rate = aff.tier.commission_rate
            tier_snapshot = {"name": aff.tier.name, "commission_rate": rate}

        # R102 Dynamic Pricing: Deduct actual shipping fee and 3% tax from base revenue for commission calculation
        shipping_fee = await CtvService._get_actual_shipping_fee(order)
        tax_rate = 0.03  # 3% tax
        tax_deduction = round((order.total_amount - shipping_fee) * tax_rate, 2)
        
        # Revenue Net (Doanh thu thuần sau thuế và ship)
        revenue_net = max(0.0, (order.total_amount - shipping_fee) * (1.0 - tax_rate))
        commission_amount = round(revenue_net * rate, 2)

        # Store detailed breakdown for tooltip transparency
        import json
        breakdown = {
            "order_total": order.total_amount,
            "shipping_fee": shipping_fee,
            "tax_rate": tax_rate,
            "tax_deduction": tax_deduction,
            "revenue_net": revenue_net,
            "rate_applied": rate,
            "commission_amount": commission_amount
        }
        admin_note = json.dumps(breakdown)

        # 6. Create ledger entry
        ledger = CommissionLedger(
            id=str(uuid.uuid4()),
            affiliate_id=aff.id,
            order_id=order_id,
            order_amount=revenue_net,  # Record net revenue for clarity
            commission_amount=commission_amount,
            rate_applied=rate,
            tier_snapshot=tier_snapshot,
            status="PENDING",
            admin_note=admin_note,
            tenant_id=aff.tenant_id or current_tenant_id.get() or "default",
        )
        ledger.integrity_token = _create_commission_seal(ledger)
        db_session.add(ledger)

        # 7. Update affiliate aggregated stats
        aff.total_revenue += revenue_net
        aff.total_commission += commission_amount
        aff.total_orders += 1
        aff.balance_seal = _create_balance_seal(aff)

        # 8. Auto-upgrade tier if threshold crossed
        await CtvService._maybe_upgrade_tier(db_session, aff)

        await db_session.commit()

        logger.info(
            f"[CTV] Commission credited: {commission_amount:,.0f}đ ({rate*100:.0f}%) "
            f"for affiliate {aff.ctv_code} | order {order_id}"
        )
        return True

    @staticmethod
    async def confirm_pending_commissions(db_session: AsyncSession, order_id: str) -> bool:
        """
        Called when order transitions to DELIVERED: move PENDING → CONFIRMED.
        Commission becomes available for withdrawal after confirmation.
        """
        stmt = select(CommissionLedger).where(
            and_(CommissionLedger.order_id == order_id, CommissionLedger.status == "PENDING")
        )
        res = await db_session.execute(stmt)
        ledger: Optional[CommissionLedger] = res.scalar_one_or_none()
        if not ledger:
            return False

        # Verify integrity before confirming
        if not _verify_commission_seal(ledger):
            logger.error(f"[CTV-SECURITY] Integrity seal mismatch for ledger {ledger.id}!")
            return False

        ledger.status = "CONFIRMED"
        ledger.confirmed_at = datetime.now(timezone.utc)
        await db_session.commit()
        logger.info(f"[CTV] Commission confirmed: {ledger.id}")
        return True

    @staticmethod
    async def void_commission(db_session: AsyncSession, order_id: str) -> bool:
        """
        Called when order is CANCELLED: void PENDING commission entry.
        Deducts from affiliate aggregated stats and marks ledger as VOIDED.
        """
        stmt = select(CommissionLedger).where(
            and_(CommissionLedger.order_id == order_id, CommissionLedger.status == "PENDING")
        )
        res = await db_session.execute(stmt)
        ledger: Optional[CommissionLedger] = res.scalar_one_or_none()
        if not ledger:
            return False  # Nothing to void

        # Rollback affiliate aggregated stats
        aff_stmt = select(AffiliateProfile).where(AffiliateProfile.id == ledger.affiliate_id)
        aff_res = await db_session.execute(aff_stmt)
        aff: Optional[AffiliateProfile] = aff_res.scalar_one_or_none()

        if aff:
            aff.total_revenue = max(0.0, aff.total_revenue - ledger.order_amount)
            aff.total_commission = max(0.0, aff.total_commission - ledger.commission_amount)
            aff.total_orders = max(0, aff.total_orders - 1)
            aff.balance_seal = _create_balance_seal(aff)
            logger.info(f"[CTV] Rolled back stats for affiliate {aff.ctv_code}: -{ledger.commission_amount:,.0f}đ")

        ledger.status = "VOIDED"
        await db_session.commit()
        logger.info(f"[CTV] Commission voided: {ledger.id} for order {order_id}")
        return True

    @staticmethod
    async def _maybe_upgrade_tier(db_session: AsyncSession, aff: AffiliateProfile) -> None:
        """Auto-upgrade tier based on total_revenue. Never auto-downgrade."""
        tenant = current_tenant_id.get() or "default"
        tiers_stmt = select(CommissionTier).where(
            and_(
                CommissionTier.tenant_id == tenant,
                CommissionTier.deleted_at == None,
            )
        ).order_by(CommissionTier.min_revenue_threshold.desc())
        tiers_res = await db_session.execute(tiers_stmt)
        tiers = tiers_res.scalars().all()

        for tier in tiers:
            if aff.total_revenue >= tier.min_revenue_threshold:
                # Only upgrade, never downgrade
                current_threshold = aff.tier.min_revenue_threshold if aff.tier else 0.0
                if tier.min_revenue_threshold > current_threshold:
                    aff.commission_tier_id = tier.id
                    logger.info(f"[CTV] Affiliate {aff.ctv_code} upgraded to tier: {tier.name}")
                break

    @staticmethod
    async def request_withdrawal(
        db_session: AsyncSession,
        user_id: str,
        amount: float,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> WithdrawalRequest:
        """Submit a withdrawal request. Snapshots bank_info at request time."""
        from litestar.exceptions import ValidationException

        aff = await CtvService.get_affiliate_by_user(db_session, user_id)
        if not aff:
            raise ValidationException("Bạn chưa đăng ký chương trình CTV")
        if aff.status != "ACTIVE":
            raise ValidationException("Tài khoản CTV không ở trạng thái hoạt động")
        if not aff.bank_info_enc:
            raise ValidationException("Vui lòng cập nhật thông tin ngân hàng trước khi rút tiền")
        if amount < MIN_WITHDRAWAL_VND:
            raise ValidationException(f"Số tiền rút tối thiểu là {MIN_WITHDRAWAL_VND:,.0f}đ")

        # Calculate available balance (dashboard_stats automatically reconciles balance)
        stats = await CtvService.get_dashboard_stats(db_session, user_id)
        available = stats["stats"]["available_to_withdraw"]
        if amount > available:
            raise ValidationException(f"Số dư khả dụng chỉ còn {available:,.0f}đ")

        # Check max monthly withdrawal for tier
        if aff.tier and amount > aff.tier.max_withdrawal_per_month:
            raise ValidationException(
                f"Tier {aff.tier.name} giới hạn rút tối đa {aff.tier.max_withdrawal_per_month:,.0f}đ/tháng"
            )

        # Check no pending request
        pending_wr = await db_session.execute(
            select(WithdrawalRequest).where(
                and_(WithdrawalRequest.affiliate_id == aff.id, WithdrawalRequest.status == "PENDING")
            )
        )
        if pending_wr.scalar_one_or_none():
            raise ValidationException("Bạn đã có yêu cầu rút tiền đang chờ xử lý")

        wr = WithdrawalRequest(
            id=str(uuid.uuid4()),
            affiliate_id=aff.id,
            amount_requested=amount,
            bank_snapshot_enc=aff.bank_info_enc,  # Snapshot tại thời điểm request
            status="PENDING",
            tenant_id=current_tenant_id.get() or "default",
        )
        wr.integrity_token = _create_withdrawal_seal(wr)
        db_session.add(wr)
        
        # Forensic Log of Withdrawal submission
        try:
            from backend.database.models.system import AuditLog
            audit = AuditLog(
                actor_id=user_id,
                ip_address=ip_address or "127.0.0.1",
                user_agent=user_agent,
                action="INSERT",
                target_table="withdrawal_requests",
                target_id=wr.id,
                changes={
                    "amount_requested": amount,
                    "action": "Submitted withdrawal request"
                }
            )
            db_session.add(audit)
        except Exception as e:
            logger.error(f"[CTV-SECURITY] Failed to write AuditLog: {e}")

        await db_session.commit()
        logger.info(f"[CTV] Withdrawal request: {amount:,.0f}đ by affiliate {aff.ctv_code}")
        return wr

    @staticmethod
    async def update_bank_info(
        db_session: AsyncSession,
        user_id: str,
        bank_info: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Update bank info (AES-GCM encrypted). Validates required fields."""
        from litestar.exceptions import ValidationException

        required = {"bank", "account_no", "account_name"}
        if not required.issubset(bank_info.keys()):
            raise ValidationException("Thiếu thông tin ngân hàng: bank, account_no, account_name")

        aff = await CtvService.get_affiliate_by_user(db_session, user_id)
        if not aff:
            raise ValidationException("Bạn chưa đăng ký chương trình CTV")

        aff.bank_info_enc = GeminiSecurity.encrypt(bank_info)
        
        # Forensic Log of bank details changes
        try:
            from backend.database.models.system import AuditLog
            audit = AuditLog(
                actor_id=user_id,
                ip_address=ip_address or "127.0.0.1",
                user_agent=user_agent,
                action="UPDATE",
                target_table="affiliate_profiles",
                target_id=aff.id,
                changes={
                    "field": "bank_info_enc",
                    "action": "Updated encrypted bank details"
                }
            )
            db_session.add(audit)
        except Exception as e:
            logger.error(f"[CTV-SECURITY] Failed to write AuditLog: {e}")

        await db_session.commit()
        return True

    @staticmethod
    async def cancel_commission(db_session: AsyncSession, order_id: str) -> bool:
        """
        Handles order cancellation/return (boom).
        1. Revokes the credited commission (deducts from affiliate total revenue and commission balance).
        2. Applies penalty x2 shipping fee due to delivery losses on returned orders.
        3. Creates negative ledger entry for accountability and anti-tamper seals.
        """
        # 1. Load order
        order_stmt = select(Order).where(Order.id == order_id)
        order_res = await db_session.execute(order_stmt)
        order: Optional[Order] = order_res.scalar_one_or_none()
        if not order:
            return False

        # 2. Find original ledger entry
        ledger_stmt = select(CommissionLedger).where(
            and_(
                CommissionLedger.order_id == order_id,
                CommissionLedger.status.in_(["PENDING", "CONFIRMED"])
            )
        )
        ledger_res = await db_session.execute(ledger_stmt)
        ledger: Optional[CommissionLedger] = ledger_res.scalar_one_or_none()
        if not ledger:
            return False  # No commission was credited for this order or already cancelled

        # 3. Load affiliate
        aff_stmt = select(AffiliateProfile).where(AffiliateProfile.id == ledger.affiliate_id)
        aff_res = await db_session.execute(aff_stmt)
        aff: Optional[AffiliateProfile] = aff_res.scalar_one_or_none()
        if not aff:
            return False

        # 4. Reconcile and subtract credited amounts
        aff.total_revenue = max(0.0, aff.total_revenue - ledger.order_amount)
        aff.total_commission = max(0.0, aff.total_commission - ledger.commission_amount)

        # 5. Apply Penalty x2 Shipping Fee for boom/returned orders
        shipping_fee = await CtvService._get_actual_shipping_fee(order)
        penalty = shipping_fee * 2.0
        aff.total_commission = max(0.0, aff.total_commission - penalty)

        # 6. Mark original ledger cancelled
        ledger.status = "CANCELLED"
        
        # 7. Create penalty log ledger
        penalty_ledger = CommissionLedger(
            id=str(uuid.uuid4()),
            affiliate_id=aff.id,
            order_id=order_id,
            order_amount=0.0,
            commission_amount=-penalty,
            rate_applied=0.0,
            tier_snapshot={"name": "Penalty", "reason": "Order Boom/Return x2 Ship Penalty"},
            status="CANCELLED",
            tenant_id=aff.tenant_id,
        )
        penalty_ledger.integrity_token = _create_commission_seal(penalty_ledger)
        db_session.add(penalty_ledger)

        # 8. Update balance seal
        aff.balance_seal = _create_balance_seal(aff)
        await db_session.commit()

        logger.info(
            f"[CTV-PENALTY] Cancelled commission for order {order_id} | "
            f"Deducted {ledger.commission_amount:,.0f}đ commission | "
            f"Applied {penalty:,.0f}đ penalty (x2 shipping fee) to affiliate {aff.ctv_code}"
        )
        return True

    @staticmethod
    def get_referral_link(ctv_code: str, base_url: str = "https://osmo.vn") -> str:
        return f"{base_url.rstrip('/')}/?ctv={ctv_code.upper()}"


ctv_service = CtvService()
