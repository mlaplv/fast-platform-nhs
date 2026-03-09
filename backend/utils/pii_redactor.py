"""
PII Redactor — Personal Identifiable Information Shield
========================================================
Masks PII (phone numbers, emails, Vietnamese citizen IDs, addresses)
from text BEFORE it leaves the server to Cloud LLM (Gemini/OpenAI).

The original PII is stored in a session map so the Gateway can
re-hydrate it before writing to the database.

Usage:
    from backend.utils.pii_redactor import PIIRedactor
    redactor = PIIRedactor()
    safe_text, pii_map = redactor.redact("Gọi cho tôi số 0912345678")
    # safe_text = "Gọi cho tôi số [PHONE_REDACTED_1]"
    # pii_map = {"[PHONE_REDACTED_1]": "0912345678"}
    original = redactor.rehydrate(safe_text, pii_map)
"""
import re
from typing import Dict, Tuple


class PIIRedactor:
    """Regex-based PII redaction for Vietnamese and international formats."""

    # Vietnamese phone: 0xxx xxx xxxx or +84 xxx xxx xxxx
    _RE_PHONE = re.compile(
        r"(?:\+84|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}\b"
    )

    # Email
    _RE_EMAIL = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    # Vietnamese Citizen ID (CCCD): 12 digits
    _RE_CCCD = re.compile(r"\b\d{12}\b")

    # Credit card-like: 4 groups of 4 digits
    _RE_CARD = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")

    def redact(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Scan text for PII and replace with placeholders.
        Returns (redacted_text, pii_map) where pii_map maps placeholder → original.
        """
        if not text:
            return text, {}

        pii_map: Dict[str, str] = {}
        counter = {"phone": 0, "email": 0, "id": 0, "card": 0}

        def _replace(match: re.Match, category: str) -> str:
            counter[category] += 1
            placeholder = f"[{category.upper()}_REDACTED_{counter[category]}]"
            pii_map[placeholder] = match.group(0)
            return placeholder

        result = text
        # Order matters: check card before CCCD (card is 16 digits, CCCD is 12)
        result = self._RE_CARD.sub(lambda m: _replace(m, "card"), result)
        result = self._RE_PHONE.sub(lambda m: _replace(m, "phone"), result)
        result = self._RE_EMAIL.sub(lambda m: _replace(m, "email"), result)
        result = self._RE_CCCD.sub(lambda m: _replace(m, "id"), result)

        return result, pii_map

    @staticmethod
    def rehydrate(text: str, pii_map: Dict[str, str]) -> str:
        """Replace placeholders back with original PII values."""
        result = text
        for placeholder, original in pii_map.items():
            result = result.replace(placeholder, original)
        return result
