from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext

class GreetingHandler(BaseHandler):
    """
    ZONE 1: Persona Greeting Specialist.
    Priority: Build rapport and set the Vibe (WARM/PROFESSIONAL).
    """

    async def handle(self, ctx: SupportContext) -> bool:
        # 1. Skip if conversation is too deep or no greeting detected in current message
        # UNLESS it's the very first message of the session.
        
        is_first_msg = not ctx.history_text
        has_greeting = any(kw in ctx.request.message.lower() for kw in ["chào", "hi", "hello", "dạ", "alo"])
        
        if is_first_msg or has_greeting:
            # Elite V2.2: Personality-Driven Greeting Based on Customer DNA
            prefix = "Dạ Helen chào Anh/Chị! 🌸 "
            
            if ctx.dna.segment == "VIP":
                prefix = f"Dạ Helen thân chào khách quý! 🌟 Em rất vui được gặp lại mình ạ. "
            elif ctx.dna.segment == "REGULAR":
                prefix = f"Dạ Helen chào Anh/Chị, rất vui được gặp lại mình! "
            elif ctx.dna.segment == "CHURN":
                prefix = f"Dạ Helen chào Anh/Chị ạ! Em rất nhớ mình, hôm nay em có ưu đãi dành riêng cho mình đây... 🎁 "
            
            # Special case for products
            if ctx.request.product_slug == "hong-son":
                prefix += "Cảm ơn Anh/Chị đã quan tâm đến liệu trình Đặc trị Hôi nách Hồng Sơn của bên em. "

            ctx.replies.insert(0, prefix)
            
        # Greeting never 'consumes' the intent, to allow Order/Consultant to run.
        return False
