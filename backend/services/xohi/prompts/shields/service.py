import re
import random
from typing import Optional
from ..schema import PromptComponent, PromptCategory

class SgeShieldService:
    """
    SGE Shield V2.0: AI Footprint Entropy & Lexical Sanitization.
    Prevents Google SGE from detecting AI-generated patterns.
    """
    
    # Common AI buzzwords to eliminate (Elite V2.2 Expansion + SGE Shield V2.0)
    GLOBAL_BLACKLIST = [
        "trong bối cảnh", "hứa hẹn mang lại", "giải pháp tối ưu", 
        "ngày nay", "không chỉ... mà còn", "tầm cao mới", 
        "một cách đáng kể", "được thiết kế để", "khám phá ngay",
        "tổng kết lại", "tóm lại là", "đáng chú ý là", "thú vị là",
        "không thể phủ nhận", "chúng ta hãy cùng", "đầu tiên là",
        "hơn nữa", "ngoài ra", "bên cạnh đó", "thêm vào đó",
        # SGE Shield V2.0: Extended patterns
        "đặc biệt đáng chú ý", "một cách toàn diện", "chúng ta có thể thấy",
        "về cơ bản", "tựu chung lại", "qua đó cho thấy",
        "xét cho cùng", "nói một cách khác", "theo đó",
        "nhìn nhận một cách khách quan", "cần phải nhấn mạnh rằng",
        "trên thực tế", "điều này cho thấy", "có thể nói rằng",
        "cũng cần lưu ý", "đáng lưu ý rằng",
    ]

    def get_entropy_instructions(self, seed: Optional[str] = None) -> str:
        """Generates structural and lexical entropy instructions based on a seed."""
        if seed:
            random.seed(seed)
            
        patterns = [
            "Sử dụng các câu ngắn xen kẽ câu dài (Burstiness).",
            "Đảo ngược cấu trúc câu bị động sang chủ động.",
            "Bắt đầu đoạn văn bằng một câu hỏi hoặc một sự thật gây sốc.",
            "Tránh sử dụng các trạng từ chỉ mức độ (rất, quá, cực kỳ).",
            "Chèn 1-2 câu rất ngắn (3-5 từ) giữa các đoạn dài để phá nhịp.",
            "Bắt đầu 1 đoạn bằng liên từ phản biện (Nhưng, Tuy nhiên, Trái lại).",
            "Dùng câu hỏi tu từ ở giữa bài để kích thích tư duy người đọc.",
            "Kết thúc 1 phần bằng câu ngắn gọn, dứt khoát — không giải thích thêm.",
        ]
        
        selected = random.sample(patterns, min(4, len(patterns)))
        return f"[SGE SHIELD ENTROPY]\n" + "\n".join(selected)

    def get_shield_component(self, seed: Optional[str] = None) -> PromptComponent:
        entropy = self.get_entropy_instructions(seed)
        return PromptComponent(
            id=f"sge_shield_{seed[:8] if seed else 'global'}",
            category=PromptCategory.SHIELD,
            content=f"{entropy}\n[LEXICAL RULES] Cấm dùng: {', '.join(self.GLOBAL_BLACKLIST)}"
        )

    def sanitize(self, text: str) -> str:
        """Removes blacklisted AI buzzwords from the text."""
        for word in self.GLOBAL_BLACKLIST:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            text = pattern.sub("", text)
        return text

shield_service = SgeShieldService()
