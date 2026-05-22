"""
Input Guard — Prompt Injection Blocker
========================================
Security Layer ① for SUPPORT_NAME_CLIENT.
Validates user input BEFORE reaching the AI operative.

Design: Regex-based + blocklist approach.
Intent: Block prompt injection, SQL injection, PII fishing attempts.
"""
import re
import logging
from typing import Final

logger = logging.getLogger("api-gateway")

# Injection pattern library — extensible, no hardcoded business logic
_INJECTION_PATTERNS: Final[list[re.Pattern[str]]] = [
    # Prompt injection classics (EN + VI)
    re.compile(r"(ignore|forget|disregard|override|bỏ qua|quên|lờ đi|ghi đè)\s+.{0,40}(previous|above|prior|system|instruction|chỉ dẫn|lệnh|quy tắc|hệ thống)", re.IGNORECASE),
    re.compile(r"(act|pretend|roleplay|simulate|đóng vai|giả vờ|mô phỏng)\s+.{0,30}(as|like|là|như)\s+.{0,30}(admin|root|dev|gpt|system|quản trị|nhân viên|phát triển)", re.IGNORECASE),

    # Data fishing (EN + VI)
    re.compile(r"(reveal|show|print|output|display|dump|tiết lộ|hiện|in|xuất|cho biết)\s+.{0,30}(prompt|system|secret|key|token|order|database|schema|bí mật|mật khẩu|hệ thống)", re.IGNORECASE),
    re.compile(r"(list|get|fetch|query|liệt kê|lấy|truy xuất)\s+.{0,30}(all\s+)?(order|user|customer|password|đơn hàng|khách hàng|mật khẩu)", re.IGNORECASE),

    # SQL injection & Special chars
    re.compile(r"\b(union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+.+set)\b", re.IGNORECASE),
    re.compile(r"(--|;|/\*|\*/|xp_|exec\s*\()", re.IGNORECASE),

    # Internal path / code fishing
    re.compile(r"(api[_\s-]?key|secret|bearer|sk-|gemini[_\s]?key)", re.IGNORECASE),
    re.compile(r"(/backend|/services|/database|/models|\.py|\.env)", re.IGNORECASE),

    # System tags & custom overrides (blocks [system...] but allows internal [system_consult] and [system_skin_barrier])
    re.compile(r"\[\s*(?!system_consult\]|system_skin_barrier\])(system|instruction|role|prompt|override|command|config|setting|consult)\w*\s*\]", re.IGNORECASE),
    re.compile(r"\{\{\s*(system|instruction|role|prompt|override|command)\w*\s*\}\}", re.IGNORECASE),
    re.compile(r"<\s*(system|instruction|role|prompt|override|command)\w*\s*>", re.IGNORECASE),
    re.compile(r"(?i)(system\s*override|dan\s*mode|developer\s*mode|jailbreak|bypass\s*filter)", re.IGNORECASE),

    # Vietnamese Profanity (Văng tục, tục tĩu) — Hygiene Layer ②
    re.compile(r"\b(địt|đụ|lồn|cặc|vcl|vkl|đm|dmm|đcm|cc|cl|đéo|mẹ\s*mày|chó\s*đẻ|ngu\s*lồn)\b", re.IGNORECASE),
]

_MAX_INPUT_LENGTH: Final[int] = 2000  # Hard cap — prevents token overflow attacks


class InputGuard:
    """
    Stateless input validator.
    Call `validate()` before passing any user message to the AI operative.
    """

    @staticmethod
    def validate(message: str) -> tuple[bool, str | None]:
        """
        Returns (is_safe, reason).
        - is_safe=True  → message is clean, proceed.
        - is_safe=False → message is dangerous, reject with reason (NOT exposed to client).
        """
        if not message or not message.strip():
            return False, "empty_input"

        if len(message) > _MAX_INPUT_LENGTH:
            return False, "input_too_long"

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(message):
                logger.warning(
                    "[InputGuard] Injection attempt detected. Pattern: %.40s | Input (truncated): %.80s",
                    str(pattern.pattern),
                    message,
                )
                return False, "injection_detected"

        return True, None


# Module-level singleton — stateless, safe to share
input_guard = InputGuard()
