from __future__ import annotations
import logging
from sqlalchemy import select
from backend.database.models.commerce import Order
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.services.commerce.logic.lead_extractor import lead_extractor
from backend.schemas.support import SupportIntent

logger = logging.getLogger("api-gateway")

class OrderHandler(BaseHandler):
    """
    ZONE 3: The Order Closer and Status Specialist.
    Priority: Identify purchase intent and extract leads.
    """
    
    async def handle(self, ctx: SupportContext) -> bool:
        """ZONE 3: Order Closing. Refined Elite V2.5 Architecture."""
        msg = ctx.request.message.lower().strip()
        
        # 1. INTENT RECOGNITION (Heuristic)
        staff_patterns = ["cho 1 đơn", "cho đơn", "về :", "lên đơn", "gửi đơn"]
        has_digits = any(char.isdigit() for char in msg)
        potential_keywords = ["mua", "đặt", "lấy", "ship", "giao", "ok", "chốt", "đơn", "lên đơn", "chốt đơn"]
        
        is_staff_order = any(sp in msg for sp in staff_patterns) and has_digits
        has_buying_intent = any(kw in msg for kw in potential_keywords)
        is_strong_intent = has_digits and (has_buying_intent or is_staff_order)

        # 🚀 2. ATOMIC EXTRACTION (Execute ONLY ONCE)
        lead_data = None
        if is_strong_intent or is_staff_order:
            try:
                lead_data = await lead_extractor.extract_and_convert(
                    ctx.db, ctx.request.message, ctx.session_id, current_product_slug=ctx.request.product_slug
                )
                ctx.lead_data = lead_data
            except Exception as e:
                logger.error(f"[OrderHandler] Atomic extraction failed: {e}")

        # 🚀 3. DECISION ENGINE (The Lockdown)
        import os
        debug_prefix = "[z3] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""

        # Case A: Success (Order Created)
        if lead_data and lead_data.processed_order_id:
            ctx.processed_order_id = lead_data.processed_order_id
            ctx.intent = SupportIntent.PURCHASE
            
            order_id = str(lead_data.processed_order_id)
            stmt = select(Order).where(Order.id == order_id)
            order_obj = (await ctx.db.execute(stmt)).scalar_one_or_none()
            
            if order_obj:
                total_qty = 0
                if isinstance(order_obj.items, list):
                    for it in order_obj.items:
                        if isinstance(it, dict):
                            qty_val = it.get("quantity", 1)
                            total_qty += int(qty_val) if isinstance(qty_val, (int, str)) else 1
                
                formatted_price = "{:,.0f}".format(float(order_obj.total_amount or 0)).replace(",", ".")
                delivery_info = self._calculate_delivery_time(order_obj.customer_address or "", getattr(lead_data, "shipping_days", None))
                
                from backend.services.commerce.constants.support_config import support_cfg
                reply = (
                    f"{debug_prefix}Dạ Helen xin cảm ơn quý khách! 🌸\nĐơn hàng thành công:\n- Mã đơn: **{order_id[-8:].upper()}**\n"
                    f"- Số sản phẩm: {total_qty} lọ/combo\n- Tổng tiền: **{formatted_price}đ** (đã free ship)\n"
                    f"- Nhận hàng: **{delivery_info}**\n\n"
                    f"[🔍 KIỂM TRA ĐƠN HÀNG]({support_cfg.app_url}/account/orders/{order_id})"
                )
                ctx.replies.append(reply)
                return True # ACTION SUCCESS -> STOP PIPELINE

        # Case B: Partial Data or Nuclear Intent (Bypass AI uncertainty)
        if is_staff_order or (lead_data and (lead_data.customer_phone or lead_data.customer_address)):
            ctx.intent = SupportIntent.PURCHASE
            # 2. DECISION ENGINE (Elite V2.5 / V4.0 Upsell Edition)
            if is_staff_order and lead_data and not lead_data.items:
                # Case: Staff says "Cho 1 đơn" or "Cho về" but no "lọ/combo" defined.
                # Trigger Consultative Menu instead of failing or creating empty order.
                logger.info(f"💡 [OrderHandler] Ambiguous order detected. Triggering Upsell Menu for: {msg}")
                
                # Retrieve price from recent Turn or Config (Fallback to 249k)
                offer_reply = (
                    f"{debug_prefix}Dạ Helen đã nhận diện yêu cầu lên đơn của Sếp! 🌸\n\n"
                    "Để tối ưu hiệu quả và tiết kiệm nhất, Sếp muốn chốt theo liệu trình nào ạ?\n"
                    "- **1 Lọ:** 249.000đ (Dùng thử)\n"
                    "- **Combo 2 Tặng 1 (3 Lọ):** 498.000đ (Tiết kiệm 249k - **🔥 Bán chạy nhất**)\n"
                    "- **Combo 4 Tặng 1 (5 Lọ):** Ưu đãi lớn nhất cho liệu trình chuyên sâu.\n\n"
                    "Sếp cho em xin **số lượng** để em hoàn tất lên đơn ngay nhé!"
                )
                
                ctx.replies.append(offer_reply)
                return True

            if lead_data and lead_data.customer_phone and lead_data.customer_address:
                p_name = ctx.p_info.name if ctx.p_info else "sản phẩm"
                reply = (
                    f"{debug_prefix}Dạ Helen đã ghi nhận SĐT **{lead_data.customer_phone}** và địa chỉ của mình tại **{lead_data.customer_address}** ạ.\n\n"
                    f"Anh/Chị muốn đặt ngay liệu trình **{p_name}** này để em lên đơn và gửi đi cho mình luôn nhé? 🌸"
                )
            else:
                # Force feedback if it's a staff command or clear intent but extraction was incomplete
                reply = f"{debug_prefix}Helen đã nhận diện yêu cầu lên đơn của Sếp. Tuy nhiên em cần thêm SĐT và Địa chỉ chi tiết để hoàn tất. Sếp kiểm tra lại giúp em nhé! 🌸"
            
            ctx.replies.append(reply)
            return True # BLOCK CONSULTANT!

        return False # Fallthrough to next specialists (Greeting/Consultant)

    def _calculate_delivery_time(self, address: str, shipping_days: str | None = None) -> str:
        """Heuristic Shipping Estimator (Standardized Logic)."""
        if shipping_days: return shipping_days
        if not address: return "2-3 ngày"
        addr = address.lower()
        hcm_keys = ["hồ chí minh", "tp.hcm", "hcm", "sài gòn", "quận 1", "quận 3", "quận 5", "quận 10", "tân bình", "bình thạnh"]
        if any(key in addr for key in hcm_keys): return "1 ngày"
        south_keys = ["bình dương", "đồng nai", "long an", "vũng tàu", "cần thơ"]
        if any(key in addr for key in south_keys): return "1-2 ngày"
        return "3-5 ngày"
