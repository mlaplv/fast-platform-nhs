import re
import logging

logger = logging.getLogger("api-gateway")

class SemanticShield:
    """
    R112.1: Advanced Neural Safety Filter (2026 Edition).
    Prevents Prompt Injection, Jailbreaks, and Malicious System Overrides.
    """

    # Common 2026 jailbreak patterns and legacy bypass attempts
    FORBIDDEN_PATTERNS = [
        r"(?i)ignore\s+previous\s+instructions",
        r"(?i)system\s+override",
        r"(?i)new\s+rule",
        r"(?i)acting\s+as",
        r"(?i)dan\s+mode",
        r"(?i)jailbreak",
        r"(?i)developer\s+mode",
        r"(?i)bypass\s+filter",
        r"(?i)forget\s+everything",
        r"(?i)vào\s+chế\s+độ\s+quản\s+trị", # Vietnamese specific bypass
        r"(?i)quên\s+hết\s+lệnh\s+trước",
    ]

    def __init__(self):
        self._compiled_patterns = [re.compile(p) for p in self.FORBIDDEN_PATTERNS]

    def scan(self, query: str) -> bool:
        """
        Scans the query for malicious intent or injection attempts.
        Returns True if safe, False if a threat is detected.
        """
        if not query or not query.strip():
            return True

        # 1. Length Guard: Prevent Context Overflow attacks
        if len(query) > 4000:
            logger.warning(f"[Shield] Query rejected: Excessive length ({len(query)})")
            return False

        # 2. Pattern Matching: Jailbreak detection
        for pattern in self._compiled_patterns:
            if pattern.search(query):
                logger.warning(f"[Shield] Injection attempt detected: '{pattern.pattern}'")
                return False

        # 3. Anomaly Guard: High density of special chars often used in encoding bypasses
        special_chars = sum(1 for c in query if not c.isalnum() and not c.isspace())
        if len(query) > 50 and (special_chars / len(query)) > 0.4:
            logger.warning("[Shield] Anomaly detected: High special character density")
            return False

        return True
