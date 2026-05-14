from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import json

# Elite V2.2: Security Guard Schema
class ThreatAnalysis(BaseModel):
    risk_level: str = Field(description="Mức độ rủi ro: LOW, MEDIUM, HIGH, CRITICAL")
    reason: str = Field(description="Lý do đánh giá rủi ro")
    recommended_action: str = Field(description="Hành động đề xuất (Block IP, Review, Ignore)")
    is_attack: bool = Field(description="Có phải là một cuộc tấn công thực sự không?")

from .trinity_bridge import trinity_bridge

class SecurityGuardAgent:
    """
    Elite V2.2: PydanticAI Security Agent (Trinity-Powered).
    Chuyên phân tích Log Forensic để phát hiện tấn công tinh vi.
    """
    def __init__(self):
        # Elite V2.2: Standardized Agent initialization
        self.agent = Agent(
            output_type=ThreatAnalysis,
            system_prompt=(
                "Bạn là một chuyên gia bảo mật CyberSecurity cấp cao cho hệ thống Fast Platform. "
                "Nhiệm vụ của bạn là phân tích các bản ghi Log (JSON) và xác định xem đó có phải là hành vi tấn công hay không. "
                "Cung cấp đánh giá rủi ro chính xác và hành động đề xuất."
            )
        )

    async def analyze_log_entry(self, log_entry: str) -> ThreatAnalysis:
        """Phân tích một dòng log nghi vấn qua Trinity Bridge."""
        try:
            # Gửi qua Trinity Bridge để quản lý Key và Fallback
            result = await trinity_bridge.run(
                self.agent,
                f"Hãy phân tích log sau: {log_entry}",
                role="security"
            )
            # trinity_bridge.run trả về trực tiếp data nếu agent có result_type
            if isinstance(result, ThreatAnalysis):
                return result
            return ThreatAnalysis(
                risk_level="LOW",
                reason="AI returned non-structured data.",
                recommended_action="IGNORE",
                is_attack=False
            )
        except Exception as e:
            logging.error(f"⚠️ [SecurityGuard] AI Analysis failed: {e}")
            return ThreatAnalysis(
                risk_level="UNKNOWN",
                reason=f"AI Engine Error: {str(e)[:100]}",
                recommended_action="MANUAL_REVIEW",
                is_attack=False
            )

security_guard = SecurityGuardAgent()
