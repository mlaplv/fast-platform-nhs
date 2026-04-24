import re
import logging
import difflib
from typing import Optional

logger = logging.getLogger("api-gateway")

RE_WS = re.compile(r'\s+')
RE_HTML = re.compile(r'<[^>]+>')


def _strip(text: str) -> str:
    """
    Elite V2.2: Universal Surgical Stripper.
    Strips HTML and keeps ONLY alphanumeric characters for robust fuzzy matching.
    """
    if not text: return ""
    text = unicodedata.normalize('NFC', text)
    # Strip HTML tags
    text = RE_HTML.sub('', text)
    # Use isalnum() for perfect Unicode support (including Vietnamese accents)
    return "".join([ch for ch in text if ch.isalnum()]).lower()


import unicodedata

def surgical_stitch(content: str, old_text: str, new_text: str, label: str = "Stitcher") -> str:
    """
    R1.9/V82.75: Advanced Neural Surgical Stitching Utility.
    Strategy: 3-phase matching (Exact → HTML-aware Fuzzy → Anchor Recovery)
    
    CRITICAL FIX V87.1: Annotations từ AI luôn là plain text, nhưng bài viết là HTML.
    CRITICAL FIX V87.2: Force NFC Normalization để tránh lỗi tiếng Việt NFD/NFC.
    """
    if not old_text or not new_text or not content:
        return content

    # Chuẩn hóa Unicode NFC (W3C Standard) để tránh sai lệch dấu tiếng Việt
    content = unicodedata.normalize('NFC', content)
    old_text = unicodedata.normalize('NFC', old_text)
    new_text = unicodedata.normalize('NFC', new_text)

    # [PHASE 1] Exact Match (O(1) fast path)
    if old_text in content:
        return content.replace(old_text, new_text, 1)

    # [PHASE 1.5] HTML-stripped Exact Match
    # Annotation text là plain text, ta tìm nó trong phiên bản stripped của content
    norm_old = _strip(old_text)
    if len(norm_old) < 10:
        logger.warning(f"[{label}] Surgical match failed: Snippet too short ({len(norm_old)} chars).")
        return content

    # Tìm anchor (chuỗi ~20 ký tự đầu tiên) để xác định "vùng phẫu thuật" trong HTML gốc
    # Sử dụng kỹ thuật "Sliding Window" trên plain text → ánh xạ về HTML
    content_stripped = _strip(content)
    
    # Tìm vị trí của norm_old trong content_stripped
    pos_in_stripped = content_stripped.find(norm_old)
    if pos_in_stripped != -1:
        # Tìm thấy exact match trong bản stripped → Ánh xạ ngược vào HTML gốc
        # Lấy ~20 ký tự đầu và ~20 ký tự cuối làm "neo" để tìm trong HTML gốc
        anchor_start = norm_old[:min(30, len(norm_old))]
        anchor_end = norm_old[max(0, len(norm_old) - 30):]
        
        # Tìm vị trí bắt đầu trong HTML gốc bằng cách tìm anchor_start sau khi strip từng vị trí
        html_start = _find_html_pos(content, anchor_start)
        html_end = _find_html_pos_reverse(content, anchor_end)
        
        if html_start is not None and html_end is not None and html_end > html_start:
            # Kiểm tra xem phần cắt ra có hợp lệ không (>60% match)
            candidate = content[html_start:html_end]
            candidate_stripped = _strip(candidate)
            if len(candidate_stripped) > 0:
                # Sử dụng difflib để xác nhận match quality (trên bản stripped alphanumeric)
                ratio = difflib.SequenceMatcher(None, norm_old, candidate_stripped).ratio()
                if ratio > 0.60: # Lowered threshold for better recovery of manual edits
                    logger.info(f"[{label}] HTML-aware match successful (Ratio: {ratio:.2f}).")
                    return content[:html_start] + new_text + content[html_end:]

    # [PHASE 2] Neural Fuzzy Discovery (difflib trên stripped content)
    s = difflib.SequenceMatcher(None, norm_old, content_stripped)
    match = s.find_longest_match(0, len(norm_old), 0, len(content_stripped))
    
    if match.size > len(norm_old) * 0.45:
        # Tìm chuỗi matched trong stripped
        matched_text = content_stripped[match.b:match.b + match.size]
        # Ánh xạ ngược vào HTML gốc
        html_start = _find_html_pos(content, matched_text[:min(25, len(matched_text))])
        if html_start is not None:
            # Mở rộng ra phía sau để bao phủ toàn bộ snippet
            remaining = len(norm_old) - match.a
            html_end = min(len(content), html_start + int(remaining * 2.5))
            candidate_stripped = _strip(content[html_start:html_end])
            ratio = difflib.SequenceMatcher(None, norm_old, candidate_stripped).ratio()
            if ratio > 0.45:
                logger.info(f"[{label}] Neural fuzzy match successful (Score: {match.size}/{len(norm_old)}, Ratio: {ratio:.2f}).")
                return content[:html_start] + new_text + content[html_end:]

    logger.warning(f"[{label}] Surgical match failed: Snippet not found even with Neural Fuzzy Logic.")
    return content


def _build_alphanumeric_map(html: str) -> tuple[str, list[int]]:
    """
    Elite V2.2 Helper: Unified HTML-to-Alphanumeric Mapping.
    Returns (clean_buffer, plain_to_html_map).
    """
    html = unicodedata.normalize('NFC', html)
    parts = re.split(r'(<[^>]+>)', html)
    plain_to_html_map: list[int] = []
    plain_buffer = ""
    
    html_pos = 0
    for part in parts:
        if part.startswith('<'):
            html_pos += len(part)
        else:
            for ch_idx, ch in enumerate(part):
                # CNS V88.5: Use isalnum() for perfect parity with frontend
                if ch.isalnum():
                    plain_to_html_map.append(html_pos + ch_idx)
                    plain_buffer += ch.lower()
            html_pos += len(part)
    return plain_buffer, plain_to_html_map


def _find_html_pos(html: str, anchor: str) -> Optional[int]:
    """
    Elite V2.2: Robust Alphanumeric HTML Mapper.
    Finds the index in HTML that corresponds to the start of the alphanumeric anchor.
    """
    if not anchor: return None
    
    plain_buffer, plain_to_html_map = _build_alphanumeric_map(html)
    anchor_clean = "".join(re.findall(r'[\w\d]+', anchor, re.UNICODE)).lower()
    if not anchor_clean: return None
    
    idx = plain_buffer.find(anchor_clean)
    if idx != -1 and idx < len(plain_to_html_map):
        return plain_to_html_map[idx]
    return None


def _find_html_pos_reverse(html: str, anchor: str) -> Optional[int]:
    """
    Finds the index in HTML that corresponds to the END of the alphanumeric anchor.
    """
    if not anchor: return None
    
    plain_buffer, plain_to_html_map = _build_alphanumeric_map(html)
    anchor_clean = "".join(re.findall(r'[\w\d]+', anchor, re.UNICODE)).lower()
    if not anchor_clean: return None
    
    idx = plain_buffer.rfind(anchor_clean)
    if idx != -1:
        end_idx = idx + len(anchor_clean)
        if end_idx <= len(plain_to_html_map):
            if end_idx == len(plain_to_html_map):
                return len(html)
            return plain_to_html_map[end_idx - 1] + 1
    return None

