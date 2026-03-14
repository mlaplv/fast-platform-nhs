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
