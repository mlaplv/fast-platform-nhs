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
RE_LEARN_1 = re.compile(r"hoc lenh ['\"]?(.+?)['\"]? la (.+)", re.IGNORECASE)
RE_LEARN_2 = re.compile(r"hoc ['\"]?(.+?)['\"]? la (.+)", re.IGNORECASE)
RE_LEARN_3 = re.compile(r"day lenh ['\"]?(.+?)['\"]? la (.+)", re.IGNORECASE)
RE_LEARN_VN_1 = re.compile(r"học lệnh ['\"]?(.+?)['\"]? là (.+)", re.IGNORECASE)
RE_LEARN_VN_2 = re.compile(r"học ['\"]?(.+?)['\"]? là (.+)", re.IGNORECASE)
RE_LEARN_VN_3 = re.compile(r"dạy lệnh ['\"]?(.+?)['\"]? là (.+)", re.IGNORECASE)

# --- Keyword Dictionaries (avoid hardcode — centralized here for easy tuning) ---
TARGET_KEYWORDS = {
    "revenue": ["doanh thu", "doanh so", "bieu do", "tien", "doanh tu", "doanh thuu", "gianh thu", "danh thu", "dan thu", "bi do", "bi do"],
    "order":   ["don hang", "hoa don", "bill", "dau hang", "don han", "ton hang", "don hanh", "don hangg"],
    "product": ["san pham", "ton kho", "kho hang", "sang pham", "sam pham", "san phan", "san bam"],
    "user":    ["nguoi dung", "khach", "nhan vien", "tai khoan", "khach hang", "khach han", "cat hang"],
    "category": ["danh muc", "nhom hang", "loai hang"],
    "news":    ["tin tuc", "bai viet", "viet bai", "sang tac", "content", "bai dang"],
    "settings": ["cai dat", "setting", "cau hinh", "voice", "giong noi", "am thanh"],
    "campaign": ["campaign", "chien dich", "chien dichh", "chien dichx", "camp", "canh pain", "cam pain"],
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
}

VI_VERB_MAP = {"create": "tạo", "edit": "sửa", "delete": "xóa"}
VI_TARGET_MAP = {"user": "nhân viên", "product": "sản phẩm", "category": "danh mục", "order": "đơn hàng", "news": "bài viết", "campaign": "chiến dịch"}


# --- Phase 76.3: Pre-Normalized Keywords (Zero-Allocation) ---
NORM_TARGET_KEYWORDS = {tgt: [normalize_vn(kw) for kw in kws] for tgt, kws in TARGET_KEYWORDS.items()}
NORM_MODE_KEYWORDS = {mode: [normalize_vn(kw) for kw in kws] for mode, kws in MODE_KEYWORDS.items()}
NORM_TIMEFRAME_KEYWORDS = {tf: [normalize_vn(kw) for kw in kws] for tf, kws in TIMEFRAME_KEYWORDS.items()}
NORM_COUNT_KEYWORDS = [normalize_vn(kw) for kw in COUNT_KEYWORDS]
NORM_QUESTION_KEYWORDS = [normalize_vn(kw) for kw in QUESTION_KEYWORDS]
NORM_LEARN_KEYWORDS = [normalize_vn(kw) for kw in LEARN_KEYWORDS]
NORM_MUTATE_KEYWORDS = [normalize_vn(kw) for kw in MUTATE_KEYWORDS]

# Navigation & Content Factory Pre-normalized (Zero-Allocation)
NORM_NAV_EXPLICIT = {normalize_vn(kw) for kw in ["bieu do", "mo", "xem", "vao", "show"]}
NORM_CONTENT_FACTORY = {normalize_vn(kw) for kw in ["viet bai", "sang tac", "content"]}

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
    context: Optional[dict] = None,
    intent_map: Optional[dict] = None,
    norm_query: Optional[str] = None
) -> Optional[IntentResponse]:
    """
    Zero-LLM Heuristic Fallback — classify known patterns by keyword.
    Only handles clear-cut queries. Returns None for ambiguous ones.
    """
    # Phase 76.4: Use persistent context from xohi_memory
    ctx = context if context is not None else {}

    # Phase 76.3: Reuse pre-normalized query from orchestrator
    if norm_query is None:
        norm_query = normalize_vn(combined_lower)

    # Fetch dynamic intent mapping from local memory (Sub-1ms)
    dynamic_mapping = intent_map if intent_map is not None else await xohi_memory.get_system_intent_mapping()

    # --- Phase 77.2: Learn Command Heuristic (Priority) ---
    if any(kw in norm_query for kw in NORM_LEARN_KEYWORDS):
        logger.info(f"[Heuristic] Learn Command detected: '{norm_query}'")
        
        learn_kw = ""
        learn_tgt = ""
        
        # Try Regex Extraction (V77.3)
        # Check normalized first for reliability, but extract from combined_lower if possible for clarity
        for reg in [RE_LEARN_VN_1, RE_LEARN_VN_2, RE_LEARN_VN_3]:
            match = reg.search(combined_lower)
            if match:
                learn_kw = match.group(1).strip().strip("'\"")
                learn_tgt = match.group(2).strip().strip("'\"")
                break
        
        if not learn_kw: # Fallback to normalized regex
            for reg in [RE_LEARN_1, RE_LEARN_2, RE_LEARN_3]:
                match = reg.search(norm_query)
                if match:
                    learn_kw = match.group(1).strip()
                    learn_tgt = match.group(2).strip()
                    break

        return IntentResponse(
            status="success",
            action=IntentAction.MUTATE,
            message="",
            router_tier=RouterTier.TIER_1_HEURISTIC,
            data={
                "intent_type": "LEARN_COMMAND",
                "target": "none",
                "learn_keyword": learn_kw,
                "learn_target": learn_tgt
            }
        )

    # --- Phase 77: Direct Command Mapping (Dynamic Zen Path) ---
    if dynamic_mapping:
        for cmd, widget in dynamic_mapping.items():
            if isinstance(widget, str) and (widget.startswith("show_") or widget.isupper()): # Support both show_ and WidgetType (CAMPAIGNS)
                norm_cmd = normalize_vn(cmd)
                if norm_cmd in norm_query:
                    logger.info(f"[Heuristic] Direct Command Match: '{cmd}' -> {widget}")
                    
                    # Phase 77.1: Intelligent Action Mapping
                    intent_type = "UI_NAV"
                    ui_action = ""
                    category = "SESSION_CTRL" if widget in ["HARDWARE_SLEEP", "WAKE_ROUTINE"] else "UI_NAV"
                    action_val = widget if widget in ["HARDWARE_SLEEP", "WAKE_ROUTINE"] else ""
                    response_msg = f"Dạ sếp, em mở {cmd} cho sếp ngay đây ạ."

                    if widget == "HARDWARE_SLEEP":
                        intent_type = "SESSION_CTRL"
                        response_msg = "Hẹn gặp lại sếp."
                    elif widget == "WAKE_ROUTINE":
                        intent_type = "SESSION_CTRL"
                        # Proactive greeting from Profile
                        profile = context.get("profile", {}) if context else {}
                        response_msg = profile.get("greeting_template", "Dạ, em nghe đây sếp.")
                    elif widget == "CAMPAIGNS":
                        ui_action = "show_campaigns"
                    else:
                        ui_action = widget if widget.startswith("show_") else f"show_{widget.lower()}"
                    
                    return IntentResponse(
                        status="success",
                        action=IntentAction.READ,
                        message=response_msg,
                        router_tier=RouterTier.TIER_1_HEURISTIC,
                        data={
                            "intent_type": intent_type,
                            "target": "dynamic",
                            "ui_action": ui_action,
                            "category": category,
                            "action": action_val
                        }
                    )

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
                # V77: Skip direct string mappings in the merge loop
                if not isinstance(kws, list): continue
                
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
        if any(kw in norm_query for kw in keywords):
            target = tgt
            break

    # --- Detect TIMEFRAME (Shadow-safe detection) ---
    timeframe = "none"
    # Sort keys to check longer/more specific timeframes first (e.g., 'this_month' before 'today')
    for tf in ["this_month", "this_week", "today"]:
        keywords = NORM_TIMEFRAME_KEYWORDS.get(tf, [])
        if any(kw in norm_query for kw in keywords):
            timeframe = tf
            break

    # ═══ CONTEXTUAL RESOLUTION (Phase 76.4) ═══
    # Rule 1: Explicit Product Ellipsis (Priority)
    is_product_ellipsis = any(kw in norm_query for kw in ["gia bao nhieu", "con hang khong", "con ko", "gia sao"])
    if is_product_ellipsis:
        target = "product"
        logger.debug("[Heuristic] Product Ellipsis detected -> target: product")

    # Rule 2: Inheritance for follow-up questions (e.g., "thế còn tháng này?")
    if target == "none":
        if timeframe != "none" or any(kw in norm_query for kw in ["the con", "con", "va"]):
            target = ctx.get("last_target", "none")
            if target != "none":
                logger.debug(f"[Heuristic] Inherited target: {target}")

    if target == "none":
        return None

    # Rule 3: Timeframe Inheritance (Only for data-heavy targets)
    if timeframe == "none" and target in ["revenue", "order"]:
        timeframe = ctx.get("last_timeframe", "none")
        if timeframe != "none":
            logger.debug(f"[Heuristic] Inherited timeframe: {timeframe}")

    # Persistence for next turn (XoHi memory)
    ctx["last_target"] = target
    ctx["last_timeframe"] = timeframe

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
    is_nav_explicit = any(kw in norm_query for kw in NORM_NAV_EXPLICIT)

    # Rule R82.23: Content Factory Priority (Phase 77.2 Tightening)
    # 76.3: Use pre-normalized keywords for content factory
    # V77.6: Data Query targets (revenue, order, etc.) MUST NOT trigger CONTENT_CREATE 
    # unless explicit factory keywords are present.
    is_content_factory = (target == "news" and verb == "create") or any(kw in norm_query for kw in NORM_CONTENT_FACTORY)
    
    # Safety Override: If it looks like a data query (revenue), drop content factory flag
    if is_content_factory and target in ["revenue", "order", "product", "user"] and not any(kw in norm_query for kw in NORM_CONTENT_FACTORY):
        logger.debug(f"[Heuristic] Safety Reject: Mixed DATA_QUERY/CONTENT target {target} - defaulting to DATA_QUERY")
        is_content_factory = False

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
            "campaign": "Dạ sếp, em mở Content Factory cho sếp ngay đây ạ.",
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
