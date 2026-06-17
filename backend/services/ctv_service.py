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

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.affiliate import (
    AffiliateProfile, CommissionLedger, CommissionTier, WithdrawalRequest,
)
from backend.database.models.commerce import Order
from backend.constants.commerce import ShippingConfig
from backend.database import current_tenant_id
from backend.utils.security import GeminiSecurity
from backend.utils.uid import new_id

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
        "a": str(int(ledger.commission_amount)),   # BigInteger VNĐ
        "r": str(int(ledger.rate_applied_bps)),     # bps integer
    })


def _create_withdrawal_seal(wr: WithdrawalRequest) -> str:
    return GeminiSecurity.encrypt({
        "id": wr.id,
        "aff": wr.affiliate_id,
        "amt": str(int(wr.amount_requested)),  # BigInteger VNĐ
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
                id=new_id(),
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
    async def _verify_balance_seal_only(aff: AffiliateProfile) -> bool:
        """
        #12 Fix: Fast-path seal check — O(1), zero DB query.
        Chỉ verify AES-GCM seal, không chạy aggregate query.
        Full reconciliation (verify_financial_integrity) được chuyển sang arq background job thêu Sếp!
        """
        if not aff.balance_seal:
            return True  # Legacy data — no seal yet, allow
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            seal_data = await loop.run_in_executor(
                None,
                lambda: GeminiSecurity.decrypt(aff.balance_seal)
            )
        except Exception:
            return False
        if not isinstance(seal_data, dict):
            return False
        return (
            seal_data.get("id") == aff.id
            and abs(float(seal_data.get("com", 0)) - aff.total_commission) < 0.01
            and abs(float(seal_data.get("paid", 0)) - aff.paid_commission) < 0.01
        )

    @staticmethod
    async def verify_financial_integrity(db_session: AsyncSession, aff: AffiliateProfile) -> bool:
        """
        Military-grade Double-Entry Reconciliation Guard.
        Compares cached balance fields with live ledger aggregates.
        Suspends account and raises alert on any discrepancy.
        NOTE: Gọi bởi arq background worker mỗi 1h — KHÔNG gọi per-request.
        """
        # 1. Live sum of all earned/confirmed/paid/pending commission from ledger thêu Sếp!
        ledger_stmt = select(func.sum(CommissionLedger.commission_amount)).where(
            and_(
                CommissionLedger.affiliate_id == aff.id,
                CommissionLedger.status.in_(["PENDING", "CONFIRMED", "PAID"])
            )
        )

        # All paid withdrawals thêu Sếp!
        withdrawal_stmt = select(func.sum(WithdrawalRequest.amount_approved)).where(
            and_(
                WithdrawalRequest.affiliate_id == aff.id,
                WithdrawalRequest.status == "PAID"
            )
        )

        ledger_res = await db_session.execute(ledger_stmt)
        withdrawal_res = await db_session.execute(withdrawal_stmt)

        real_total_com = float(ledger_res.scalar() or 0.0)
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

        # 3. Verify balance seal thêu Sếp!
        if not await CtvService._verify_balance_seal_only(aff):
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
        if aff.status == "SUSPENDED":
            from litestar.exceptions import ValidationException
            raise ValidationException("Tài khoản CTV của bạn đã bị tạm khóa do vi phạm chính sách")

        # #12 Fix: Chỉ verify AES-GCM seal (O(1), zero DB) — Full reconciliation được chuyển sang arq worker (mỗi 1h) thêu Sếp!
        if not await CtvService._verify_balance_seal_only(aff):
            from litestar.exceptions import ValidationException
            raise ValidationException(
                "Cảnh báo bảo mật: Seal tài khoản không hợp lệ. Giao dịch đã bị tạm khóa!"
            )

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
                "commission_rate_bps": active_tier.commission_rate_bps if active_tier else 1500,
                "commission_rate_pct": f"{(active_tier.commission_rate_bps / 100) if active_tier else 15.0:.1f}%",
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
                    "commission_rate_bps": t.commission_rate_bps,
                    "commission_rate_pct": f"{t.commission_rate_bps / 100:.1f}%",
                    "bonus_rate_bps": t.bonus_rate_bps,
                    "min_revenue_threshold": t.min_revenue_threshold,
                }
                for t in tiers_list
            ],
            "referral_link": f"/?ctv={encrypted_token}",
        }

    @staticmethod
    async def _get_shipping_and_tax(
        db_session: AsyncSession, order: Order
    ) -> tuple[float, float]:
        """
        #7 Fix: Fetch shipping fee + tax rate trong 1 Redis pipeline (thay vì 2 query riêng).
        Returns (shipping_fee: float, tax_rate: float)
        """
        shipping_fee: Optional[float] = None
        tax_rate: Optional[float] = None

        # Fast path: Redis pipeline — 2 GET trong 1 round-trip
        try:
            from backend.services.xohi_memory import xohi_memory
            if xohi_memory._use_redis and xohi_memory.client:
                pipe = xohi_memory.client.pipeline()
                pipe.get("config:shipping:default_fee")
                pipe.get("config:shipping:tax_rate")
                results = await pipe.execute()
                if results[0]:
                    shipping_fee = float(results[0])
                if results[1]:
                    tax_rate = float(results[1])
        except Exception as e:
            logger.error(f"[CTV] Redis pipeline failed: {e}")

        # Fallback: 1 DB query duy nhất cho cả 2 giá trị
        if shipping_fee is None or tax_rate is None:
            try:
                from backend.services.xohi_memory import xohi_memory
                from backend.database.models.system import SystemSetting
                stmt = select(SystemSetting).where(SystemSetting.key == "ctv_shipping_config")
                res = await db_session.execute(stmt)
                setting = res.scalar_one_or_none()
                if setting and setting.value:
                    if shipping_fee is None and "default_fee" in setting.value:
                        shipping_fee = float(setting.value["default_fee"])
                    if tax_rate is None and "tax_rate" in setting.value:
                        tax_rate = float(setting.value["tax_rate"])
                # Write-through cache cho lần sau
                try:
                    if xohi_memory._use_redis and xohi_memory.client:
                        if shipping_fee is not None:
                            await xohi_memory.client.set(
                                "config:shipping:default_fee", str(shipping_fee)
                            )
                        if tax_rate is not None:
                            await xohi_memory.client.set(
                                "config:shipping:tax_rate", str(tax_rate)
                            )
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"[CTV] Failed to load config from DB: {e}")

        # Check order metadata for actual shipping snapshot
        order_shipping = order.order_metadata.get("shipping_fee") if order.order_metadata else None
        if order_shipping is not None and float(order_shipping) > 0.0:
            shipping_fee = float(order_shipping)

        return (shipping_fee or ShippingConfig.STANDARD_FEE, tax_rate or 0.03)


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

        # Collect all product IDs and Names for both main items and their gifts
        main_product_identifiers = set()
        gift_names = set()
        gift_product_ids = set()
        
        item_list = order.items if isinstance(order.items, list) else []
        for it in item_list:
            m_id = it.get("product_id") or it.get("id")
            if m_id:
                main_product_identifiers.add(m_id)
            
            gifts = it.get("gifts") or []
            for g in gifts:
                g_id = g.get("product_id") or g.get("id")
                if g_id:
                    gift_product_ids.add(g_id)
                g_name = g.get("name")
                if g_name:
                    gift_names.add(g_name)

        from backend.database.models.commerce import ProductBase
        # Query products by ID
        all_query_ids = list(main_product_identifiers.union(gift_product_ids))
        products_map = {}
        
        if all_query_ids:
            prod_stmt = select(ProductBase).where(ProductBase.id.in_(all_query_ids))
            prod_res = await db_session.execute(prod_stmt)
            for p in prod_res.scalars():
                products_map[p.id] = p
                products_map[p.name.lower().strip()] = p
                
        # Query gifts by Name if not found by ID
        if gift_names:
            gift_name_list = list(gift_names)
            gift_stmt = select(ProductBase).where(ProductBase.name.in_(gift_name_list))
            gift_res = await db_session.execute(gift_stmt)
            for p in gift_res.scalars():
                products_map[p.name.lower().strip()] = p
                products_map[p.id] = p

        # Resolve tier rates (bps → float cho arithmetic lịch sử, sẽ chuyển integer sau Sprint 3)
        default_tier = await CtvService._get_default_tier(db_session, tenant_id=aff.tenant_id)
        default_rate_bps = default_tier.commission_rate_bps if default_tier else 500  # 5% = 500 bps
        default_rate = default_rate_bps / 10000.0  # float chỉ dùng cho phép tính nội bộ
        default_name = default_tier.name if default_tier else "Đồng"

        tier_rate = default_rate
        tier_name = default_name
        if aff.tier:
            tier_rate = aff.tier.commission_rate_bps / 10000.0
            tier_name = aff.tier.name

        # #7 Fix: Redis pipeline — 1 round-trip cho cả shipping fee + tax rate (thay vì 2 query riêng)
        shipping_fee, tax_rate = await CtvService._get_shipping_and_tax(db_session, order)
        revenue_to_allocate = max(0.0, order.total_amount - shipping_fee)

        # Build list of items to allocate
        allocation_items = []
        total_retail_value = 0.0

        for it in item_list:
            m_id = it.get("product_id") or it.get("id")
            qty = it.get("qty") or 1
            main_prod = products_map.get(m_id) if m_id else None
            
            # If main product not in map, search by name
            if not main_prod and it.get("name"):
                main_prod = products_map.get(it.get("name").lower().strip())
                
            retail_price = main_prod.price if main_prod else (it.get("unit_price") or 0.0)
            main_total_retail = retail_price * qty
            total_retail_value += main_total_retail

            allocation_items.append({
                "type": "main",
                "id": m_id or (main_prod.id if main_prod else ""),
                "name": it.get("name") or (main_prod.name if main_prod else "Sản phẩm chính"),
                "qty": qty,
                "retail_price": retail_price,
                "total_retail": main_total_retail,
                "prod_obj": main_prod
            })

            # Check and add gifts
            gifts = it.get("gifts") or []
            for g in gifts:
                g_id = g.get("product_id") or g.get("id")
                g_qty = g.get("qty") or g.get("quantity") or 1
                g_name = g.get("name") or ""
                
                gift_prod = products_map.get(g_id) if g_id else None
                if not gift_prod and g_name:
                    gift_prod = products_map.get(g_name.lower().strip())
                
                g_retail_price = gift_prod.price if gift_prod else 0.0
                g_total_retail = g_retail_price * g_qty
                total_retail_value += g_total_retail

                allocation_items.append({
                    "type": "gift",
                    "id": g_id or (gift_prod.id if gift_prod else ""),
                    "name": g_name or (gift_prod.name if gift_prod else "Quà tặng"),
                    "qty": g_qty,
                    "retail_price": g_retail_price,
                    "total_retail": g_total_retail,
                    "prod_obj": gift_prod
                })

        # Calculate allocated revenue and commission for each item
        allocation_details = []
        total_allocated_revenue = 0.0
        total_gross_commission = 0.0

        for ai in allocation_items:
            prod_obj = ai["prod_obj"]
            
            # 1. Resolve fraction
            fraction = (ai["total_retail"] / total_retail_value) if total_retail_value > 0.0 else 0.0
            allocated_rev = revenue_to_allocate * fraction
            total_allocated_revenue += allocated_rev

            # 2. Resolve rate
            rate_source = "tier"
            if prod_obj and prod_obj.ctv_rate_override_bps is not None:
                rate = prod_obj.ctv_rate_override_bps / 10000.0  # bps → float cho arithmetic
                rate_source = "product_override"
            else:
                rate = tier_rate
                
            # Calculate gross commission
            gross_comm = allocated_rev * rate
            total_gross_commission += gross_comm

            allocation_details.append({
                "name": ai["name"],
                "type": ai["type"],
                "qty": ai["qty"],
                "retail_price": ai["retail_price"],
                "total_retail": ai["total_retail"],
                "allocated_revenue": round(allocated_rev, 2),
                "fraction": round(fraction * 100, 2),
                "rate": rate,
                "rate_source": rate_source,
                "gross_commission": round(gross_comm, 2)
            })

        # Revenue Net (Doanh thu thuần sau thuế và ship)
        tax_deduction = round(total_gross_commission * tax_rate, 2)
        commission_amount = max(0.0, round(total_gross_commission * (1.0 - tax_rate), 2))
        revenue_net = max(0.0, revenue_to_allocate)

        # Average effective rate for display compatibility
        rate = (total_gross_commission / revenue_to_allocate) if revenue_to_allocate > 0.0 else tier_rate
        rate_source = "hybrid_allocation"
        tier_snapshot = {"name": tier_name, "commission_rate_bps": round(rate * 10000), "source": rate_source}

        # Store detailed breakdown for tooltip transparency
        import json
        breakdown = {
            "order_total": order.total_amount,
            "shipping_fee": shipping_fee,
            "tax_rate": tax_rate,
            "tax_deduction": tax_deduction,
            "revenue_net": revenue_net,
            "rate_applied_bps": round(rate * 10000),
            "rate_source": rate_source,
            "commission_amount": commission_amount,
            "is_allocated": True,
            "allocation_details": allocation_details
        }
        admin_note = json.dumps(breakdown)

        # 6. Create ledger entry
        ledger = CommissionLedger(
            id=new_id(),
            affiliate_id=aff.id,
            order_id=order_id,
            order_amount=revenue_net,  # Record net revenue for clarity
            commission_amount=commission_amount,
            rate_applied_bps=round(rate * 10000),
            tier_snapshot=tier_snapshot,
            status="PENDING",
            admin_note=admin_note,
            tenant_id=aff.tenant_id or current_tenant_id.get() or "default",
        )
        ledger.integrity_token = _create_commission_seal(ledger)
        db_session.add(ledger)

        # #4 Fix: Atomic aggregate stats update — SQL UPDATE thay vì ORM read-modify-write
        # Ngăn race condition khi 2 đơn hàng của cùng CTV submit đồng thời
        new_revenue = aff.total_revenue + revenue_net
        new_commission = aff.total_commission + commission_amount
        new_orders = aff.total_orders + 1
        await db_session.execute(
            update(AffiliateProfile)
            .where(AffiliateProfile.id == aff.id)
            .values(
                total_revenue=AffiliateProfile.total_revenue + revenue_net,
                total_commission=AffiliateProfile.total_commission + commission_amount,
                total_orders=AffiliateProfile.total_orders + 1,
            )
        )
        # Sync in-memory object với giá trị mới để tạo seal chính xác
        aff.total_revenue = new_revenue
        aff.total_commission = new_commission
        aff.total_orders = new_orders
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
            # #4 Fix: Atomic rollback — func.greatest() đảm bảo không vào số âm
            await db_session.execute(
                update(AffiliateProfile)
                .where(AffiliateProfile.id == aff.id)
                .values(
                    total_revenue=func.greatest(0, AffiliateProfile.total_revenue - ledger.order_amount),
                    total_commission=func.greatest(0, AffiliateProfile.total_commission - ledger.commission_amount),
                    total_orders=func.greatest(0, AffiliateProfile.total_orders - 1),
                )
            )
            # Refresh để lấy giá trị DB mới nhất trước khi seal
            await db_session.refresh(aff)
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

        # SECURITY: Row lock (SELECT ... FOR UPDATE) to prevent financial race conditions (double spend / balance drain)
        stmt = (
            select(AffiliateProfile)
            .where(and_(AffiliateProfile.user_id == user_id, AffiliateProfile.deleted_at == None))
            .with_for_update()
        )
        res = await db_session.execute(stmt)
        aff = res.scalar_one_or_none()
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
            id=new_id(),
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
        if aff.status != "ACTIVE":
            raise ValidationException("Tài khoản CTV không ở trạng thái hoạt động")

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
        shipping_fee = await CtvService._get_actual_shipping_fee(db_session, order)
        penalty = shipping_fee * 2.0
        aff.total_commission = max(0.0, aff.total_commission - penalty)

        # 6. Mark original ledger cancelled
        ledger.status = "CANCELLED"
        
        # 7. Create penalty log ledger
        penalty_ledger = CommissionLedger(
            id=new_id(),
            affiliate_id=aff.id,
            order_id=order_id,
            order_amount=0,
            commission_amount=-penalty,
            rate_applied_bps=0,
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
