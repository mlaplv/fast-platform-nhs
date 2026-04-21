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
        if (is_first_msg or has_greeting) and len(msg) < 25:
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

            # Elite V2.6: Context-aware greeting hook
            if ctx.p_info:
                # Đang ở trang sản phẩm cụ thể
                prefix += f"Helen rất hân hạnh được hỗ trợ mình về sản phẩm **{ctx.p_info.name}** ạ. "
                ctx.replies.append(prefix)
                ctx.replies.append("Anh/Chị cần Helen tư vấn thông tin gì hay muốn lên đơn trải nghiệm luôn không ạ?")
            else:
                # Ở Homepage / Category / Cart — Smart Hook
                ctx.replies.append(prefix)
                ctx.replies.append(
                    "Bên Micsmo đang có nhiều sản phẩm chăm sóc da hot và chương trình ưu đãi hấp dẫn lắm ạ! "
                    "Anh/Chị muốn Helen tư vấn dòng sản phẩm nào cho mình, hay tìm hiểu về ưu đãi đang chạy không ạ? 🌸"
                )

            logger.info(f"✨ [Greeting Heuristic] Responding to greeting: {msg}")
            return True  # TERMINATE: Pure greeting consumed.

        return False  # Fall-through to Consultant/Order for complex queries

