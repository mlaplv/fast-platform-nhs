from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext

class GreetingHandler(BaseHandler):
    """
    ZONE 1: Persona Greeting Specialist.
    Priority: Build rapport and set the Vibe (WARM/PROFESSIONAL).
    """

    async def handle(self, ctx: SupportContext) -> bool:
        """ZONE 1: Standard Greeting with Early Exit Strategy."""
        msg = ctx.request.message.lower().strip()
        is_first_msg = not ctx.history_text
        keywords = ["chào", "hi", "hello", "dạ", "alo", "helen"]
        has_greeting = any(kw in msg for kw in keywords)
        
        # Elite V2.2: Intent Analytics - Determine if further specialists are needed
        # We search for clues of price/buying interest or KNOWLEDGE queries to avoid Early Exit.
        buying_intent = any(kw in msg for kw in [
            "giá", "bao nhiêu", "nhiêu", "mua", "đặt", "ship", "lấy", "tư vấn",
            "thành phần", "công dụng", "tác dụng", "liệu trình", "cách dùng", "hiệu quả", "an toàn", "sử dụng"
        ])
        # Elite V2.2 Fix: Detect pure knowledge questions — these should bypass greeting prefix
        # to avoid polluting the Consultant's response with an irrelevant welcome message.
        is_question = any(kw in msg for kw in [
            "?", " gì", " ở đâu", " bất", " bao nhiêu", " như thế nào",
            "địa chỉ", "thành phần", "công dụng", "giá", "cách", "liệu trình", "chính sách"
        ])
        
        if (is_first_msg or has_greeting) and not is_question:
            prefix = "[z1] Dạ Helen chào Anh/Chị! 🌸 "
            if ctx.dna.segment == "VIP":
                prefix = f"Dạ Helen thân chào khách quý! 🌟 Rất vui được gặp lại mình ạ. "
            elif ctx.dna.segment == "REGULAR":
                prefix = f"Dạ Helen chào Anh/Chị, em rất vui được gặp lại mình! "
            
            if ctx.p_info:
                prefix += f"Em rất hân hạnh được hỗ trợ mình về liệu trình **{ctx.p_info.name}** bên em ạ. "
            
            # 🚀 Elite V2.2: Social Proof Indicator
            if ctx.active_visitors > 2:
                prefix += f"Hiện đang có hơn {ctx.active_visitors} khách khác cũng đang quan tâm tới sản phẩm này, em sẽ hỗ trợ mình thật nhanh nhé! 🔥 "
            elif ctx.active_visitors > 1:
                prefix += "Sản phẩm này hiện được rất nhiều khách quan tâm hỏi thăm ạ. 🌸 "

            ctx.replies.insert(0, prefix)
            
            # 🚀 EARLY EXIT: If it's JUST a greeting (short message without buying clues or knowledge curiosity), terminate here.
            # This saves LLM costs for pure rapport building.
            # We enforce strict False if there's any sign of deeper intent.
            if has_greeting and not buying_intent and not is_question and len(msg) < 15:
                # Add a soft closing if it's an early exit to not sound abrupt
                ctx.replies.append("Anh/Chị cần em tư vấn về liệu trình hay hỗ trợ thông tin gì không ạ?")
                return True # Terminate pipeline correctly
            
        return False # Continue to Order/Consultant for deep logic
