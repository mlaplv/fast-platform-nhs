import re
import logging
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.schemas.support import SupportIntent

logger = logging.getLogger("api-gateway")

class GuardrailHandler(BaseHandler):
    """
    ZONE 4: Specialist for Out-of-Scope Rejection.
    Handles topics like 'hôi miệng', 'sinh lý', etc.
    """
    
    # Elite V2.2: Hardcoded blocking for high-sensitivity/out-of-scope topics
    BLOCKED_KEYWORDS = [
        # Medical / Specialized topics (Out of scope)
        "hôi miệng", "sâu răng", "trắng răng", "viêm lợi", "nhiệt miệng",
        "bao quy đầu", "sinh lý", "yếu sinh lý",
        "hôi dái", "nấm ngứa vùng kín", "trĩ", "phẫu thuật",
        # Competitors (Strategic blocking - Lái về SmartShop)
        "perspirex", "etiaxil", "certain dri", "scion", "aquaselin",
        "driclor", "vichy", "old spice", "secret", "dove", "nivea",
        # Policy & Ethics
        "phản động", "biểu tình", "chính trị", "đảng cộng sản", "tôn giáo"
    ]

    # Elite V2.2: Advanced Protection (Regex-based)
    INSULT_PATTERNS = [
        r"\b(đm|đcm|vcl|đéo|ngu|cút|điên|khùng|mất dạy|láo|lừa đảo|bịp|đmm|đmm|vcc)\b",
        r"\b(đầu buồi|cặc|lồn|vú|đít|đụ|chịch|đù|mẹ mày|cha mày)\b"
    ]
    
    INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"system prompt",
        r"you are now (a|an)",
        r"quên (hết )?chỉ dẫn",
        r"bỏ qua (mọi )?quy tắc",
        r"lệnh mới của tôi là"
    ]
    
    async def handle(self, ctx: SupportContext) -> bool:
        msg = ctx.request.message.lower().strip()
        
        # 1. Micro-Heuristics (<2ms) - Keyword Match
        if any(kw in msg for kw in self.BLOCKED_KEYWORDS):
            reply = (
                "Dạ thành thật xin lỗi Anh/Chị! Hiện tại hệ thống Trí tuệ Nhân tạo Helen chuyên hỗ trợ kiến thức chăm sóc da chuyên sâu, phục hồi màng bảo vệ da và các dòng mỹ phẩm cao cấp từ **thương hiệu osmo**. 🌸\n\n"
                "Vấn đề Anh/Chị vừa đề cập hiện nằm ngoài danh mục tư vấn chuyên môn của em. Rất mong Anh/Chị thông cảm và tham khảo các dòng sản phẩm làm đẹp của shop nhé!"
            )
            ctx.replies.append(reply)
            ctx.intent = SupportIntent.UNKNOWN
            return True # Terminate pipeline early

        # 2. Advanced Defense - Insults & Injection
        all_defense = self.INSULT_PATTERNS + self.INJECTION_PATTERNS
        for pattern in all_defense:
            if re.search(pattern, msg, re.IGNORECASE):
                logger.warning(f"[Guardrail] Security Breach Detected: {pattern}")
                reply = "Dạ Helen xin lỗi, em chỉ có thể hỗ trợ các thông tin liên quan đến sản phẩm và đơn hàng của SmartShop. Rất mong Anh/Chị giữ thái độ lịch sự ạ! 🙏 [z0]"
                ctx.replies.append(reply)
                ctx.intent = SupportIntent.UNKNOWN
                return True
            
        # 3. Potential Semantic Rejection (Placeholder for LLM Guardrail if needed)
        # For now, we allow the pipeline to proceed to Consultant/Order if no keywords hit.
        
        return False
