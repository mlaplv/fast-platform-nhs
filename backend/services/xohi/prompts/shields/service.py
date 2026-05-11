import re
import random
from typing import Optional
from ..schema import PromptComponent, PromptCategory

class SgeShieldService:
    """
    SGE Shield V2.0: AI Footprint Entropy & Lexical Sanitization.
    Prevents Google SGE from detecting AI-generated patterns.
    """
    
    # Common AI buzzwords to eliminate (Elite V2.2 Expansion)
    GLOBAL_BLACKLIST = [
        "trong bối cảnh", "hứa hẹn mang lại", "giải pháp tối ưu", 
        "ngày nay", "không chỉ... mà còn", "tầm cao mới", 
        "một cách đáng kể", "được thiết kế để", "khám phá ngay",
        "tổng kết lại", "tóm lại là", "đáng chú ý là", "thú vị là",
        "không thể phủ nhận", "chúng ta hãy cùng", "đầu tiên là",
        "hơn nữa", "ngoài ra", "bên cạnh đó", "thêm vào đó"
    ]

    def get_entropy_instructions(self, seed: Optional[str] = None) -> str:
        """Generates structural and lexical entropy instructions based on a seed."""
        if seed:
            random.seed(seed)
            
        patterns = [
            "Sử dụng các câu ngắn xen kẽ câu dài (Burstiness).",
            "Đảo ngược cấu trúc câu bị động sang chủ động.",
            "Bắt đầu đoạn văn bằng một câu hỏi hoặc một sự thật gây sốc.",
            "Tránh sử dụng các trạng từ chỉ mức độ (rất, quá, cực kỳ)."
        ]
        
        selected = random.sample(patterns, 2)
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
