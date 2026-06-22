"""
Vietnamese Elite NLP Guard — Tầng 2: Linguistic Analyzer.
Sử dụng underthesea (open-source) cho POS tagging + Dependency Parsing.

Chức năng:
- Kiểm tra cấu trúc câu thật sự (chủ ngữ + vị ngữ) bằng dependency parse
- Tính Content Density (tỷ lệ từ mang nghĩa) để phát hiện sáo rỗng
- Phát hiện lặp từ/cụm từ thừa bằng N-gram analysis
"""

import re
import logging
from collections import Counter
from typing import Optional

logger = logging.getLogger("api-gateway")

# ── Lazy imports để tránh load nặng khi module được import ──────────────
_pos_tag_fn: Optional[object] = None
_dep_parse_fn: Optional[object] = None
_word_tokenize_fn: Optional[object] = None


def _ensure_underthesea() -> None:
    """Lazy-load underthesea functions lần đầu sử dụng."""
    global _pos_tag_fn, _dep_parse_fn, _word_tokenize_fn
    if _pos_tag_fn is not None:
        return
    try:
        from underthesea import pos_tag, dependency_parse, word_tokenize
        _pos_tag_fn = pos_tag
        _dep_parse_fn = dependency_parse
        _word_tokenize_fn = word_tokenize
        logger.info("[NLP Guard] underthesea loaded successfully.")
    except ImportError:
        logger.warning("[NLP Guard] underthesea not installed. Tầng 2 disabled.")
    except Exception as e:
        logger.warning(f"[NLP Guard] underthesea load error: {e}. Tầng 2 disabled.")


# ── POS Tag Sets ────────────────────────────────────────────────────────
# Từ mang nghĩa thực (content words)
CONTENT_POS_TAGS: frozenset[str] = frozenset({
    "N", "Np", "Nc", "Nu",   # Danh từ (chung, riêng, loại, đơn vị)
    "V",                      # Động từ
    "A",                      # Tính từ
    "M",                      # Số từ
})

# Từ chức năng (function words) — thường không mang nghĩa thực
FUNCTION_POS_TAGS: frozenset[str] = frozenset({
    "E",   # Giới từ
    "C",   # Liên từ
    "CC",  # Liên từ đẳng lập
    "R",   # Phó từ
    "T",   # Trợ từ
    "I",   # Thán từ
    "CH",  # Dấu câu
    "L",   # Định từ
    "P",   # Đại từ
})

# Dependency relations chỉ chủ ngữ
SUBJECT_RELATIONS: frozenset[str] = frozenset({
    "nsubj", "csubj", "nsubj:pass", "csubj:pass",
})


def check_sentence_completeness(sentence: str) -> tuple[bool, str]:
    """
    Kiểm tra câu có đầy đủ chủ ngữ + vị ngữ bằng dependency parse.
    
    Returns: (is_valid, error_message)
    """
    _ensure_underthesea()
    if _dep_parse_fn is None or _pos_tag_fn is None:
        return True, ""  # Graceful fallback: bỏ qua nếu underthesea không khả dụng
    
    # Strip HTML tags cho plain text analysis
    plain = re.sub(r'<[^>]+>', ' ', sentence).strip()
    plain = ' '.join(plain.split())
    if not plain or len(plain) < 5:
        return True, ""  # Quá ngắn để phân tích
    
    try:
        deps: list[tuple[str, int, str]] = _dep_parse_fn(plain)
        tags: list[tuple[str, str]] = _pos_tag_fn(plain)
    except Exception as e:
        logger.warning(f"[NLP Guard] Parse error: {e}")
        return True, ""  # Graceful fallback
    
    if not deps or not tags:
        return True, ""
    
    # 1. Tìm node ROOT và POS tag của nó
    root_idx = -1
    root_tag = None
    for idx, (word, head, rel) in enumerate(deps):
        if rel == "root":
            root_idx = idx
            if idx < len(tags):
                root_tag = tags[idx][1]
            break
            
    if root_idx == -1 or root_tag is None:
        return False, "Câu thiếu thành phần cốt lõi (không tìm thấy vị ngữ chính)."
    
    # 2. Kiểm tra có chủ ngữ không
    has_subject = any(rel in SUBJECT_RELATIONS for _, _, rel in deps)
    
    # 3. Kiểm định cấu trúc dựa trên POS của ROOT
    if root_tag in ("N", "Np", "Nc", "Nu"):
        # Cụm danh từ: Luôn hợp lệ nếu không quá ngắn (đã check ở T1)
        return True, ""
        
    elif root_tag == "A":
        # Cụm tính từ miêu tả: Luôn hợp lệ
        return True, ""
        
    elif root_tag == "V":
        # Cụm động từ: Yêu cầu có chủ ngữ HOẶC là câu mệnh lệnh/chỉ dẫn
        is_imperative = False
        if not has_subject:
            # Câu mệnh lệnh bắt đầu bằng từ chỉ dẫn hoặc động từ
            if tags[0][0].lower() in {"hãy", "đừng", "chớ", "nên", "cần", "vui lòng", "chủ động"}:
                is_imperative = True
            elif root_idx == 0:
                is_imperative = True
            elif len(tags) > 1 and tags[0][1] == "R" and tags[1][1] == "V": # Ví dụ: "rất thích" -> không phải mệnh lệnh, nhưng "hãy làm" -> R + V
                if tags[0][0].lower() in {"hãy", "nên", "cần", "vui lòng"}:
                    is_imperative = True
                    
        if not has_subject and not is_imperative:
            return False, "Câu thiếu chủ ngữ."
            
    return True, ""


def calculate_content_density(sentence: str) -> float:
    """
    Tính tỷ lệ từ mang nghĩa (N, V, A, M) / tổng số từ.
    Câu sáo rỗng thường có content density < 0.25.
    
    Returns: float từ 0.0 đến 1.0
    """
    _ensure_underthesea()
    if _pos_tag_fn is None:
        return 1.0  # Graceful fallback: không block
    
    plain = re.sub(r'<[^>]+>', ' ', sentence).strip()
    if not plain:
        return 1.0
    
    try:
        tags: list[tuple[str, str]] = _pos_tag_fn(plain)
    except Exception:
        return 1.0
    
    if not tags:
        return 1.0
    
    # Loại bỏ dấu câu khỏi tổng số
    non_punct = [(word, tag) for word, tag in tags if tag != "CH"]
    if not non_punct:
        return 1.0
    
    content_count = sum(1 for _, tag in non_punct if tag in CONTENT_POS_TAGS)
    return content_count / len(non_punct)


def detect_word_repetition(text: str, threshold: int = 3) -> list[str]:
    """
    Phát hiện các từ/cụm từ lặp lại quá nhiều trong 1 đoạn văn.
    
    Args:
        text: Đoạn văn cần kiểm tra
        threshold: Số lần lặp tối thiểu để coi là lỗi
    
    Returns: Danh sách các từ/cụm từ lặp quá nhiều
    """
    _ensure_underthesea()
    if _word_tokenize_fn is None:
        return []
    
    plain = re.sub(r'<[^>]+>', ' ', text).strip()
    if not plain:
        return []
    
    try:
        tokens: list[str] = _word_tokenize_fn(plain)
    except Exception:
        return []
    
    # Chuẩn hóa lowercase, bỏ dấu câu
    clean_tokens = [t.lower().strip() for t in tokens if t.strip() and not re.match(r'^[.,;:!?()"\'-]+$', t.strip())]
    
    if len(clean_tokens) < 10:
        return []  # Quá ngắn để phân tích lặp
    
    # Bigram analysis (cụm 2 từ liên tiếp)
    bigrams = [f"{clean_tokens[i]} {clean_tokens[i+1]}" for i in range(len(clean_tokens) - 1)]
    bigram_counts = Counter(bigrams)
    
    repeated: list[str] = []
    for gram, count in bigram_counts.most_common():
        if count >= threshold:
            # Bỏ qua các cụm quá ngắn hoặc chứa stopword thuần
            words_in_gram = gram.split()
            if all(len(w) <= 2 for w in words_in_gram):
                continue
            repeated.append(f"'{gram}' (lặp {count} lần)")
    
    return repeated


def analyze_sentence(sentence: str) -> dict[str, object]:
    """
    Phân tích tổng hợp một câu tiếng Việt.
    Trả về dict chứa tất cả kết quả phân tích.
    """
    is_complete, completeness_err = check_sentence_completeness(sentence)
    density = calculate_content_density(sentence)
    
    return {
        "is_complete": is_complete,
        "completeness_error": completeness_err,
        "content_density": density,
        "is_fluffy": density < 0.25,
    }
