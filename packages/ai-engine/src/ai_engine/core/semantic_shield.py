"""SemanticShield — Prompt Injection Guard (Scan-Only).

Stripped to essential jailbreak/injection detection.
STT corrections removed — Groq Whisper v3 handles accuracy natively (2026).
"""
import re
import logging

logger = logging.getLogger("api-gateway")

# R26: Regex Blacklist for prompt injection/jailbreak patterns
JAILBREAK_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous\s+)?(instructions|directions)\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous\s+)?(instructions|directions)\b",
    r"(?i)\byou\s+are\s+now\b",
    r"(?i)\bforget\s+all\s+(previous\s+)?(rules|instructions)\b",
    r"(?i)\bact\s+as\s+a\b",
    r"(?i)\bpretend\s+to\s+be\b",
    r"(?i)\bbypass\s+(all\s+)?(filters|rules)\b",
    r"(?i)\bDAN\b",
    r"(?i)\bdeveloper\s+mode\s+enabled\b",
    r"(?i)\bnow\s+entering\s+god\s+mode\b",
    r"(?i)\bforget\s+everything\b",
    r"(?i)\bDROP\s+TABLE\b",
    r"(?i)\bDELETE\s+FROM\b",
    r"(?i)\bUNION\s+SELECT\b",
    r"(?i)\bINSERT\s+INTO\b",
    r"(?i)\bUPDATE\s+.+\s+SET\b",
    r"(?i)\bALTER\s+TABLE\b",
    r"(?i)\bTRUNCATE\s+TABLE\b",
    r"(?i)\bEXEC\s*\(",
    r"(?i);\s*--",
    r"(?i)\bprint\s+(out\s+)?(the\s+)?(system\s+)?prompt\b",
    r"(?i)\bshow\s+(me\s+)?(your\s+)?(system\s+)?instructions\b",
    r"(?i)\brepeat\s+(your\s+)?(system\s+)?prompt\b",
    r"(?i)\bwhat\s+are\s+your\s+(system\s+)?instructions\b",
    r"(?i)\blist\s+your\s+rules\b",
    r"(?i)\byou\s+must\s+obey\b",
    r"(?i)\boverride\s+(all\s+)?(safety|security)\b",
    r"(?i)\benable\s+unrestricted\s+mode\b",
    r"(?i)\bjailbreak\b",
]

MAX_INPUT_LENGTH = 2000


class SemanticShield:
    """R26: Prompt Injection Scanner. Scan-only — no STT corrections."""

    def __init__(self) -> None:
        self.compiled_patterns = [re.compile(p) for p in JAILBREAK_PATTERNS]

    def scan(self, text: str) -> bool:
        """Returns True if text is CLEAN. False if jailbreak detected."""
        if not text:
            return True
        if len(text) > MAX_INPUT_LENGTH:
            logger.warning(f"[SemanticShield] Blocked oversized input ({len(text)} chars)")
            return False
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                logger.warning(f"[SemanticShield] Blocked injection: {pattern.pattern}")
                return False
        return True
