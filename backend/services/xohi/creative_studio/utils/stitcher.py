import re
import logging
from typing import List, Dict, Optional
from backend.utils.noise_cleaner import RE_WHITESPACE

logger = logging.getLogger("api-gateway")

def surgical_stitch(content: str, old_text: str, new_text: str, label: str = "Stitcher") -> str:
    """
    R1.8/V82.68: Advanced Surgical Stitching Utility.
    Replaces old_text with new_text in content using exact or 'Relaxed' matching.
    """
    if not old_text or old_text not in content:
        # Phase 2: Relaxed Match (whitespace-agnostic)
        norm_old = RE_WHITESPACE.sub('', old_text)
        if len(norm_old) < 20:
            logger.warning(f"[{label}] Surgical match failed: Snippet too short for relaxed match.")
            return content
            
        # Search for a segment that normalizes to the same thing
        for start_idx in range(len(content) - len(old_text) + 20):
            # Optimistic window search
            window = content[start_idx : start_idx + len(old_text) + 20]
            if RE_WHITESPACE.sub('', window).startswith(norm_old):
                # Found it! Determine actual match segment
                actual_match = content[start_idx : start_idx + len(old_text)]
                # Check if slightly wider window matches better?
                # For now, length-based slice is the gold standard for surgical precision
                logger.info(f"[{label}] Relaxed match successful.")
                return content.replace(actual_match, new_text)
        
        logger.warning(f"[{label}] Surgical match failed: Snippet not found even with relaxed match.")
        return content
        
    # Phase 1: Exact Match (High Fidelity)
    return content.replace(old_text, new_text)
