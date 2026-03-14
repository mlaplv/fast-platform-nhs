"""
Heuristic Classifier — Zero-LLM Intent Classification.
======================================================
V56.0: Extracted from intent_orchestrator.py (Rule 1.3: <300 LOC per file).

Classifies clear-cut queries by keyword matching without any LLM call.
Returns None for ambiguous queries → falls through to T2 Dispatcher.
"""
import re
import logging
from typing import Optional

from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.utils.text import normalize_vn
from backend.services.xohi_memory import xohi_memory

logger = logging.getLogger("api-gateway")

# --- Pre-compiled Regex for Performance (V76.3) ---
RE_EMAIL = re.compile(r'[\w.-]+@[\w.-]+\.\w+')

# --- Keyword Dictionaries (avoid hardcode — centralized here for easy tuning) ---
TARGET_KEYWORDS = {
    "revenue": ["doanh thu", "doanh so", "bieu do", "tien", "doanh tu", "doanh thuu", "gianh thu", "danh thu", "dan thu"],
    "order":   ["don hang", "hoa don", "bill", "dau hang", "don han", "ton hang", "don hanh", "don hangg"],
    "product": ["san pham", "ton kho", "kho hang", "sang pham", "sam pham", "san phan", "san bam"],
    "user":    ["nguoi dung", "khach", "nhan vien", "tai khoan", "khach hang", "khach han", "cat hang"],
    "category": ["danh muc", "nhom hang", "loai hang"],
    "news":    ["tin tuc", "bai viet", "viet bai", "sang tac", "content", "bai dang"],
    "settings": ["cai dat", "setting", "cau hinh", "voice", "giong noi", "am thanh"],
}

MODE_KEYWORDS = {
    "viral": ["viral", "ngan", "nhanh", "tiktok", "facebook", "ngắn"],
    "deep_dive": ["sau", "phan tich", "chi tiet", "dai", "deep dive", "sâu", "phân tích", "dài"]
}

TIMEFRAME_KEYWORDS = {
    "today":      ["hom nay", "hom ni", "nay"],
    "this_month": ["thang nay", "thang ni"],
    "this_week":  ["tuan nay", "tuan ni"],
}

COUNT_KEYWORDS = ["bao nhieu", "may", "tong so", "tong", "thong ke", "chi tiet", "nao", "duoc khong", "het bao nhieu"]
QUESTION_KEYWORDS = ["co khong", "chua", "roi"]
MUTATE_KEYWORDS = ["them", "tao", "xoa", "sua", "update", "create", "delete"]

DELETE_KEYWORDS = ["xóa", "xoa", "delete", "bỏ", "bo", "hủy", "huy"]
EDIT_KEYWORDS = ["sửa", "sua", "edit", "update", "cập nhật", "cap nhat", "đổi", "doi"]

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
}

VI_VERB_MAP = {"create": "tạo", "edit": "sửa", "delete": "xóa"}
VI_TARGET_MAP = {"user": "nhân viên", "product": "sản phẩm", "category": "danh mục", "order": "đơn hàng", "news": "bài viết"}


# --- Phase 76.3: Pre-Normalized Keywords (Zero-Allocation) ---
NORM_TARGET_KEYWORDS = {tgt: [normalize_vn(kw) for kw in kws] for tgt, kws in TARGET_KEYWORDS.items()}
NORM_MODE_KEYWORDS = {mode: [normalize_vn(kw) for kw in kws] for mode, kws in MODE_KEYWORDS.items()}
NORM_TIMEFRAME_KEYWORDS = {tf: [normalize_vn(kw) for kw in kws] for tf, kws in TIMEFRAME_KEYWORDS.items()}
NORM_COUNT_KEYWORDS = [normalize_vn(kw) for kw in COUNT_KEYWORDS]
NORM_QUESTION_KEYWORDS = [normalize_vn(kw) for kw in QUESTION_KEYWORDS]
NORM_MUTATE_KEYWORDS = [normalize_vn(kw) for kw in MUTATE_KEYWORDS]

# Cached merged target keywords (static + dynamic)
_DYNAMIC_MERGE_CACHE = {} # { (user_id_or_system, mapping_hash): merged_dict }

def _merge_lists(a, b):
    # deduplicate list using set for O(1) lookups during merge
    res = list(a)
    seen = set(a)
    for x in b:
        if x not in seen:
            res.append(x)
            seen.add(x)
    return res

async def heuristic_classify(
    combined_lower: str,
    user_id: str,
    app_state: object,
    intent_map: Optional[dict] = None,
    norm_query: Optional[str] = None
) -> Optional[IntentResponse]:
    """
    Zero-LLM Heuristic Fallback — classify known patterns by keyword.
    Only handles clear-cut queries. Returns None for ambiguous ones.
    """
    # Phase 76.3: Reuse pre-normalized query from orchestrator
    if norm_query is None:
        norm_query = normalize_vn(combined_lower)

    # Fetch dynamic intent mapping from local memory (Sub-1ms)
    dynamic_mapping = intent_map if intent_map is not None else await xohi_memory.get_system_intent_mapping()

    # 76.3: Optimization - Cached Dynamic Merge
    # Create a stable key for the cache based on the mapping content
    map_hash = hash(str(dynamic_mapping)) if dynamic_mapping else 0
    cache_key = (user_id, map_hash)

    if dynamic_mapping:
        if cache_key in _DYNAMIC_MERGE_CACHE:
            merged_target_keywords = _DYNAMIC_MERGE_CACHE[cache_key]
        else:
            # Normalize and merge only once per mapping change
            merged_target_keywords = {**NORM_TARGET_KEYWORDS}
            for tgt, kws in dynamic_mapping.items():
                norm_kws = [normalize_vn(kw) for kw in kws]
                if tgt in merged_target_keywords:
                    merged_target_keywords[tgt] = _merge_lists(merged_target_keywords[tgt], norm_kws)
                else:
                    merged_target_keywords[tgt] = norm_kws

            # Prune cache if too large
            if len(_DYNAMIC_MERGE_CACHE) > 100:
                _DYNAMIC_MERGE_CACHE.clear()
            _DYNAMIC_MERGE_CACHE[cache_key] = merged_target_keywords
    else:
        merged_target_keywords = NORM_TARGET_KEYWORDS

    # --- Detect TARGET ---
    target = "none"
    for tgt, keywords in merged_target_keywords.items():
        # Using pre-normalized keywords and query
        if any(kw in norm_query for kw in keywords):
            target = tgt
            break

    if target == "none":
        return None

    # --- Detect TIMEFRAME ---
    timeframe = "none"
    for tf, keywords in NORM_TIMEFRAME_KEYWORDS.items():
        if any(kw in norm_query for kw in keywords):
            timeframe = tf
            break

    # ═══ TIMEFRAME & TARGET INHERITANCE (XoHi Next-Gen) ═══
    voice_cache = getattr(app_state, "voice_cache", {})
    user_profile = voice_cache.get(user_id, {})

    if target == "none" and timeframe != "none":
        target = user_profile.get("last_target", "none")
        logger.debug(f"[Heuristic] Inherited target: {target}")

    if timeframe == "none" and target in ["revenue", "order"]:
        timeframe = user_profile.get("last_timeframe", "none")
        logger.debug(f"[Heuristic] Inherited timeframe: {timeframe}")

    if target != "none":
        user_profile["last_target"] = target
    if timeframe != "none":
        user_profile["last_timeframe"] = timeframe
    voice_cache[user_id] = user_profile

    # --- Detect INTENT TYPE ---
    is_count = any(kw in norm_query for kw in NORM_COUNT_KEYWORDS)
    is_question = any(kw in norm_query for kw in NORM_QUESTION_KEYWORDS)
    is_mutate = any(kw in norm_query for kw in NORM_MUTATE_KEYWORDS)

    # --- Entity Extraction ---
    extracted_entities: dict = {}
    verb = "create"

    if is_mutate:
        if any(kw in combined_lower for kw in DELETE_KEYWORDS):
            verb = "delete"
        elif any(kw in combined_lower for kw in EDIT_KEYWORDS):
            verb = "edit"

        for marker in NAME_MARKERS:
            if marker in combined_lower:
                name_part = combined_lower.split(marker)[1].strip()
                for stop in NAME_STOP_WORDS:
                    if stop in name_part:
                        name_part = name_part.split(stop)[0].strip()
                extracted_entities["name"] = name_part.title()
                break

        email_match = RE_EMAIL.search(combined_lower)
        if email_match:
            extracted_entities["email"] = email_match.group(0)

    # --- Resolve intent type + action ---
    # 76.3: Use pre-normalized navigation keywords
    is_nav_explicit = any(kw in norm_query for kw in ["bieu do", "mo", "xem", "vao", "show"])

    # Rule R82.23: Content Factory Priority
    # 76.3: Use pre-normalized keywords for content factory
    is_content_factory = (target == "news" and (verb == "create" or "viet bai" in norm_query)) or any(kw in norm_query for kw in ["viet bai", "sang tac", "content"])

    content_mode = "viral"
    if is_content_factory:
        for mode, keywords in NORM_MODE_KEYWORDS.items():
            if any(kw in norm_query for kw in keywords):
                content_mode = mode
                break

    if is_content_factory:
        intent_type = "CONTENT_CREATE"
        action = IntentAction.CONTENT_CREATE
    elif is_mutate:
        intent_type = "MUTATE"
        action = IntentAction.MUTATE
    elif not is_nav_explicit and (is_count or is_question or (target != "none" and timeframe != "none") or target == "revenue"):
        intent_type = "DATA_QUERY"
        action = IntentAction.COUNT
    else:
        intent_type = "UI_NAV"
        action = IntentAction.READ

    # Rule R82.25: Decouple UI Actions from Data Queries
    # Only assign widget_id if it's explicitly a navigation request or certain navigation keywords are present
    is_nav_keywords = any(kw in norm_query for kw in ["mo ", "xem ", "vao ", "bieu do"])
    widget_id = TARGET_TO_WIDGET.get(target, "") if (intent_type == "UI_NAV" or is_nav_keywords) else ""

    # --- Build response message ---
    if intent_type == "MUTATE":
        v_label = VI_VERB_MAP.get(verb, verb)
        t_label = VI_TARGET_MAP.get(target, target)
        name = extracted_entities.get("name", "")
        response_msg = f"Sếp muốn {v_label} {t_label}" + (f' "{name}"' if name else "") + ". Xác nhận thông tin bên dưới ạ."
    elif intent_type == "UI_NAV":
        nav_msg_map = {
            "revenue":  "Dạ sếp, em mở biểu đồ doanh thu cho sếp ngay đây ạ.",
            "order":    "Dạ sếp, em mở quản lý đơn hàng cho sếp ngay đây ạ.",
            "product":  "Dạ sếp, em mở quản lý sản phẩm cho sếp ngay đây ạ.",
            "user":     "Dạ sếp, em mở danh sách nhân viên cho sếp ngay đây ạ.",
            "category": "Dạ sếp, em mở quản lý danh mục cho sếp ngay đây ạ.",
            "news":     "Dạ sếp, em mở quản lý bài viết cho sếp ngay đây ạ.",
            "settings": "Dạ sếp, em mở cài đặt giọng nói cho sếp ngay đây ạ.",
        }
        response_msg = nav_msg_map.get(target, "")
    else:
        response_msg = ""

    logger.debug(f"[Heuristic] Result: {intent_type} target={target} verb={verb} widget={widget_id} timeframe={timeframe}")
    
    res_data = {
        "intent_type": intent_type,
        "target": target,
        "verb": verb,
        "timeframe": timeframe,
        "content_mode": content_mode,
        "ui_action": widget_id,
        "entities": extracted_entities,
    }

    # Signal frontend to end conversation on navigation
    if intent_type == "UI_NAV":
        res_data["category"] = "SESSION_CTRL"
        res_data["action"] = "HARDWARE_SLEEP"

    return IntentResponse(
        status="success",
        action=action,
        message=response_msg,
        router_tier=RouterTier.TIER_1_HEURISTIC,
        cost_tokens=0.0,
        requires_confirmation=intent_type == "MUTATE",
        data=res_data,
    )
