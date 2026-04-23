import re
import logging
import difflib
from typing import Optional

logger = logging.getLogger("api-gateway")

RE_WS = re.compile(r'\s+')
RE_HTML = re.compile(r'<[^>]+>')


def _strip(text: str) -> str:
    """Normalize text for loose comparison: strip HTML tags and collapse whitespace."""
    return RE_WS.sub(' ', RE_HTML.sub('', text)).strip()


def surgical_stitch(content: str, old_text: str, new_text: str, label: str = "Stitcher") -> str:
    """
    R1.9/V82.75: Advanced Neural Surgical Stitching Utility.
    Uses Difflib for high-precision fuzzy matching when exact match fails.
    """
    if not old_text or not new_text:
        return content

    # [PHASE 1] Exact Match (O(1) fast path)
    if old_text in content:
        return content.replace(old_text, new_text, 1)

    # [PHASE 2] Neural Fuzzy Discovery (difflib)
    # We strip HTML only for comparison, but we must stay in the raw content for the final replacement
    norm_old = _strip(old_text)
    if len(norm_old) < 15: # Critical floor for fuzzy safety
        logger.warning(f"[{label}] Surgical match failed: Snippet too short for fuzzy ({len(norm_old)} chars).")
        return content

    # To avoid O(N*M) explosion on massive articles, we clip the search window 
    # if the anchor (first word) can be found.
    words = norm_old.split()
    anchor = words[0] if words else ""
    
    search_start = 0
    search_end = len(content)
    
    if anchor and anchor.lower() in content.lower():
        idx = content.lower().find(anchor.lower())
        search_start = max(0, idx - 100)
        search_end = min(len(content), idx + len(old_text) * 3 + 200)

    window = content[search_start:search_end]
    
    # Use SequenceMatcher to find the best block
    s = difflib.SequenceMatcher(None, norm_old, window)
    match = s.find_longest_match(0, len(norm_old), 0, len(window))
    
    # R2026.5: If we found a substantial shared block (>45% of old_text), we proceed
    # We lowered the threshold slightly to catch more manual edits.
    if match.size > len(norm_old) * 0.45:
        # Infer the start/end of the full snippet in the window
        # We calculate the relative position to expand the window correctly
        w_match_start = match.b
        w_match_end = match.b + match.size
        
        offset_start = match.a
        offset_end = len(norm_old) - (match.a + match.size)
        
        # Elite V2.7: Dynamic Expansion. We use 1.6x multiplier for better coverage 
        # of structural changes (like extra spaces/tags)
        final_start = max(0, w_match_start - int(offset_start * 1.6))
        final_end = min(len(window), w_match_end + int(offset_end * 1.6))
        
        # Verify the candidate block in raw content
        candidate = window[final_start:final_end]
        if len(_strip(candidate)) > len(norm_old) * 0.35:
            logger.info(f"[{label}] Neural fuzzy match successful (Score: {match.size}/{len(norm_old)}).")
            return content[:search_start + final_start] + new_text + content[search_start + final_end:]

    # [PHASE 3] Extreme Anchor Recovery (Last resort)
    # If we have a very strong anchor but the rest is messed up
    if anchor and len(anchor) > 10 and anchor in content:
        # If the anchor is unique enough, we might try to replace the paragraph it belongs to
        # But for now, we just log and fail safely to avoid data corruption.
        pass

    logger.warning(f"[{label}] Surgical match failed: Snippet not found even with Neural Fuzzy Logic.")
    return content
