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
        """ZONE 3: Order Closing. Heuristic guard before LLM extraction."""
        msg = ctx.request.message.lower().strip()
        
        # 🚀 Elite V2.2: Tighten Heuristics (Elite Discipline)
        # We REMOVE noisy keywords like 'address' or 'name' which should trigger Consultant/L0.
        order_keywords = [
            "mua", "đặt", "lấy", "ship", "giao", "lên đơn", "check đơn",
            "1 lọ", "2 lọ", "3 lọ", "combo", "đặt hàng", "mua ngay"
        ]
        potential_order = any(kw in msg for kw in order_keywords)
        has_digits = any(char.isdigit() for char in msg)
        # Detect clear order signals: message has both digits (phone) AND address-like patterns
        has_address_signal = any(kw in msg for kw in ["đường", "phố", "quận", "huyện", "phường", "xã", "tỉnh", "tp", "thành phố", "ngõ", "ngách", "/"])
        
        if not potential_order and not has_digits and not has_address_signal and len(msg) < 15:
            return False

        # 1. RUN LEAD EXTRACTOR (Core Engine)
        try:
            lead_data = await lead_extractor.extract_and_convert(
                ctx.db, ctx.request.message, ctx.session_id, current_product_slug=ctx.request.product_slug
            )
            ctx.lead_data = lead_data
        except Exception as le:
            logger.error(f"[OrderHandler] Lead extraction failed: {le}")
            return False
        
        # 2. SUCCESS PATH: Order was created successfully
        if lead_data and lead_data.processed_order_id:
            ctx.processed_order_id = lead_data.processed_order_id
            ctx.intent = SupportIntent.PURCHASE
            
            order_id = str(lead_data.processed_order_id)
            stmt = select(Order).where(Order.id == order_id)
            order_obj = (await ctx.db.execute(stmt)).scalar_one_or_none()
            
            if order_obj:
                total_qty: int = 0
                if isinstance(order_obj.items, list):
                    for it in order_obj.items:
                        if isinstance(it, dict):
                            # Elite V2.2: Safe extraction from JSONB items
                            qty_val = it.get("quantity", 1)
                            total_qty += int(qty_val) if isinstance(qty_val, (int, str)) else 1
                
                formatted_price = "{:,.0f}".format(float(order_obj.total_amount or 0)).replace(",", ".")
                delivery_info = self._calculate_delivery_time(order_obj.customer_address or "", getattr(lead_data, "shipping_days", None))
                
                from backend.services.commerce.constants.support_config import support_cfg
                reply = (
                    f"Dạ Helen xin cảm ơn quý khách! 🌸 [z3]\nĐơn hàng thành công:\n- Mã đơn: **{order_id[-8:].upper()}**\n"
                    f"- Số sản phẩm: {total_qty} lọ/combo\n- Tổng tiền: **{formatted_price}đ** (đã free ship)\n"
                    f"- Nhận hàng: **{delivery_info}**\n\n"
                    f"[🔍 KIỂM TRA ĐƠN HÀNG]({support_cfg.app_url}/account/orders/{order_id})"
                )
                ctx.replies.append(reply)
                return True # ACTION-FIRST: Stop the pipeline on purchase success.
        
        # 3. SEMI-SUCCESS: Lead identified but Order not created (Missing info)
        # If we have BOTH phone and address, we consider this an Action-Locked state.
        # We terminate to provide a focused confirmation/request.
        if lead_data and lead_data.customer_phone and lead_data.customer_address:
            ctx.intent = SupportIntent.PURCHASE
            # Elite V2.2 Fix: Never enter a state with empty replies if consuming the pipeline
            p_name = ctx.p_info.name if ctx.p_info else "sản phẩm"
            reply = (
                f"Dạ Helen đã ghi nhận SĐT **{lead_data.customer_phone}** và địa chỉ của mình tại **{lead_data.customer_address}** ạ. [z3-lead]\n\n"
                f"Anh/Chị muốn đặt ngay liệu trình **{p_name}** này để em lên đơn và gửi đi cho mình luôn nhé? 🌸"
            )
            ctx.replies.append(reply)
            return True
            
        return False

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
