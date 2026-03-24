import re
import logging
from typing import Optional

logger = logging.getLogger("api-gateway")

RE_WS = re.compile(r'\s+')
RE_HTML = re.compile(r'<[^>]+>')


def _strip(text: str) -> str:
    """Normalize text for loose comparison: strip HTML tags and collapse whitespace."""
    return RE_WS.sub(' ', RE_HTML.sub('', text)).strip()


def surgical_stitch(content: str, old_text: str, new_text: str, label: str = "Stitcher") -> str:
    """
    R1.9/V82.70: Advanced Surgical Stitching Utility.
    Replaces old_text with new_text in content using:
    Phase 1 - Exact match  
    Phase 2 - HTML-agnostic fuzzy match (strips HTML before comparison)
    """
    if not old_text or not new_text:
        return content

    # Phase 1: Exact Match
    if old_text in content:
        return content.replace(old_text, new_text, 1)

    # Phase 2: HTML-stripped fuzzy match
    norm_old = _strip(old_text)
    if len(norm_old) < 10:
        logger.warning(f"[{label}] Surgical match failed: Snippet too short.")
        return content

    norm_content = _strip(content)
    if norm_old not in norm_content:
        logger.warning(f"[{label}] Surgical match failed: Snippet not found even with relaxed match.")
        return content

    # Use the position in stripped content to infer position in original content
    # Strategy: find the first actual word of norm_old in raw content, then replace the surrounding block
    first_words = norm_old.split()[:5]
    first_token = first_words[0] if first_words else ''
    if not first_token:
        return content

    start = content.lower().find(first_token.lower())
    if start == -1:
        logger.warning(f"[{label}] Surgical match failed: Could not locate first word '{first_token[:20]}'.")
        return content

    # Approximate end: len ratio of raw/norm content
    ratio = len(content) / max(len(norm_content), 1)
    approx_len = int(len(norm_old) * ratio * 1.5)
    candidate = content[start: start + approx_len]

    if _strip(candidate).startswith(norm_old[:len(norm_old) // 2]):
        logger.info(f"[{label}] Relaxed match successful via first-word anchor.")
        return content[:start] + new_text + content[start + approx_len:]

    logger.warning(f"[{label}] Surgical match failed: Snippet not found even with relaxed match.")
    return content
