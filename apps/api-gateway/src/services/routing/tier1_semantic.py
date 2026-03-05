# apps/api-gateway/src/services/routing/tier1_semantic.py
import difflib
import logging
from shared.schemas.intent import IntentResponse, IntentAction, RouterTier
from src.utils.text import normalize_vn

logger = logging.getLogger("api-gateway")

# T1 widget ID → frontend ACTION_WIDGET_MAP key
WIDGET_TO_ACTION = {
    "ORDER_MANAGEMENT": "show_order_management",
    "PRODUCT_MANAGEMENT": "show_product_management",
    "REVENUE_CHART": "show_revenue_chart",
    "NEWS_MANAGEMENT": "show_news_management",
    "USER_MANAGEMENT": "show_user_management",
}

WIDGET_VI_LABEL = {
    "ORDER_MANAGEMENT": "Đơn hàng",
    "PRODUCT_MANAGEMENT": "Sản phẩm",
    "REVENUE_CHART": "Biểu đồ Doanh thu",
    "NEWS_MANAGEMENT": "Tin tức",
    "USER_MANAGEMENT": "Người dùng",
}

# T1 widget ID → Data Injector target (for DB fetch)
WIDGET_TO_TARGET = {
    "ORDER_MANAGEMENT": "order",
    "PRODUCT_MANAGEMENT": "product",
    "REVENUE_CHART": "revenue",
    "NEWS_MANAGEMENT": "none",
    "USER_MANAGEMENT": "user",
}

class Tier1SemanticRouter:
    """
    Tier 1 Semantic Router (Zero-RAM V33.0 - Bulletproof Edition)
    =============================================================
    - Tích hợp Bypass Filter chặn đứng lỗi "so thang" vs "kho hang".
    - Exact Match ưu tiên tuyệt đối.
    - Fuzzy Match siết chặt 0.85.
    """
    def __init__(self):
        # Đã nạp lại đạn: Chứa cả từ chuẩn và các lỗi STT phổ biến (KHÔNG DẤU)
        self.intent_matrix = {
            "ORDER_MANAGEMENT": ["don hang", "don dat", "bill", "hoa don", "quan ly don", "dong hang"],
            "PRODUCT_MANAGEMENT": ["san pham", "mat hang", "kho hang", "quan ly san pham", "ton kho", "tong kho"],
            "REVENUE_CHART": ["doanh thu", "bao cao", "bieu do", "tien vo", "thu nhap", "doanh so", "dan so"],
            "NEWS_MANAGEMENT": ["tin tuc", "quan ly tin tuc", "bang tin", "tin moi"],
            "USER_MANAGEMENT": ["nguoi dung", "quan ly nguoi dung", "tai khoan", "nguoi sai", "tai khoang"]
        }
        
        self.keyword_to_widget = {}
        self.all_keywords = []
        for widget_id, keywords in self.intent_matrix.items():
            for kw in keywords:
                self.keyword_to_widget[kw] = widget_id
                self.all_keywords.append(kw)

    def catch_basic_commands(self, clean_text: str, user_id: str, app_state: object) -> IntentResponse | None:
        # R1.11: GLOBAL SYSTEM WAKE WORD — check "xohi" TRƯỚC, KHÔNG phụ thuộc user_id
        DEFAULT_GREETING = "Dạ, em nghe đây sếp."
        
        voice_cache = app_state["voice_cache"] if isinstance(app_state, dict) else getattr(app_state, "voice_cache", {})
        user_profile = voice_cache.get(user_id) if user_id else None
        
        wake_words = user_profile.get("wake_words", []) if user_profile else []
        sleep_words = user_profile.get("sleep_words", []) if user_profile else []
        greeting_template = user_profile.get("greeting_template", DEFAULT_GREETING) if user_profile else DEFAULT_GREETING

        # BẮT BUỘC: Thêm 'xohi' làm wake word mặc định toàn hệ thống
        system_wake_words = list(set(wake_words + ["xohi"]))
        
        logger.info(f"[T1 Wake] clean_text='{clean_text}', user_id={user_id}, wake_words={system_wake_words}")
        
        for word in system_wake_words:
            if word in clean_text or difflib.SequenceMatcher(None, clean_text, word).ratio() > 0.8:
                logger.info(f"[T1 Wake] MATCHED wake word '{word}'")
                return IntentResponse(status="success", action=IntentAction.READ, message=greeting_template, router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "SESSION_CTRL", "action": "WAKE_ROUTINE", "confidence": 1.0}, cost_tokens=0.0)

        for word in sleep_words:
            if word in clean_text or difflib.SequenceMatcher(None, clean_text, word).ratio() > 0.8:
                return IntentResponse(status="success", action=IntentAction.READ, message="Hẹn gặp lại sếp.", router_tier=RouterTier.TIER_1_HEURISTIC, data={"category": "SESSION_CTRL", "action": "HARDWARE_SLEEP", "confidence": 1.0}, cost_tokens=0.0)
        return None

    def route(self, transcript: str, user_id: str, app_state: object) -> IntentResponse | None:
        # R1.8: Anti-Blocking — Truncate input to protect CPU from O(n²) fuzzy matching
        transcript = transcript[:500]

        # 1. Chuẩn hóa cơ bản (chỉ lowercase + bỏ dấu, KHÔNG lọc stop words) để check bypass
        # Điều này quan trọng vì "nay", "nao" ... có thể là stop words nhưng lại cần để bypass T1
        import unicodedata
        import re
        
        raw_clean = unicodedata.normalize("NFC", transcript)
        raw_clean = raw_clean.replace("đ", "d").replace("Đ", "D")
        raw_clean = unicodedata.normalize("NFD", raw_clean)
        raw_clean = "".join(c for c in raw_clean if unicodedata.category(c) != "Mn")
        raw_clean = raw_clean.lower()
        raw_clean = re.sub(r"[^a-z0-9\s]", "", raw_clean).strip()

        # BYPASS FILTER: Nhường quyền cho Tier 2 nếu có từ khóa thống kê hoặc từ hỏi phức tạp
        # TUY NHIÊN: Nếu lệnh bắt đầu bằng "mở" hoặc "xem" + keyword T1 -> Ưu tiên UI_NAV ngay
        bypass_keywords = [
            "bao nhieu", "thang nay", "hom nay", "tong", 
            "chua xu ly", "nao", "co khong",
            "tao ", "them ", "xoa ", "sua ", "cap nhat", "doi ", "xac nhan"
        ]
        
        is_explicit_open = raw_clean.startswith(("mo ", "xem ", "show "))
        
        if any(kw in raw_clean for kw in bypass_keywords) and not is_explicit_open:
            logger.info(f"[T1] Bypass Filter triggered for '{raw_clean}', delegating to T2")
            return None

        # 2. Chuẩn hóa kịch liệt (có lọc stop words) để match widget chính xác
        clean_text = normalize_vn(transcript).lower().strip()

        basic_match = self.catch_basic_commands(clean_text, user_id, app_state)
        if basic_match: return basic_match

        # 1. 🎯 EXACT MATCH: ƯU TIÊN SỐ 1 (Độ trễ 0ms)
        for widget_id, keywords in self.intent_matrix.items():
            for kw in keywords:
                if kw in clean_text:
                    ui_action = WIDGET_TO_ACTION.get(widget_id, "")
                    vi_label = WIDGET_VI_LABEL.get(widget_id, widget_id)
                    logger.info(f"[T1] Exact Match: {widget_id} → {ui_action} (Keyword: '{kw}')")
                    return IntentResponse(
                        status="success", action=IntentAction.READ,
                    data={"matched_query": kw, "confidence": 1.0, "ui_action": ui_action, "intent_type": "UI_NAV", "target": WIDGET_TO_TARGET.get(widget_id, "none"), "timeframe": "none"},
                        message=f"Dạ, em mở {vi_label} cho sếp.",
                        router_tier=RouterTier.TIER_1_HEURISTIC, cost_tokens=0.0
                    )

        # 3. ✂️ N-GRAMS FUZZY MATCH (Dynamic Size)
        words = clean_text.split()
        chunks = []

        # Tính độ dài từ khóa lớn nhất trong từ điển
        max_kw_len = max((len(kw.split()) for kw in self.all_keywords), default=4)

        # Tạo chunks từ size 2 đến max_kw_len
        for size in range(2, max_kw_len + 1):
            for i in range(len(words) - size + 1):
                chunks.append(" ".join(words[i:i+size]))

        if 0 < len(words) <= max_kw_len:
            chunks.append(clean_text)

        best_score = 0.0
        best_widget = None
        best_kw = None

        for chunk in chunks:
            # SIẾT CHẶT CUTOFF LÊN 0.85 (Khóa mõm lỗi 0.75)
            matches = difflib.get_close_matches(chunk, self.all_keywords, n=1, cutoff=0.85)
            if matches:
                matched_kw = matches[0]
                score = difflib.SequenceMatcher(None, chunk, matched_kw).ratio()
                if score > best_score:
                    best_score = score
                    best_kw = matched_kw
                    best_widget = self.keyword_to_widget[matched_kw]

        if best_widget:
            ui_action = WIDGET_TO_ACTION.get(best_widget, "")
            vi_label = WIDGET_VI_LABEL.get(best_widget, best_widget)
            logger.info(f"[T1] N-gram Match: {best_widget} → {ui_action} (Score: {best_score:.2f}, Keyword: '{best_kw}')")
            return IntentResponse(
                status="success", action=IntentAction.READ,
                data={"matched_query": best_kw, "confidence": best_score, "ui_action": ui_action, "intent_type": "UI_NAV", "target": WIDGET_TO_TARGET.get(best_widget, "none"), "timeframe": "none"},
                message=f"Dạ, em mở {vi_label} cho sếp.",
                router_tier=RouterTier.TIER_1_HEURISTIC, cost_tokens=0.0
            )    
        return None