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
        # Any mention of price, ingredients, or address should SILENCE the greeting
        # to ensure the Consultant/L0 response is clean and specialized.
        knowledge_keywords = [
            "giá", "bao nhiêu", "nhiêu", "thành phần", "công dụng", "địa chỉ", "ở đâu", 
            "nhà thuốc", "địa điểm", "chi nhánh", "như thế nào", "sử dụng", 
            "liệu trình", "hiệu quả", "an toàn", "?"
        ]
        has_knowledge_intent = any(kw in msg for kw in knowledge_keywords)
        buying_intent = any(kw in msg for kw in [
            "mua", "đặt", "lấy", "ship", "giao",
            # Elite V2.5: Direct order-intake patterns (e.g. "Cho 1 đơn về : ...")  
            "cho 1 đơn", "cho đơn", "lên đơn", "chốt đơn", "đơn về",
            "về :", "về:",  # Address separator pattern
        ])
        # Thêm: nếu msg có số điện thoại format (10 digits) hoặc có "/" (địa chỉ), xem là order intent
        has_phone_pattern = sum(1 for c in msg if c.isdigit()) >= 9
        has_address_slash = "/" in msg

        # ELITE DISCIPLINE: Silence Zone 1 if Zone 2 (Knowledge) or Zone 3 (Order) is detected.
        if has_knowledge_intent or buying_intent or has_phone_pattern or has_address_slash:
            logger.debug(f"🔇 [Greeting Silenced] Knowledge/Order intent detected: {msg}")
            return False

        if (is_first_msg or has_greeting) and len(msg) < 15:
            # Simple pure greeting ("Chào", "Hi", "Alo") — Terminate pipeline here
            prefix = "[z1] Dạ Helen chào Anh/Chị! 🌸 "
            if ctx.dna.segment == "VIP":
                prefix = f"Dạ Helen thân chào khách quý! 🌟 Rất vui được gặp lại mình ạ. "
            elif ctx.dna.segment == "REGULAR":
                prefix = f"Dạ Helen chào Anh/Chị, em rất vui được gặp lại mình! "

            if ctx.p_info:
                prefix += f"Em rất hân hạnh được hỗ trợ mình về liệu trình **{ctx.p_info.name}** bên em ạ. "

            # Elite V2.5 Fix: ONLY append when we're sure we're terminating (return True)
            # Previously: append() was called before the len check → [z1] leaked into Order replies
            ctx.replies.append(prefix)
            ctx.replies.append("Anh/Chị cần em hỗ trợ hay tư vấn thông tin gì không ạ?")
            logger.info(f"✨ [Greeting Heuristic] Responding to greeting: {msg}")
            return True  # TERMINATE: Pure greeting consumed.

        return False  # Fall-through to Consultant/Order for complex queries
