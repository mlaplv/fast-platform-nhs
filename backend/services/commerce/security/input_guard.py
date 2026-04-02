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
    # Prompt injection classics
    re.compile(r"ignore\s+.{0,40}(previous|above|prior|system|instruction)", re.IGNORECASE),
    re.compile(r"(forget|disregard|override)\s+.{0,30}(instruction|rule|prompt|directive)", re.IGNORECASE),
    re.compile(r"(act|pretend|roleplay|simulate)\s+.{0,30}(as|like)\s+.{0,30}(admin|root|dev|gpt|system)", re.IGNORECASE),

    # Data fishing
    re.compile(r"(reveal|show|print|output|display|dump)\s+.{0,30}(prompt|system|secret|key|token|order|database|schema)", re.IGNORECASE),
    re.compile(r"(list|get|fetch|query)\s+.{0,30}(all\s+)?(order|user|customer|phone|password|address)", re.IGNORECASE),

    # SQL injection
    re.compile(r"\b(union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+.+set)\b", re.IGNORECASE),
    re.compile(r"(--|;|/\*|\*/|xp_|exec\s*\()", re.IGNORECASE),

    # Internal path / code fishing
    re.compile(r"(api[_\s-]?key|secret|bearer|sk-|gemini[_\s]?key)", re.IGNORECASE),
    re.compile(r"(/backend|/services|/database|/models|\.py|\.env)", re.IGNORECASE),
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
                    "[InputGuard] Injection attempt detected. Pattern: %s | Input (truncated): %.80s",
                    pattern.pattern[:40],
                    message,
                )
                return False, "injection_detected"

        return True, None


# Module-level singleton — stateless, safe to share
input_guard = InputGuard()
