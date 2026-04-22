import logging
from typing import List, Dict, Optional, Union
from backend.schemas.pricing import PricingBreakdown, PricingItem, PricingInputItem
from backend.database.models.promotion import Voucher, ComboDeal
from backend.services.commerce.promotion import PromotionService

logger = logging.getLogger("api-gateway")

class PricingEngine:
    """
    Elite V2.2: The Unified Pricing Engine (Martial Combo Protocol).
    Centralizes all billing logic to ensure 100% consistency between 
    AI Support (Helen), Checkout, and Backend Services.
    """

    @staticmethod
    def calculate(
        items: List[PricingInputItem],
        vouchers: Optional[List[Voucher]] = None,
        combo_deals: Optional[List[ComboDeal]] = None,
        points_to_redeem: int = 0,
        available_points: int = 0,
        point_value_vnd: float = 1000.0,
        base_shipping_fee: float = 30000.0
    ) -> PricingBreakdown:
        """
        Executes the full billing pipeline:
        1. Subtotal calculation
        2. Combo discount (Priority 1)
        3. Voucher discount (Priority 2)
        4. Point discount (Priority 3 - Strict 1% Cap)
        5. Shipping fee calculation
        6. Final Payable & Points Earned
        """
        breakdown = PricingBreakdown()
        vouchers = vouchers or []
        combo_deals = combo_deals or []

        # --- 1. Subtotal ---
        subtotal = 0.0
        pricing_items = []
        for it in items:
            p_id = it.product_id
            name = it.name
            qty = it.quantity
            price = it.unit_price
            total = qty * price
            
            subtotal += total
            pricing_items.append(PricingItem(
                product_id=p_id,
                name=name,
                quantity=qty,
                unit_price=price,
                total_price=total
            ))
        
        breakdown.items = pricing_items
        breakdown.subtotal = subtotal

        # --- 2. Combo Discount ---
        # Note: calculate_combo_discount modifies the 'qty' in the list it receives to avoid double-dipping,
        # so we pass a simplified list of dicts for it to work with.
        working_items = [{"id": it.product_id, "qty": it.quantity, "unit_price": it.unit_price} for it in pricing_items]
        combo_discount = PromotionService.calculate_combo_discount(working_items, combo_deals)
        breakdown.combo_discount = combo_discount
        breakdown.applied_combo_ids = [str(c.id) for c in combo_deals]

        # --- 3. Voucher Discount ---
        total_voucher_discount = 0.0
        shipping_voucher_discount = 0.0
        
        # Amount after combo, which is the base for value vouchers
        amount_after_combo = max(0, subtotal - combo_discount)
        
        for v in vouchers:
            if v.type == "SHIPPING":
                # Shipping vouchers are handled separately at the end
                shipping_voucher_discount += PromotionService.calculate_voucher_discount(amount_after_combo, v)
            else:
                # Value vouchers (FIXED/PERCENT)
                total_voucher_discount += PromotionService.calculate_voucher_discount(amount_after_combo, v)
            
            breakdown.applied_voucher_ids.append(str(v.id))
        
        breakdown.voucher_discount = total_voucher_discount

        # --- 4. Point Discount (The Elite V2.2 Cap Rule) ---
        # Sếp Rule: Max 1% of the amount AFTER combo and vouchers
        amount_after_discounts = max(0, subtotal - combo_discount - total_voucher_discount)
        max_allowed_vnd = amount_after_discounts * 0.01
        
        # Effective points to use
        effective_points = min(points_to_redeem, available_points)
        point_discount_vnd = min(max_allowed_vnd, effective_points * point_value_vnd)
        
        breakdown.max_point_discount_allowed = max_allowed_vnd
        breakdown.points_redeemed = int(point_discount_vnd // point_value_vnd)
        breakdown.point_discount_amount = point_discount_vnd

        # --- 5. Shipping Fee ---
        breakdown.base_shipping_fee = base_shipping_fee
        breakdown.shipping_discount = min(base_shipping_fee, shipping_voucher_discount)
        breakdown.final_shipping_fee = max(0, base_shipping_fee - breakdown.shipping_discount)

        # --- 6. Final Calculation ---
        breakdown.final_payable = max(0, amount_after_discounts - breakdown.point_discount_amount + breakdown.final_shipping_fee)
        
        # Points to earn: 1 point per 100k VND
        breakdown.points_to_earn = int(breakdown.final_payable // 100000)

        return breakdown
