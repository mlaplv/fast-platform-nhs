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
        # We search for clues of price/buying interest to avoid Early Exit when user asks "Chào, giá bao nhiêu?"
        buying_intent = any(kw in msg for kw in ["giá", "bao nhiêu", "nhiêu", "mua", "đặt", "ship", "lấy", "tư vấn"])
        
        if is_first_msg or has_greeting:
            prefix = "Dạ Helen chào Anh/Chị! 🌸 "
            if ctx.dna.segment == "VIP":
                prefix = f"Dạ Helen thân chào khách quý! 🌟 Rất vui được gặp lại mình ạ. "
            elif ctx.dna.segment == "REGULAR":
                prefix = f"Dạ Helen chào Anh/Chị, em rất vui được gặp lại mình! "
            
            if ctx.p_info:
                prefix += f"Em rất hân hạnh được hỗ trợ mình về liệu trình **{ctx.p_info.name}** bên em ạ. "

            ctx.replies.insert(0, prefix)
            
            # 🚀 EARLY EXIT: If it's JUST a greeting (short message without buying clues), terminate here.
            # This saves LLM costs for pure rapport building.
            if has_greeting and not buying_intent and len(msg) < 15:
                # Add a soft closing if it's an early exit to not sound abrupt
                ctx.replies.append("Anh/Chị cần em tư vấn về liệu trình hay hỗ trợ thông tin gì không ạ?")
                return True # Terminate pipeline correctly
            
        return False # Continue to Order/Consultant for deep logic
