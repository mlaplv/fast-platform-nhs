import logging
import unicodedata
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext

logger = logging.getLogger("api-gateway")

class GreetingHandler(BaseHandler):
    """
    ZONE 1: Persona Greeting Specialist (Micsmo Elite V2.6).
    Priority: Build rapport, set Vibe, and plant a sales hook.
    """

    async def handle(self, ctx: SupportContext) -> bool:
        """ZONE 1: Smart Greeting with Sales Hook (AI-Zero Quota)."""
        # Elite V2.6: NFKC Normalization for accurate Vietnamese string matching
        raw_msg = ctx.request.message.lower().strip()
        msg = unicodedata.normalize("NFKC", raw_msg)
        is_first_msg = not ctx.history_text
        keywords = ["chào", "hi", "hello", "dạ", "alo", "helen", "ơi", "shop ơi", "ad ơi"]
        has_greeting = any(kw in msg for kw in keywords)

        # Elite V2.6: Expanded threshold (25 chars) to catch "chào shop tư vấn giúp"
        # Elite V5.6: NEVER consume greeting if cart exists (Let Consultant report cart)
        if (is_first_msg or has_greeting) and len(msg) < 25 and not ctx.request.cart_items:
            import os
            from datetime import datetime
            debug_prefix = "[z1] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""

            # Elite V2.5: Time-aware greetings
            hour = datetime.now().hour
            if 5 <= hour < 11:
                time_greet = "buổi sáng tốt lành"
            elif 11 <= hour < 14:
                time_greet = "buổi trưa vui vẻ"
            elif 14 <= hour < 18:
                time_greet = "buổi chiều thuận lợi"
            else:
                time_greet = "buổi tối ấm áp"

            # Elite V3.0: Identify Name
            c_name = ctx.dna.customer_name or ctx.request.customer_name or "Quý khách"
            if c_name == "Khách ẩn danh": c_name = "Quý khách"
            
            pts_msg = ""
            if ctx.dna.available_points > 0:
                money = "{:,.0f}".format(ctx.dna.available_points * ctx.dna.point_value_vnd).replace(",", ".")
                pts_msg = f" Hiện mình đang có **{ctx.dna.available_points} điểm** tích lũy đặc quyền (~{money}đ) đó ạ. "

            if ctx.dna.segment == "VIP":
                prefix = f"{debug_prefix}Dạ Helen thân chào {c_name} - khách quý của Micsmo! 🌟 Chúc mình một {time_greet} ạ. Thật tuyệt vời khi được gặp lại mình!{pts_msg}"
            elif ctx.dna.segment == "REGULAR":
                prefix = f"{debug_prefix}Dạ Helen chào {c_name}, em rất vui được gặp lại mình trong {time_greet} hôm nay!{pts_msg}"
            else:
                prefix = f"{debug_prefix}Dạ Helen chào {c_name}! Chúc mình một {time_greet} nhé. 🌸 "

            # Elite V5.9: Context-aware Sales Assassin Hook
            if ctx.p_info:
                # Đang ở trang sản phẩm cụ thể - Chốt FOMO & Ưu đãi
                price_tag = f" (**{ctx.p_info.price_display}**)" if ctx.p_info.price_display else ""
                prefix += f"Em thấy mình đang quan tâm đến siêu phẩm **{ctx.p_info.name}**{price_tag} - đây hiện đang là dòng 'best-seller' thăng hạng nhan sắc nhà Micsmo đó ạ! ✨ "
                
                # Add a punchy Sales Hook
                ctx.replies.append(prefix)
                ctx.replies.append(
                    "Hiện tại Helen đang có ưu đãi đặc quyền **Mua 2 Tặng 1 (Combo 2+1)** hoặc **Voucher giảm sâu** dành riêng cho mình khi chốt đơn tại đây. 🌸 "
                    "Anh/Chị có muốn Helen kiểm tra mức giá tốt nhất sau khi áp mã cho mình không ạ?"
                )
            else:
                # Ở Homepage / Category / Cart — Smart Hook
                ctx.replies.append(prefix)
                ctx.replies.append(
                    "Bên Micsmo đang có rất nhiều siêu phẩm chăm sóc da và chương trình ưu đãi đặc quyền lên đến 50% dành cho mình đó ạ! ✨ "
                    "Anh/Chị đang quan tâm dòng sản phẩm nào (Trắng da, Trị nám, Chống lão hóa...) để Helen gửi mình mã giảm giá hời nhất nhé! 🌸"
                )

            return True  # TERMINATE: Pure greeting consumed.

        return False  # Fall-through to Consultant/Order for complex queries

