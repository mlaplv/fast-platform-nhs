import logging
import unicodedata
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext

logger = logging.getLogger("api-gateway")

class GreetingHandler(BaseHandler):
    """
    ZONE 1: Persona Greeting Specialist.
    Priority: Build rapport and set the Vibe (WARM/PROFESSIONAL).
    """

    async def handle(self, ctx: SupportContext) -> bool:
        """ZONE 1: Standard Greeting with Heuristic Reflex (AI-Zero Quota)."""
        # Elite V2.2: NFKC Normalization for accurate Vietnamese string matching
        raw_msg = ctx.request.message.lower().strip()
        msg = unicodedata.normalize("NFKC", raw_msg)
        is_first_msg = not ctx.history_text
        keywords = ["chào", "hi", "hello", "dạ", "alo", "helen", "ơi"]
        has_greeting = any(kw in msg for kw in keywords)

        # Elite V2.2: Intent Analytics (Knowledge-Aware Protection)
        knowledge_keywords = [
            "giá", "bao nhiêu", "nhiêu", "thành phần", "công dụng", "địa chỉ", "ở đâu",
            "nhà thuốc", "địa điểm", "chi nhánh", "như thế nào", "sử dụng",
            "liệu trình", "hiệu quả", "an toàn", "?"
        ]
        has_knowledge_intent = any(kw in msg for kw in knowledge_keywords)
        buying_intent = any(kw in msg for kw in [
            "mua", "đặt", "lấy", "ship", "giao",
            "cho 1 đơn", "cho đơn", "lên đơn", "chốt đơn", "đơn về",
            "về :", "về:",
        ])
        has_phone_pattern = sum(1 for c in msg if c.isdigit()) >= 9
        has_address_slash = "/" in msg

        # ELITE DISCIPLINE: Silence Zone 1 if Zone 2 (Knowledge) or Zone 3 (Order) is detected.
        if (is_first_msg or has_greeting) and len(msg) < 15:
            # Simple pure greeting ("Chào", "Hi", "Alo") — Terminate pipeline here
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

            if ctx.dna.segment == "VIP":
                prefix = f"{debug_prefix}Dạ Helen thân chào khách quý! 🌟 Chúc mình một {time_greet} ạ. Rất vui được gặp lại mình! "
            elif ctx.dna.segment == "REGULAR":
                prefix = f"{debug_prefix}Dạ Helen chào Anh/Chị, em rất vui được gặp lại mình trong {time_greet} hôm nay! "
            else:
                prefix = f"{debug_prefix}Dạ Helen chào Anh/Chị! Chúc mình một {time_greet} nhé. 🌸 "

            if ctx.p_info:
                prefix += f"Helen rất hân hạnh được hỗ trợ mình về liệu trình **{ctx.p_info.name}** ạ. "

            # Elite V2.5 Fix: ONLY append when we're sure we're terminating (return True)
            ctx.replies.append(prefix)
            ctx.replies.append("Anh/Chị cần Helen tư vấn thông tin gì hay muốn lên đơn trải nghiệm luôn không ạ?")
            logger.info(f"✨ [Greeting Heuristic] Responding to greeting: {msg}")
            return True  # TERMINATE: Pure greeting consumed.

        return False  # Fall-through to Consultant/Order for complex queries
