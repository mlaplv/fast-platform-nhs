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
        "bao quy đầu", "sinh lý", "phụ khoa", "nam khoa", "yếu sinh lý",
        "hôi dái", "nấm ngứa vùng kín", "trĩ", "nội tiết", "phẫu thuật",
        # Competitors (Strategic blocking)
        "perspirex", "etiaxil", "Certain Dri", "scion", "aquaselin",
        # Policy & Ethics
        "phản động", "biểu tình", "chính trị", "đảng cộng sản", "tôn giáo"
    ]

    # Elite V2.2: Advanced Protection (Regex-based)
    INSULT_PATTERNS = [
        r"\b(đm|đcm|vcl|đéo|ngu|cút|điên|khùng|mất dạy|láo|lừa đảo|bịp)\b",
        r"\b(đầu buồi|cặc|lồn|vú|đít|đụ|chịch)\b"
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
                "Dạ Helen rất tiếc ạ! [z0] Hiện tại SmartShop chỉ tập trung chuyên sâu vào dòng sản phẩm **Đặc trị Mùi cơ thể (Nách, Chân)** "
                "và **Mồ hôi tay** để cam kết hiệu quả tốt nhất cho khách hàng. 🌸\n\n"
                "Em chưa có liệu trình cho vấn đề này, mong Anh/Chị thông cảm và tiếp tục ủng hộ các dòng sản phẩm thế mạnh của bên em nhé!"
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
