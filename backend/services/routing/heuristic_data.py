import re
from backend.utils.text import normalize_vn

# --- Pre-compiled Regex for Performance (V76.3) ---
RE_EMAIL = re.compile(r'[\w.-]+@[\w.-]+\.\w+')
RE_LEARN_1 = re.compile(r"hoc lenh ['\"]?(.+?)['\"]? la (.+)", re.IGNORECASE)
RE_LEARN_2 = re.compile(r"hoc ['\"]?(.+?)['\"]? la (.+)", re.IGNORECASE)
RE_LEARN_3 = re.compile(r"day lenh ['\"]?(.+?)['\"]? la (.+)", re.IGNORECASE)
RE_LEARN_VN_1 = re.compile(r"học lệnh ['\"]?(.+?)['\"]? là (.+)", re.IGNORECASE)
RE_LEARN_VN_2 = re.compile(r"học ['\"]?(.+?)['\"]? là (.+)", re.IGNORECASE)
RE_LEARN_VN_3 = re.compile(r"dạy lệnh ['\"]?(.+?)['\"]? là (.+)", re.IGNORECASE)

# --- Keyword Dictionaries ---
TARGET_KEYWORDS = {
    "revenue": ["doanh thu", "doanh so", "bieu do", "tien", "doanh tu", "doanh thuu", "gianh thu", "danh thu", "dan thu", "bi do", "bi do"],
    "order":   ["don hang", "hoa don", "bill", "dau hang", "don han", "ton hang", "don hanh", "don hangg"],
    "product": ["san pham", "ton kho", "kho hang", "sang pham", "sam pham", "san phan", "san bam"],
    "user":    ["nguoi dung", "khach", "nhan vien", "tai khoan", "khach hang", "khach han", "cat hang"],
    "category": ["danh muc", "nhom hang", "loai hang"],
    "news":    ["tin tuc", "bai viet", "viet bai", "sang tac", "content", "bai dang"],
    "settings": ["cai dat", "setting", "cau hinh", "voice", "giong noi", "am thanh", "skills", "ky nang"],
    "campaign": ["campaign", "chien dich", "chien dichh", "chien dichx", "camp", "canh pain", "cam pain"],
    "brain":    ["brain", "nao", "tri thuc", "quan tri nao", "helen brain", "bo nao"],
    "voucher":  ["voucher", "khuyen mai", "ma giam gia", "km", "vou che", "voucher"],
    "ads_protection": ["quang cao", "ads protection", "click tac", "click fraud", "bao cao", "phap y", "report ads", "báo cáo", "quảng cáo", "bao cao info"],
    "video_script": ["kich ban video", "kich ban", "script video", "video script", "kich ban marketing", "quản lý kịch bản", "kich ban video marketing"],
}

MODE_KEYWORDS = {
    "viral": ["viral", "ngan", "nhanh", "tiktok", "facebook", "ngắn"],
    "deep_dive": ["sau", "phan tich", "chi tiet", "dai", "deep dive", "sâu", "phân tích", "dài"],
    "normal": ["thuong", "binh thuong", "stock", "regular", "thường", "bình thường"]
}

TIMEFRAME_KEYWORDS = {
    "today":      ["hom nay", "hom ni", "nay"],
    "this_month": ["thang nay", "thang ni"],
    "this_week":  ["tuan nay", "tuan ni"],
}

COUNT_KEYWORDS = ["bao nhieu", "may", "tong so", "tong", "thong ke", "chi tiet", "nao", "duoc khong", "het bao nhieu"]
LEARN_KEYWORDS = ["hoc lenh", "day lenh", "nho la", "hoc la", "hoc lan"]
QUESTION_KEYWORDS = ["co khong", "chua", "roi"]
MUTATE_KEYWORDS = ["them", "tao", "xoa", "sua", "update", "create", "delete"]
DELETE_KEYWORDS = ["xóa", "xoa", "delete", "bỏ", "bo", "hủy", "huy"]
EDIT_KEYWORDS = ["sửa", "sua", "edit", "update", "cập nhật", "cap nhat", "đổi", "doi"]
GREETING_KEYWORDS = ["ban oi", "oi", "hello", "hi", "xin chao", "chao ban", "em oi", "xohi", "xo hi", "so hi", "ban", "anh oi", "chi oi", "hey"]

NAME_MARKERS = ["tên là ", "ten la ", "tên ", "ten "]
NAME_STOP_WORDS = ["email", "mật khẩu", "vai trò", "giá", "mô tả"]

TARGET_TO_WIDGET = {
    "revenue":  "show_revenue_chart",
    "order":    "show_order_management",
    "product":  "show_product_management",
    "user":     "show_user_management",
    "category": "show_category_management",
    "news":     "show_news_management",
    "settings": "show_voice_settings",
    "campaign": "show_campaigns",
    "brain":    "show_brain",
    "voucher":  "show_voucher_management",
    "ads_protection": "show_ads_protection",
    "video_script": "show_video_script_management",
}

VI_VERB_MAP = {"create": "tạo", "edit": "sửa", "delete": "xóa"}
VI_TARGET_MAP = {"user": "nhân viên", "product": "sản phẩm", "category": "danh mục", "order": "đơn hàng", "news": "bài viết", "campaign": "chiến dịch", "brain": "brain", "voucher": "voucher", "ads_protection": "quảng cáo", "video_script": "kịch bản video"}

# --- Phase 76.3: Pre-Normalized Keywords ---
NORM_TARGET_KEYWORDS = {tgt: [normalize_vn(kw) for kw in kws] for tgt, kws in TARGET_KEYWORDS.items()}
NORM_MODE_KEYWORDS = {mode: [normalize_vn(kw) for kw in kws] for mode, kws in MODE_KEYWORDS.items()}
NORM_TIMEFRAME_KEYWORDS = {tf: [normalize_vn(kw) for kw in kws] for tf, kws in TIMEFRAME_KEYWORDS.items()}
NORM_COUNT_KEYWORDS = [normalize_vn(kw) for kw in COUNT_KEYWORDS]
NORM_QUESTION_KEYWORDS = [normalize_vn(kw) for kw in QUESTION_KEYWORDS]
NORM_LEARN_KEYWORDS = [normalize_vn(kw) for kw in LEARN_KEYWORDS]
NORM_MUTATE_KEYWORDS = [normalize_vn(kw) for kw in MUTATE_KEYWORDS]
NORM_NAV_EXPLICIT = {normalize_vn(kw) for kw in ["bieu do", "mo", "xem", "vao", "show"]}
NORM_CONTENT_FACTORY = {normalize_vn(kw) for kw in ["viet bai", "sang tac", "content", "tao san pham"]}
NORM_GREETING_KEYWORDS = {normalize_vn(kw) for kw in GREETING_KEYWORDS}
