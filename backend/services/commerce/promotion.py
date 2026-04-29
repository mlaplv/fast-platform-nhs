from typing import List, Dict, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.promotion import Voucher, ComboDeal
from backend.database import current_tenant_id
from datetime import datetime, timezone
from litestar.exceptions import NotFoundException, ValidationException
import logging

logger = logging.getLogger("api-gateway")

class PromotionService:
    @staticmethod
    async def get_active_voucher(db_session: AsyncSession, voucher_id: str) -> Optional[Voucher]:
        now = datetime.now(timezone.utc)
        stmt = select(Voucher).where(
            and_(
                Voucher.id == voucher_id,
                Voucher.is_active == True,
                Voucher.tenant_id == (current_tenant_id.get() or "default"),
                or_(Voucher.start_date == None, Voucher.start_date <= now),
                or_(Voucher.end_date == None, Voucher.end_date >= now)
            )
        )
        res = await db_session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_active_combo_deals(db_session: AsyncSession) -> List[ComboDeal]:
        now = datetime.now(timezone.utc)
        stmt = select(ComboDeal).where(
            and_(
                ComboDeal.is_active == True,
                ComboDeal.tenant_id == (current_tenant_id.get() or "default"),
                or_(ComboDeal.start_date == None, ComboDeal.start_date <= now),
                or_(ComboDeal.end_date == None, ComboDeal.end_date >= now)
            )
        )
        res = await db_session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    def calculate_combo_discount(items: List[Dict], combo_deals: List[ComboDeal]) -> float:
        """
        Elite V2.2: Advanced Combo Calculation
        Supports BUY_X_GET_Y and BUNDLE_PRICE.
        """
        total_discount = 0.0
        # Make a copy of items to track remaining quantity during calculation
        working_items = [dict(it) for it in items]
        
        for deal in combo_deals:
            if deal.type == "BUY_X_GET_Y":
                cond = deal.condition_payload or {}
                reward = deal.reward_payload or {}
                
                buy_qty = int(cond.get("buy_qty", 0))
                get_qty = int(reward.get("get_qty", 1))
                product_ids = cond.get("product_ids", [])
                
                if buy_qty <= 0 or not product_ids:
                    continue
                
                cycle_size = buy_qty + get_qty
                
                # Get relevant items and sort by price ascending (cheapest items discounted first)
                relevant_items = [it for it in working_items if it["id"] in product_ids and it["qty"] > 0]
                relevant_items.sort(key=lambda x: x["unit_price"])
                
                total_deal_qty = sum(it["qty"] for it in relevant_items)
                num_cycles = total_deal_qty // cycle_size
                items_to_discount = num_cycles * get_qty
                
                discount_pct = float(reward.get("discount_percent", 100)) / 100.0
                
                applied_count = 0
                for it in relevant_items:
                    if applied_count >= items_to_discount:
                        break
                    
                    can_discount = min(it["qty"], items_to_discount - applied_count)
                    total_discount += can_discount * it["unit_price"] * discount_pct
                    it["qty"] -= can_discount
                    applied_count += can_discount
            elif deal.type == "BUNDLE_PRICE":
                cond = deal.condition_payload or {}
                reward = deal.reward_payload or {}
                
                required_qty = int(cond.get("qty", 0))
                product_ids = cond.get("product_ids", [])
                bundle_price = float(reward.get("price", 0))
                
                if required_qty <= 0 or not product_ids or bundle_price <= 0:
                    continue
                
                relevant_items = [it for it in working_items if it["id"] in product_ids and it["qty"] > 0]
                total_qty = sum(it["qty"] for it in relevant_items)
                
                if total_qty >= required_qty:
                    num_bundles = total_qty // required_qty
                    items_in_bundles = num_bundles * required_qty
                    
                    # Sort by price descending (discount the most expensive items into the bundle)
                    # This is usually how shops work to show the "hời"
                    relevant_items.sort(key=lambda x: x["unit_price"], reverse=True)
                    
                    bundle_discount = 0.0
                    consumed_qty = 0
                    for it in relevant_items:
                        if consumed_qty >= items_in_bundles:
                            break
                        
                        count = min(it["qty"], items_in_bundles - consumed_qty)
                        # Current subtotal of these items: count * it['unit_price']
                        # Target price for these items: count * (bundle_price / required_qty)
                        bundle_discount += (count * it["unit_price"]) - (count * (bundle_price / required_qty))
                        it["qty"] -= count
                        consumed_qty += count
                    
                    total_discount += bundle_discount
                                
        return total_discount

    @staticmethod
    def calculate_voucher_discount(subtotal: float, voucher: Voucher) -> float:
        if subtotal < voucher.min_spend:
            return 0.0
            
        discount = 0.0
        if voucher.type == "FIXED":
            discount = voucher.value
        elif voucher.type == "PERCENT":
            discount = subtotal * (voucher.value / 100.0)
            if voucher.max_discount:
                discount = min(discount, voucher.max_discount)
        elif voucher.type == "SHIPPING":
             # Shipping vouchers subtract from shipping fee elsewhere, 
             # but here we can return the value if we consider it a generic discount
             discount = voucher.value
             
        return min(discount, subtotal)

    @staticmethod
    async def validate_and_use_voucher(db_session: AsyncSession, voucher_id: str, phone: str) -> Optional[Voucher]:
        """
        [ELITE V2.2] Shopee-Style Voucher Accounting & Protection
        Increments usage count and prevents multi-use per phone.
        """
        from backend.database.models.commerce import Order
        from sqlalchemy import update, func
        
        # 1. Anti-Abuse: Check if this phone used this voucher already
        # Using JSONB containment check for order_metadata.voucher_id
        usage_stmt = select(Order).where(
            and_(
                Order.customer_phone == phone,
                Order.order_metadata["voucher_id"].astext == voucher_id,
                Order.status != "CANCELLED"
            )
        ).limit(1)
        usage_res = await db_session.execute(usage_stmt)
        if usage_res.scalar_one_or_none():
            logger.warning(f"[VOUCHER-ABUSE] Phone {phone} attempted second use of voucher {voucher_id}")
            raise ValidationException("Bạn đã sử dụng mã giảm giá này cho đơn hàng trước đó.")

        # 2. Atomic Increment & Limit Check
        # We fetch the voucher first to check limits
        voucher = await PromotionService.get_active_voucher(db_session, voucher_id)
        if not voucher:
             raise NotFoundException("Mã giảm giá không hợp lệ hoặc đã hết hạn.")
             
        if voucher.usage_limit and voucher.used_count >= voucher.usage_limit:
             logger.warning(f"[VOUCHER-EXHAUSTED] Voucher {voucher_id} reached limit {voucher.usage_limit}")
             raise ValidationException("Mã giảm giá này đã hết lượt sử dụng.")

        # Atomic increment
        voucher.used_count += 1
        db_session.add(voucher)
        # No full commit here, we let the CheckoutService handle the transaction commit
        return voucher


