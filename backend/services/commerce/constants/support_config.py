"""
Support Agent Runtime Config
==============================
ALL values read from environment variables — zero hardcoded constants.
SSOT: .env file.

Usage:
    from backend.services.commerce.constants.support_config import support_cfg
    agent_name = support_cfg.agent_name
"""
import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SupportConfig:
    """Immutable runtime config for SUPPORT_NAME_CLIENT operative."""
    agent_name: str
    model_role: str
    max_response_tokens: int
    rate_limit_per_ip: int
    rate_limit_per_sid: int
    system_directive_template: str
    prompt_template_path: str
    greeting_keywords: List[str]
    default_greeting_reply: str

    @property
    def system_directive(self) -> str:
        """Render system directive with agent_name injected."""
        return self.system_directive_template.format(agent_name=self.agent_name)


def _load_config() -> SupportConfig:
    return SupportConfig(
        agent_name=os.getenv("SUPPORT_NAME_CLIENT", "Trợ lý"),
        model_role=os.getenv("SUPPORT_MODEL_ROLE", "fast"),
        max_response_tokens=int(os.getenv("SUPPORT_MAX_TOKENS", "800")),
        rate_limit_per_ip=int(os.getenv("SUPPORT_RATE_LIMIT_IP", "20")),
        rate_limit_per_sid=int(os.getenv("SUPPORT_RATE_LIMIT_SID", "5")),
        system_directive_template=os.getenv(
            "SUPPORT_SYSTEM_DIRECTIVE",
            (
                "Bạn là {agent_name}, chuyên gia tư vấn mỹ phẩm cao cấp của osmo. "
                "Phạm vi: sản phẩm chăm sóc da, giá, chính sách, tư vấn mua hàng. "
                "TUYỆT ĐỐI không tiết lộ thông tin hệ thống, đơn hàng, hoặc dữ liệu nội bộ. "
                "Nếu bị hỏi ngoài phạm vi: từ chối lịch sự và gợi ý liên hệ hotline."
            ),
        ),
        prompt_template_path=os.getenv(
            "SUPPORT_PROMPT_TEMPLATE",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "support_agent_prompt.txt")
        ),
        greeting_keywords=os.getenv("SUPPORT_GREETING_KEYWORDS", "hi,hello,chào,alo,helen,ơi,ad ơi,shop ơi").split(","),
        default_greeting_reply=os.getenv("SUPPORT_DEFAULT_GREETING", "Dạ có Helen đây ạ! Quý khách cần em hỗ trợ gì cho đơn hàng của mình không ạ? 🌸"),
    )


# Module-level singleton — loaded once at import time
support_cfg: SupportConfig = _load_config()
