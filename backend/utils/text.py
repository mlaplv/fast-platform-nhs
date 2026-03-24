import re
import unicodedata

# Phase 76.3: Pre-compiled regex for zero-allocation normalization
RE_CLEAN_VN = re.compile(r"[^a-z0-9\s]")

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
