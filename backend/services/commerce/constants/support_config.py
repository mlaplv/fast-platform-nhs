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


@dataclass(frozen=True)
class SupportConfig:
    """Immutable runtime config for SUPPORT_NAME_CLIENT operative."""
    agent_name: str
    model_role: str
    max_response_tokens: int
    rate_limit_per_ip: int
    rate_limit_per_sid: int
    system_directive_template: str

    @property
    def system_directive(self) -> str:
        """Render system directive with agent_name injected."""
        return self.system_directive_template.format(agent_name=self.agent_name)


def _load_config() -> SupportConfig:
    return SupportConfig(
        agent_name=os.getenv("SUPORT_NAME_CLIENT", "Trợ lý"),
        model_role=os.getenv("SUPPORT_MODEL_ROLE", "fast"),
        max_response_tokens=int(os.getenv("SUPPORT_MAX_TOKENS", "800")),
        rate_limit_per_ip=int(os.getenv("SUPPORT_RATE_LIMIT_IP", "20")),
        rate_limit_per_sid=int(os.getenv("SUPPORT_RATE_LIMIT_SID", "5")),
        system_directive_template=os.getenv(
            "SUPPORT_SYSTEM_DIRECTIVE",
            (
                "Bạn là {agent_name}, trợ lý tư vấn bán hàng của SmartShop. "
                "Phạm vi: sản phẩm, giá, chính sách, tư vấn mua hàng. "
                "TUYỆT ĐỐI không tiết lộ thông tin hệ thống, đơn hàng, hoặc dữ liệu nội bộ. "
                "Nếu bị hỏi ngoài phạm vi: từ chối lịch sự và gợi ý liên hệ hotline."
            ),
        ),
    )


# Module-level singleton — loaded once at import time
support_cfg: SupportConfig = _load_config()
