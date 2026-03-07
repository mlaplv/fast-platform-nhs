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

from shared.schemas.intent import IntentResponse, IntentAction, RouterTier
from src.utils.text import normalize_vn
from src.services.xohi_memory import xohi_memory

logger = logging.getLogger("api-gateway")

# --- Keyword Dictionaries (avoid hardcode — centralized here for easy tuning) ---
TARGET_KEYWORDS = {
    "revenue": ["doanh thu", "doanh so", "bieu do", "tien", "doanh tu"],
    "order":   ["don hang", "hoa don", "bill", "dau hang"],
    "product": ["san pham", "ton kho", "kho hang", "sang pham"],
    "user":    ["nguoi dung", "khach", "nhan vien", "tai khoan"],
    "category": ["danh muc"],
    "news":    ["tin tuc", "bai viet"],
    "settings": ["cai dat", "setting", "cau hinh", "voice"],
}

TIMEFRAME_KEYWORDS = {
    "today":      ["hom nay"],
    "this_month": ["thang nay"],
    "this_week":  ["tuan nay"],
}

COUNT_KEYWORDS = ["bao nhieu", "may", "tong so", "tong", "thong ke", "chi tiet", "nao", "duoc khong"]
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


def _merge_lists(a, b):
    # deduplicate list keeping order approximately
    seen = set(a)
    res = list(a)
    for x in b:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res

async def heuristic_classify(
    combined_lower: str,
    user_id: str,
    app_state: object
) -> Optional[IntentResponse]:
    """
    Zero-LLM Heuristic Fallback — classify known patterns by keyword.
    Only handles clear-cut queries. Returns None for ambiguous ones.
    """
    norm_query = normalize_vn(combined_lower)
    
    # Fetch dynamic intent mapping from local memory (Sub-1ms)
    dynamic_mapping = await xohi_memory.get_system_intent_mapping()
    merged_target_keywords = {**TARGET_KEYWORDS}
    if dynamic_mapping:
        for tgt, kws in dynamic_mapping.items():
            if tgt in merged_target_keywords:
                merged_target_keywords[tgt] = _merge_lists(merged_target_keywords[tgt], kws)
            else:
                merged_target_keywords[tgt] = kws

    # --- Detect TARGET ---
    target = "none"
    for tgt, keywords in merged_target_keywords.items():
        if any(kw in norm_query for kw in keywords):
            target = tgt
            break

    if target == "none":
        return None

    # --- Detect TIMEFRAME ---
    timeframe = "none"
    for tf, keywords in TIMEFRAME_KEYWORDS.items():
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
    is_count = any(kw in norm_query for kw in COUNT_KEYWORDS)
    is_question = any(kw in norm_query for kw in QUESTION_KEYWORDS)
    is_mutate = any(kw in norm_query for kw in MUTATE_KEYWORDS)

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

        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', combined_lower)
        if email_match:
            extracted_entities["email"] = email_match.group(0)

    # --- Resolve intent type + action ---
    is_nav_explicit = any(kw in norm_query for kw in ["bieu do", "mo ", "xem "])
    
    if is_mutate:
        intent_type = "MUTATE"
        action = IntentAction.MUTATE
    elif not is_nav_explicit and (is_count or is_question or (target != "none" and timeframe != "none") or target == "revenue"):
        intent_type = "DATA_QUERY"
        action = IntentAction.COUNT
    else:
        intent_type = "UI_NAV"
        action = IntentAction.READ

    widget_id = TARGET_TO_WIDGET.get(target, "")

    # --- Build response message ---
    if intent_type == "MUTATE":
        v_label = VI_VERB_MAP.get(verb, verb)
        t_label = VI_TARGET_MAP.get(target, target)
        name = extracted_entities.get("name", "")
        response_msg = f"Sếp muốn {v_label} {t_label}" + (f' "{name}"' if name else "") + ". Xác nhận thông tin bên dưới ạ."
    elif intent_type == "UI_NAV":
        nav_msg_map = {
            "revenue":  "Dạ, em mở biểu đồ doanh thu cho sếp.",
            "order":    "Dạ, em mở quản lý đơn hàng cho sếp.",
            "product":  "Dạ, em mở quản lý sản phẩm cho sếp.",
            "user":     "Dạ, em mở danh sách nhân viên cho sếp.",
            "category": "Dạ, em mở quản lý danh mục cho sếp ạ.",
            "news":     "Dạ, em mở quản lý bài viết cho sếp ạ.",
            "settings": "Dạ, em mở cài đặt giọng nói cho sếp ạ.",
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
