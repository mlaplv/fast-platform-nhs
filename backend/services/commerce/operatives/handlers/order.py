from __future__ import annotations
import logging
from sqlalchemy import select
from backend.database.models.commerce import Order
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.services.commerce.logic.lead_extractor import lead_extractor
from backend.services.commerce.logic.location_resolver import location_resolver
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
        
        # 1. INTENT RECOGNITION (Elite V2.5: Unit-Aware Detection)
        staff_patterns = ["cho 1 đơn", "cho đơn", "về :", "lên đơn", "gửi đơn"]
        confirmed_units = ["lọ", "hộp", "chai", "hũ", "tuýp", "combo", "bộ", "gói"]

        has_digits = any(char.isdigit() for char in msg)
        has_confirmed_unit = any(unit in msg for unit in confirmed_units)
        is_ambiguous_order = "đơn" in msg and not has_confirmed_unit

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
                delivery_info = location_resolver.resolve(order_obj.customer_address or "").shipping_days or "2-3 ngày"

                from backend.services.commerce.constants.support_config import support_cfg
                reply = (
                    f"{debug_prefix}Dạ Helen chúc mừng Anh/Chị đã đặt hàng thành công! 🌸\nHelen sẽ gửi đơn đi ngay ạ:\n"
                    f"- Mã đơn: **{order_id[-8:].upper()}**\n"
                    f"- Sản phẩm: {total_qty} {ctx.p_info.name if ctx.p_info else 'lọ/combo'}\n"
                    f"- Tổng tiền: **{formatted_price}đ** (Free ship)\n"
                    f"- Nhận hàng: **{delivery_info}**\n\n"
                    f"Anh/Chị nhớ để ý điện thoại để shipper gọi giao hàng nhé! 📞\n"
                    f"[🔍 THEO DÕI ĐƠN HÀNG]({support_cfg.app_url}/account/orders/{order_id})"
                )
                ctx.replies.append(reply)
                return True # ACTION SUCCESS -> STOP PIPELINE

        # Case B: Ambiguous "Đơn" or Partial Data
        if is_strong_intent:
            ctx.intent = SupportIntent.PURCHASE

            # Case B1: "Cho 1 đơn" -> No specific unit confirmed
            if is_ambiguous_order or (lead_data and not lead_data.items):
                logger.info(f"💡 [OrderHandler] Ambiguous 'đơn' detected. Triggering Upsell Menu.")

                base_price = int(ctx.p_info.price) if ctx.p_info and ctx.p_info.price else 249000
                formatted_base = "{:,.0f}".format(base_price).replace(",", ".")
                formatted_combo2 = "{:,.0f}".format(base_price * 2).replace(",", ".")

                offer_reply = (
                    f"{debug_prefix}Dạ Helen đã nhận thông tin chốt đơn của mình tại địa chỉ trên ạ! 🌸\n\n"
                    "Để Helen lên đơn chính xác nhất, mình muốn lấy liệu trình nào cho tiết kiệm ạ?\n"
                    f"- **1 Lọ:** {formatted_base}đ (Dùng thử)\n"
                    f"- **Combo 2 Tặng 1 (3 Lọ):** {formatted_combo2}đ (Tiết kiệm {formatted_base}đ - **🔥 Bán chạy nhất**)\n"
                    "- **Combo 4 Tặng 1 (5 Lọ):** Ưu đãi lớn nhất cho liệu trình chuyên sâu.\n\n"
                    "Anh/Chị cho em xin **số lượng** để em gửi hàng đi ngay nhé!"
                )
                ctx.replies.append(offer_reply)
                return True

            # Case B2: Missing Phone or Address but intent is clear
            if lead_data and (not lead_data.customer_phone or not lead_data.customer_address):
                if not lead_data.customer_phone:
                    reply = f"{debug_prefix}Dạ Helen đã thấy địa chỉ rồi ạ. Anh/Chị cho em xin thêm **Số Điện Thoại** để shipper liên hệ giao hàng nhé! 🌸"
                else:
                    reply = f"{debug_prefix}Dạ Helen đã có SĐT rồi ạ. Anh/Chị cho em xin **Địa chỉ cụ thể** để em gửi hàng về ngay nhé! 🌸"
                ctx.replies.append(reply)
                return True

        return False # Fallthrough # Fallthrough to next specialists (Greeting/Consultant)

    def _calculate_delivery_time(self, address: str, shipping_days: str | None = None) -> str:
        """Heuristic Shipping Estimator (Standardized Logic)."""
        if shipping_days: return shipping_days
        return location_resolver.resolve(address).shipping_days or "2-3 ngày"
