"""
DataStripper — Context Compaction for A2A Token Efficiency (R7)
===============================================================
Strips heavy/unnecessary fields from database payloads BEFORE they enter
the LLM context window. Prevents burning thousands of tokens on HTML content,
image URLs, timestamps, and long descriptions that LLMs don't need.

Usage:
    from backend.utils.data_stripper import DataStripper
    lean_data = DataStripper.strip(records, allowed_fields=["id", "name", "price"])
"""
from typing import Dict, List, Optional, Set, Union


# Fields that are ALWAYS stripped from LLM context (never useful for reasoning)
_ALWAYS_STRIP = {
    "image_url", "imageUrl", "image", "thumbnail", "avatar",
    "password", "passwordHash", "password_hash",
    "html_content", "htmlContent", "html",
    "updated_at", "updatedAt",
    "deleted_at", "deletedAt",
}

# Maximum string field length before truncation
_MAX_FIELD_LENGTH = 300

# Maximum records in a single LLM context payload
MAX_CONTEXT_RECORDS = 10


class DataStripper:
    """R7: Context Compaction — strip fat from DB payloads before LLM ingestion."""

    @staticmethod
    def strip(
        records: List[Dict[str, object]],
        allowed_fields: Optional[Set[str]] = None,
        max_records: int = MAX_CONTEXT_RECORDS,
    ) -> List[Dict[str, object]]:
        """
        Strip heavy fields and truncate long strings.
        
        Args:
            records: List of dicts from database query
            allowed_fields: If set, ONLY these fields are kept (whitelist mode).
                           If None, _ALWAYS_STRIP fields are removed (blacklist mode).
            max_records: Hard cap on number of records (default 10)
        """
        result = []
        for record in records[:max_records]:
            if not isinstance(record, dict):
                continue

            if allowed_fields:
                # Whitelist mode: only keep explicitly allowed fields
                stripped = {
                    k: DataStripper._truncate(v)
                    for k, v in record.items()
                    if k in allowed_fields
                }
            else:
                # Blacklist mode: remove known heavy fields
                stripped = {
                    k: DataStripper._truncate(v)
                    for k, v in record.items()
                    if k not in _ALWAYS_STRIP
                }

            result.append(stripped)

        return result

    @staticmethod
    def strip_single(
        record: Dict[str, object],
        allowed_fields: Optional[Set[str]] = None
    ) -> Dict[str, object]:
        """Strip a single record."""
        return DataStripper.strip([record], allowed_fields, max_records=1)[0] if record else {}

    @staticmethod
    def _truncate(value: object) -> object:
        """Truncate string values that exceed max length."""
        if isinstance(value, str) and len(value) > _MAX_FIELD_LENGTH:
            return value[:_MAX_FIELD_LENGTH] + "…"
        return value
