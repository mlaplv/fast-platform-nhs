import re
import unicodedata


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
    text = re.sub(r"[^a-z0-9\s]", "", text)

    return " ".join(text.split()).strip()
