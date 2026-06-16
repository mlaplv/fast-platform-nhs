"""
Heuristic Classifier — Zero-LLM Intent Classification.
V56.0: Modularized for Martial Law (<300 LOC).
"""
import logging
from typing import Optional

from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.utils.text import normalize_vn
from backend.services.xohi_memory import xohi_memory
from .heuristic_data import (
    RE_EMAIL, RE_LEARN_1, RE_LEARN_2, RE_LEARN_3, RE_LEARN_VN_1, RE_LEARN_VN_2, RE_LEARN_VN_3,
    NORM_TARGET_KEYWORDS, NORM_MODE_KEYWORDS, NORM_TIMEFRAME_KEYWORDS,
    NORM_COUNT_KEYWORDS, NORM_QUESTION_KEYWORDS, NORM_LEARN_KEYWORDS, NORM_MUTATE_KEYWORDS,
    NORM_NAV_EXPLICIT, NORM_GREETING_KEYWORDS, NORM_CONTENT_FACTORY, TARGET_TO_WIDGET,
    VI_VERB_MAP, VI_TARGET_MAP, DELETE_KEYWORDS, EDIT_KEYWORDS, NAME_MARKERS, NAME_STOP_WORDS
)

logger = logging.getLogger("api-gateway")
_DYNAMIC_MERGE_CACHE = {}

def _merge_lists(a, b):
    res = list(a); seen = set(a)
    for x in b:
        if x not in seen: res.append(x); seen.add(x)
    return res

async def heuristic_classify(combined_lower: str, user_id: str, context: Optional[dict] = None, intent_map: Optional[dict] = None, norm_query: Optional[str] = None) -> Optional[IntentResponse]:
    if any(p in (norm_query or normalize_vn(combined_lower)) for p in ["manage skills", "skills", "voice settings"]):
        return IntentResponse(
            status="success", action=IntentAction.READ, message="Dạ sếp, em mở cài đặt giọng nói cho sếp ngay đây ạ.",
            router_tier=RouterTier.TIER_1_HEURISTIC,
            data={"intent_type": "UI_NAV", "target": "settings", "ui_action": "show_voice_settings", "category": "SESSION_CTRL", "action": "HARDWARE_SLEEP"}
        )

    norm_query = norm_query or normalize_vn(combined_lower)
    dynamic_mapping = intent_map if intent_map is not None else await xohi_memory.get_system_intent_mapping()

    # --- Phase 77.2: Learn Command ---
    if any(kw in norm_query for kw in NORM_LEARN_KEYWORDS):
        l_kw, l_tgt = "", ""
        for reg in [RE_LEARN_VN_1, RE_LEARN_VN_2, RE_LEARN_VN_3]:
            m = reg.search(combined_lower)
            if m: l_kw, l_tgt = m.group(1).strip().strip("'\""), m.group(2).strip().strip("'\""); break
        if not l_kw:
            for reg in [RE_LEARN_1, RE_LEARN_2, RE_LEARN_3]:
                m = reg.search(norm_query)
                if m: l_kw, l_tgt = m.group(1).strip(), m.group(2).strip(); break
        return IntentResponse(status="success", action=IntentAction.MUTATE, message="", router_tier=RouterTier.TIER_1_HEURISTIC, data={"intent_type": "LEARN_COMMAND", "target": "none", "learn_keyword": l_kw, "learn_target": l_tgt})

    # --- Direct Command Mapping ---
    if dynamic_mapping:
        for cmd, widget in dynamic_mapping.items():
            if isinstance(widget, str) and (widget.startswith("show_") or widget.isupper()) and normalize_vn(cmd) in norm_query:
                category = "SESSION_CTRL" if widget in ["HARDWARE_SLEEP", "WAKE_ROUTINE"] else "UI_NAV"
                action_val = widget if widget in ["HARDWARE_SLEEP", "WAKE_ROUTINE"] else ""
                res_msg = f"Dạ sếp, em mở {cmd} cho sếp ngay đây ạ."
                if widget == "HARDWARE_SLEEP": res_msg = "Hẹn gặp lại sếp."
                elif widget == "WAKE_ROUTINE": res_msg = (context or {}).get("profile", {}).get("greeting_template", "Dạ, em nghe đây sếp.")
                ui_action = "show_campaigns" if widget == "CAMPAIGNS" else ("show_voice_settings" if widget == "VOICE_SETTINGS" else (widget if widget.startswith("show_") else f"show_{widget.lower()}"))
                return IntentResponse(status="success", action=IntentAction.READ, message=res_msg, router_tier=RouterTier.TIER_1_HEURISTIC, data={"intent_type": "UI_NAV" if widget not in ["HARDWARE_SLEEP", "WAKE_ROUTINE"] else "SESSION_CTRL", "target": "dynamic", "ui_action": ui_action, "category": category, "action": action_val})

    # --- Dynamic Merge & Search ---
    map_hash = hash(str(dynamic_mapping)); cache_key = (user_id, map_hash)
    if dynamic_mapping and cache_key in _DYNAMIC_MERGE_CACHE:
        merged_target_keywords = _DYNAMIC_MERGE_CACHE[cache_key]
    elif dynamic_mapping:
        merged_target_keywords = {**NORM_TARGET_KEYWORDS}
        for tgt, kws in dynamic_mapping.items():
            if isinstance(kws, list): merged_target_keywords[tgt] = _merge_lists(merged_target_keywords.get(tgt, []), [normalize_vn(kw) for kw in kws])
        if len(_DYNAMIC_MERGE_CACHE) > 100: _DYNAMIC_MERGE_CACHE.clear()
        _DYNAMIC_MERGE_CACHE[cache_key] = merged_target_keywords
    else: merged_target_keywords = NORM_TARGET_KEYWORDS

    target, timeframe = "none", "none"
    for tgt, keywords in merged_target_keywords.items():
        if any(kw in norm_query for kw in keywords): target = tgt; break
    for tf in ["this_month", "this_week", "today"]:
        if any(kw in norm_query for kw in NORM_TIMEFRAME_KEYWORDS.get(tf, [])): timeframe = tf; break

    if any(kw in norm_query for kw in ["gia bao nhieu", "con hang khong", "con ko", "gia sao"]): target = "product"
    if target == "none" and (timeframe != "none" or any(kw in norm_query for kw in ["the con", "con", "va"])):
        target = (context or {}).get("last_target", "none")
    
    # --- Greeting Logic (Elite V2.2) ---
    if target == "none" and any(kw in norm_query for kw in NORM_GREETING_KEYWORDS):
        return IntentResponse(
            status="success", action=IntentAction.READ, 
            message=(context or {}).get("profile", {}).get("greeting_template", "Dạ?"),
            router_tier=RouterTier.TIER_1_HEURISTIC,
            data={"intent_type": "SESSION_CTRL", "category": "SESSION_CTRL", "action": "WAKE_ROUTINE"}
        )

    if target == "none": return None
    if timeframe == "none" and target in ["revenue", "order"]: timeframe = (context or {}).get("last_timeframe", "none")
    if context is not None: context["last_target"], context["last_timeframe"] = target, timeframe

    is_mutate = any(kw in norm_query for kw in NORM_MUTATE_KEYWORDS)
    extracted_entities, verb = {}, "create"
    if is_mutate:
        if any(kw in combined_lower for kw in DELETE_KEYWORDS): verb = "delete"
        elif any(kw in combined_lower for kw in EDIT_KEYWORDS): verb = "edit"
        for marker in NAME_MARKERS:
            if marker in combined_lower:
                name_part = combined_lower.split(marker)[1].strip()
                for stop in NAME_STOP_WORDS:
                    if stop in name_part: name_part = name_part.split(stop)[0].strip()
                extracted_entities["name"] = name_part.title(); break
        email_match = RE_EMAIL.search(combined_lower)
        if email_match: extracted_entities["email"] = email_match.group(0)

    is_content_factory = (target in ["news", "product"] and verb == "create") or any(kw in norm_query for kw in NORM_CONTENT_FACTORY)
    if is_content_factory and target in ["revenue", "order", "user"] and not any(kw in norm_query for kw in NORM_CONTENT_FACTORY):
        is_content_factory = False

    content_mode = "viral"
    if is_content_factory:
        for mode, keywords in NORM_MODE_KEYWORDS.items():
            if any(kw in norm_query for kw in keywords): content_mode = mode; break

    is_content_factory = (target in ["news", "product"] and is_mutate and verb == "create") or any(kw in norm_query for kw in NORM_CONTENT_FACTORY)
    if is_content_factory: intent_type, action = "CONTENT_CREATE", IntentAction.CONTENT_CREATE
    elif is_mutate: intent_type, action = "MUTATE", IntentAction.MUTATE
    elif not any(kw in norm_query for kw in NORM_NAV_EXPLICIT) and (any(kw in norm_query for kw in NORM_COUNT_KEYWORDS) or any(kw in norm_query for kw in NORM_QUESTION_KEYWORDS) or (target != "none" and timeframe != "none") or target == "revenue"):
        intent_type, action = "DATA_QUERY", IntentAction.COUNT
    else: intent_type, action = "UI_NAV", IntentAction.READ

    widget_id = TARGET_TO_WIDGET.get(target, "") if (intent_type == "UI_NAV" or target == "revenue" or any(kw in norm_query for kw in ["mo ", "xem ", "vao ", "bieu do"])) else ""
    response_msg = ""
    if intent_type == "MUTATE":
        response_msg = f"Sếp muốn {VI_VERB_MAP.get(verb, verb)} {VI_TARGET_MAP.get(target, target)}" + (f' "{extracted_entities["name"]}"' if "name" in extracted_entities else "") + ". Xác nhận thông tin bên dưới ạ."
    elif intent_type == "UI_NAV":
        response_msg = {"revenue": "Dạ sếp, em mở biểu đồ doanh thu cho sếp ngay đây ạ.", "order": "Dạ sếp, em mở quản lý đơn hàng cho sếp ngay đây ạ.", "product": "Dạ sếp, em mở quản lý sản phẩm cho sếp ngay đây ạ.", "user": "Dạ sếp, em mở danh sách nhân viên cho sếp ngay đây ạ.", "category": "Dạ sếp, em mở quản lý danh mục cho sếp ngay đây ạ.", "news": "Dạ sếp, em mở quản lý bài viết cho sếp ngay đây ạ.", "settings": "Dạ sếp, em mở cài đặt giọng nói cho sếp ngay đây ạ.", "campaign": "Dạ sếp, em mở Content Factory cho sếp ngay đây ạ.", "brain": "Dạ sếp, em mở Helen Brain — Quản trị tri thức cho sếp ngay đây ạ.", "ads_protection": "Dạ sếp, em mở Trung tâm Google Ads cho sếp ngay đây ạ.", "video_script": "Dạ sếp, em mở quản lý kịch bản video marketing cho sếp ngay đây ạ."}.get(target, "")

    res_data = {"intent_type": intent_type, "target": target, "verb": verb, "timeframe": timeframe, "content_mode": content_mode, "ui_action": widget_id, "entities": extracted_entities}
    if intent_type == "UI_NAV": res_data["category"], res_data["action"] = "SESSION_CTRL", "HARDWARE_SLEEP"

    return IntentResponse(status="success", action=action, message=response_msg, router_tier=RouterTier.TIER_1_HEURISTIC, cost_tokens=0.0, requires_confirmation=intent_type == "MUTATE", data=res_data)
