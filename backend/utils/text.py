import re
import unicodedata

# Phase 76.3: Pre-compiled regex for zero-allocation normalization
RE_CLEAN_VN = re.compile(r"[^a-z0-9\s]")

# ── Module-level constants ──────────────────────────────────────────────
# CamelCase brand exceptions: tránh tách PubMed → Pub Med
_CAMEL_EXCEPTIONS: dict[str, str] = {
    "Pub Med": "PubMed",
    "Science Direct": "ScienceDirect",
    "Chat Gpt": "ChatGPT",
    "Chat GPT": "ChatGPT",
    "You Tube": "YouTube",
    "Git Hub": "GitHub",
    "App Store": "AppStore",
    "Play Store": "PlayStore",
    "Web P": "WebP",
    "Base Model": "BaseModel",
    "Svelte Kit": "SvelteKit",
    "Type Script": "TypeScript",
    "Java Script": "JavaScript",
}

def normalize_vn(text: str) -> str:
    """
    Chuẩn hóa văn bản tiếng Việt cho wake/sleep word matching:
    1. NFC → xử lý Đ/đ → NFD → bỏ dấu → lowercase
    2. Xóa ký tự đặc biệt (giữ a-z, 0-9, space)
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = RE_CLEAN_VN.sub("", text)

    return " ".join(text.split()).strip()

def slugify(text: str) -> str:
    """
    Tạo slug từ văn bản tiếng Việt.
    """
    if not text:
        return ""

    text = normalize_vn(text)
    return text.replace(" ", "-")

def sanitize_id(id_val: str | None) -> str | None:
    """
    R105: Standardize ID logic - strips legacy 'undefined' or 'null' strings
    and empty whitespace to prevent DB leakage.
    """
    if id_val is None:
        return None

    if not isinstance(id_val, str):
        return str(id_val)

    s = id_val.strip()
    if not s or s.lower() in ("undefined", "null", "none"):
        return None

    return s

def to_int(val: object, default: int = 0) -> int:
    """
    Robust integer parsing: handles "~500", "500+", "approx 500", etc.
    Extracts the first numeric sequence found in the string.
    """
    if val is None: return default
    if isinstance(val, int): return val
    try:
        s = str(val).strip()
        m = re.search(r'\d+', s)
        if m:
            return int(m.group())
        return default
    except (ValueError, TypeError):
        return default

def extract_readable_text(content: str) -> str:
    """
    If content is a JSON string, parses it and recursively extracts all string values
    into a single plain text string. Useful for AI operatives analyzing structured data.
    If it's not JSON, returns the original string.
    """
    if not content or not isinstance(content, str):
        return content or ""
        
    content_stripped = content.strip()
    if not (content_stripped.startswith("{") and content_stripped.endswith("}")):
        return content

    import json
    try:
        data = json.loads(content_stripped)
        
        def _extract_strings(obj: object) -> list[str]:
            if isinstance(obj, str):
                return [obj]
            elif isinstance(obj, dict):
                res = []
                for v in obj.values():
                    res.extend(_extract_strings(v))
                return res
            elif isinstance(obj, list):
                res = []
                for item in obj:
                    res.extend(_extract_strings(item))
                return res
            return []
            
        strings = _extract_strings(data)
        return "\n\n".join(strings)
    except Exception:
        return content

def is_json(content: str) -> bool:
    if not content or not isinstance(content, str):
        return False
    content_stripped = content.strip()
    if not (content_stripped.startswith("{") and content_stripped.endswith("}")):
        return False
    import json
    try:
        json.loads(content_stripped)
        return True
    except Exception:
        return False

def normalize_vietnamese_encoding(text: str) -> str:
    """
    Chuẩn hóa font chữ tiếng Việt sang NFC để tránh lỗi hiển thị/lỗi font,
    và tự động bổ sinh khoảng trắng hợp lý giữa các ranh giới từ bị dính liền.
    """
    if not text:
        return text
    # 1. Chuẩn hóa sang NFC
    text = unicodedata.normalize("NFC", text)
    
    # 2. Thêm khoảng trắng giữa chữ thường và chữ hoa (ví dụ: bìThấp -> bì Thấp)
    text = re.sub(
        r'([a-zâăêơưđàáảãạằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ])([A-ZÂĂÊƠƯĐÀÁẢÃẠẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ])',
        r'\1 \2',
        text
    )
    
    # 2b. Khôi phục các danh từ riêng/nhãn hiệu chuẩn CamelCase (tránh lỗi PubMed -> Pub Med)
    for split_val, orig_val in _CAMEL_EXCEPTIONS.items():
        text = text.replace(split_val, orig_val)
    
    # 3. Thêm khoảng trắng sau dấu đóng ngoặc nếu dính liền chữ/số (ví dụ: (PubMed, 2018)Sodium -> (PubMed, 2018) Sodium)
    text = re.sub(
        r'([\)\]\}])([a-zA-Z0-9âăêơưđÂĂÊƠƯĐàáảãạằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ])',
        r'\1 \2',
        text
    )
    
    # 4. Thêm dấu cách sau dấu % nếu viết liền với chữ/số (ví dụ: 31.4%là -> 31.4% là)
    text = re.sub(r'(\d+(?:\.\d+)?%)(\w)', r'\1 \2', text)
    
    # 5. Thêm dấu cách sau số nếu viết liền với chữ tiếng Việt (ví dụ: 4tuần -> 4 tuần)
    text = re.sub(
        r'(\d+)([a-zA-ZâăêơưđÂĂÊƠƯĐàáảãạằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ])',
        r'\1 \2',
        text
    )
    
    # 6. Thêm dấu cách trước số/phần trăm nếu viết liền sau chữ tiếng Việt (ví dụ: lệ31.4% -> lệ 31.4%)
    text = re.sub(
        r'([a-zA-ZâăêơưđÂĂÊƠƯĐàáảãạằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ])(\d+)',
        r'\1 \2',
        text
    )
    return text

def sanitize_sentence_linebreaks(text: str) -> str:
    """
    Tách dòng và khoảng trắng dư thừa trong câu để tránh lỗi ngắt dòng giữa chừng.
    """
    if not text:
        return text
    text = normalize_vietnamese_encoding(text)
    # Thay thế các ký tự xuống dòng bằng khoảng trắng
    text = re.sub(r'[\r\n]+', ' ', text)
    # Thu gọn nhiều khoảng trắng liên tiếp
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def validate_vietnamese_sentence(text: str, mode: str = "standard") -> str:
    """
    TRÙM CUỐI: Vietnamese Elite NLP Guard.
    Kiểm tra tính hoàn chỉnh về mặt ngữ nghĩa của câu tiếng Việt.
    
    Modes:
    - "light": Chỉ Tầng 1 (Structural Guard) — dùng cho fast path / content dài
    - "standard": Tầng 1 + 2 (Structural + Linguistic) — mặc định
    - "full": Tầng 1 + 2 + 3 (+ Neural Spell) — dùng cho final publish
    """
    if not text:
        return text

    # ═══ TẦNG 1: STRUCTURAL GUARD (Regex) ═══════════════════════════════
    text = normalize_vietnamese_encoding(text)
    # Loại bỏ các thẻ HTML để lấy nội dung text thuần để kiểm tra
    raw_text = re.sub(r'<[^>]+>', ' ', text).strip()
    if not raw_text:
        return text

    # 1. Kiểm tra ngắt dòng
    if "\n" in raw_text or "\r" in raw_text:
        raise ValueError("Tuyệt đối không được ngắt dòng khi chưa viết hết câu.")

    # Loại bỏ khoảng trắng thừa
    raw_text = " ".join(raw_text.split())

    incomplete_endings = {
        "và", "hoặc", "như", "của", "với", "là", "bởi", "trong", "trên", "dưới", "tại", "cho", "vì", 
        "nên", "thì", "mà", "để", "nhưng", "tuy", "bằng", "về"
    }

    # Lấy các từ dạng chữ bằng regex
    words = [w.strip() for w in re.findall(r'\b\w+\b', raw_text.lower(), re.UNICODE)]
    if not words:
        return text

    last_word = words[-1]
    if last_word in incomplete_endings:
        raise ValueError(f"Câu bị viết thiếu nghĩa, kết thúc lửng lơ bằng từ nối '{last_word}'.")

    # 3. Kiểm tra cụm từ vô nghĩa hoặc lỗi diễn đạt cụ thể (như 'có như cao?')
    bad_patterns = [
        r'\bcó như cao\b',
        r'\bnhư cao\?$',
        r'\bnhư cao\.$',
        r'\bnhư cáo\b',
        r'\btên gọi cáo\b',
        r'\blà một trong những\s*$',
        r'\bđược đánh giá là\s*$'
    ]
    for pattern in bad_patterns:
        if re.search(pattern, raw_text.lower(), re.UNICODE):
            raise ValueError("Lời văn thiếu nghĩa hoặc chứa lỗi diễn đạt ngớ ngẩn (ví dụ: 'có như cao', 'như cáo', 'tên gọi cáo').")

    # 4. Kiểm tra câu quá ngắn / thiếu thành phần cơ bản
    # Một câu tiếng Việt hoàn chỉnh thường có ít nhất 3 từ (ví dụ: "Nó rất tốt.", "Sản phẩm tốt.")
    if len(words) < 3:
        raise ValueError("Câu quá ngắn, thiếu thành phần chủ ngữ hoặc vị ngữ để tạo thành ý nghĩa hoàn chỉnh.")

    # Bỏ qua kiểm tra ngữ pháp (Tầng 2) nếu chuỗi chứa bảng dữ liệu hoặc hình ảnh có cấu trúc
    is_structured = any(tag in text.lower() for tag in ["<table", "<figure", "<blockquote", "xohi-clinical-table"])

    # ═══ TẦNG 2: LINGUISTIC ANALYZER (underthesea) ══════════════════════
    if mode in ("standard", "full") and not is_structured:
        try:
            from backend.utils.vietnamese_nlp import (
                check_sentence_completeness,
                calculate_content_density,
            )
            is_valid, err = check_sentence_completeness(raw_text)
            if not is_valid:
                raise ValueError(err)

            density = calculate_content_density(raw_text)
            if density < 0.20:
                raise ValueError(
                    f"Câu có mật độ nội dung quá thấp ({density:.0%}), có dấu hiệu sáo rỗng."
                )
        except ValueError:
            raise  # Re-raise validation errors
        except Exception:
            pass  # Graceful fallback: nếu underthesea lỗi thì bỏ qua

    # ═══ TẦNG 3: NEURAL SPELL CORRECTOR (BARTpho) ═══════════════════════
    if mode == "full":
        try:
            from backend.utils.spell_corrector import VietnameseSpellCorrector
            corrector = VietnameseSpellCorrector.get_instance()
            corrected, changes = corrector.correct(text)
            if changes:
                text = corrected
        except Exception:
            pass  # Graceful fallback

    return text

def validate_vietnamese_text_block(text: str, mode: str = "light") -> str:
    """
    Kiểm tra toàn bộ khối văn bản (nhiều dòng, nhiều đoạn văn) chuẩn Elite Protocol.
    Mặc định dùng mode="light" để tránh chậm trên content dài.
    """
    if not text:
        return text

    text = normalize_vietnamese_encoding(text)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue

        # 1. Kiểm tra ngắt dòng giữa chừng (premature line break)
        if i < len(lines) - 1:
            next_line = lines[i+1].strip()
            if next_line:
                # Dòng hiện tại kết thúc bằng chữ hoặc số bình thường (không phải dấu câu kết thúc)
                if line_clean[-1].isalnum():
                    # Dòng tiếp theo bắt đầu bằng chữ thường
                    if next_line[0].islower():
                        raise ValueError("Tuyệt đối không được ngắt dòng khi chưa viết hết câu.")

        # Tách các câu trong dòng để kiểm thử từng câu
        sentences = re.split(r'(?<=[.!?])\s+', line_clean)
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue
            # Bỏ qua các định dạng đặc biệt (tiêu đề, list, bảng, HTML)
            if (sentence_clean.startswith("#") or 
                sentence_clean.startswith("*") or 
                sentence_clean.startswith("-") or 
                re.match(r'^\d+\.', sentence_clean) or
                "|" in sentence_clean or
                (sentence_clean.startswith("<") and sentence_clean.endswith(">"))):
                continue
                
            validate_vietnamese_sentence(sentence_clean, mode=mode)
            
    return text
