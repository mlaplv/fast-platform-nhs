import logging
from backend.utils.text import normalize_vn

logger = logging.getLogger("api-gateway")

NAV_PATTERNS = {
    "mo bieu do", "xem bieu do", "doanh so thang nay", "doanh thu hom nay",
    "xem don hang", "danh sach san pham", "ok", "dung", "vang", "phai", "thoat",
    "mo danh muc", "vao danh muc", "mo tin tuc", "vao tin tuc", "mo cai dat",
    "chao", "xin chao", "tam biet", "bye", "hẹn gặp lại"
}
NORM_NAV_PATTERNS = {normalize_vn(p) for p in NAV_PATTERNS}

SOUND_ALIKES = {
    "dân số": "doanh số",
    "nhân số": "doanh số",
    "doanh tu": "doanh thu",
    "đau hàng": "đơn hàng",
    "sang phẩm": "sản phẩm",
    "số hi": "xohi",
    "xố hỉ": "xohi",
    "số huy": "xohi",
    "so huy": "xohi",
    "học lần": "học lệnh",
    "học lẹ": "học lệnh",
    "chương dịch": "chiến dịch",
    "bí đồ": "biểu đồ",
    "bi đồ": "biểu đồ",
    "dan so": "doanh số",
    "doanh so": "doanh số",
    "hang hoa": "hàng hóa",
    "don hang": "đơn hàng",
    "san pham": "sản phẩm",
}
NORM_SOUND_ALIKES = {normalize_vn(k): v for k, v in SOUND_ALIKES.items()}

# Global normalization cache to avoid redundant calls to normalize_vn (V76.3)
_GLOBAL_NORM_CACHE = {} 

def get_norm(text: str) -> str:
    if text not in _GLOBAL_NORM_CACHE:
        if len(_GLOBAL_NORM_CACHE) > 1000: _GLOBAL_NORM_CACHE.clear()
        _GLOBAL_NORM_CACHE[text] = normalize_vn(text)
    return _GLOBAL_NORM_CACHE[text]
