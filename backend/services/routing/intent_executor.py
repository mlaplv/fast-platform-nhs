import logging, time
from typing import List, Dict, Optional, Any
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.utils.text import normalize_vn
from backend.services.xohi_memory import xohi_memory
from backend.services.data_injector import data_injector
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.database.repositories import ContentCampaignRepository

logger = logging.getLogger("api-gateway")

NAV_MSG_MAP = {
    "revenue": "biểu đồ doanh thu", "order": "quản lý đơn hàng", "product": "quản lý sản phẩm",
    "user": "danh sách nhân viên", "category": "quản lý danh mục", "news": "quản lý bài viết", 
    "settings": "cài đặt hệ thống", "campaign": "quản lý chiến dịch", "analytics": "thống kê chi tiết"
}

class RouterExecutor:
    """Phase 2: Action Execution (Phase 3 of Trinity Loop)."""
    def __init__(self, t3_router, t2_refiner):
        self.t3_router = t3_router
        self.t2_refiner = t2_refiner

    async def execute(self, classification: IntentResponse, transcript: str, context=None, screen_context=None, **kwargs) -> IntentResponse:
        start = time.monotonic()
        d = classification.data or {}; t = d.get("cleaned_transcript", transcript)
        i_type = d.get("intent_type", "UNKNOWN")
        mod = kwargs.get("modality", "text"); m_tag = "v" if mod == "voice" else "c"

        if i_type == "LEARN_COMMAND": return await self._handle_learn(d)
        if i_type in ["DEEP_ANALYSIS", "UNKNOWN"] or classification.action == IntentAction.ANALYZE:
            return await self.t3_router.reason(t, context, screen_context=screen_context)

        if i_type == "CONTENT_CREATE" or classification.action == IntentAction.CONTENT_CREATE:
            return await content_factory.handle_voice_request(t, campaign_repo=kwargs.get("campaign_repo"), user_id=kwargs.get("user_id"), intent_data=d)

        if i_type in ["CONTENT_APPROVE", "CONTENT_REJECT"]:
            repo = kwargs.get("campaign_repo")
            lat = await content_factory.get_active_campaign(repo, user_id=kwargs.get("user_id"))
            if not lat: return IntentResponse(status="error", action=IntentAction.READ, message="Không có yêu cầu nào đang chờ.")
            gr = await (content_factory.approve_step(lat.id, {"approved":True}, repo) if i_type == "CONTENT_APPROVE" else content_factory.retry_step(lat.id, repo))
            return IntentResponse(
                status=gr.status,
                action=classification.action,
                message=gr.message,
                router_tier=classification.router_tier,
                data={**(classification.data or {}), **(gr.data or {})}
            )

        # Default Inject
        res = await data_injector.inject(classification, t, **kwargs)
        
        # Refine Data Queries
        if i_type == "DATA_QUERY" or res.action == IntentAction.COUNT:
            raw = res.data.get("injected_count") or res.data.get("raw_count")
            if raw is not None:
                msg, cost = await self.t2_refiner.refine(t, res.data.get("target", ""), str(raw))
                res.message, res.cost_tokens = msg, (res.cost_tokens or 0) + cost
        elif i_type == "UI_NAV" and not res.message:
            res.message = f"Dạ sếp, em mở {NAV_MSG_MAP.get(res.data.get('target', 'none'), 'trang quản trị')} cho sếp ạ."

        if res.data is None: res.data = {}
        res.data.update({"source_tag": m_tag, "router_tier_label": f"t{res.router_tier.value if hasattr(res.router_tier, 'value') else res.router_tier}"})
        return res

    async def _handle_learn(self, d) -> IntentResponse:
        kw = normalize_vn(d.get("learn_keyword", "").lower()); tgt = d.get("learn_target", "").lower()
        t_map = {"doanh thu": "show_revenue_chart", "đơn hàng": "show_order_management", "sản phẩm": "show_product_management", "nhân viên": "show_user_management", "tin tức": "show_news_management", "cài đặt": "show_voice_settings"}
        res_w = t_map.get(tgt, tgt)
        cur = await xohi_memory.get_system_intent_mapping()
        is_up = kw in cur; cur[kw] = res_w; await xohi_memory.set_system_intent_mapping(cur)
        return IntentResponse(status="success", action=IntentAction.READ, message=f"Đã {'cập nhật' if is_up else 'ghi nhớ'} lệnh '{kw}'.", router_tier=RouterTier.TIER_1_HEURISTIC, data={"intent_type": "LEARN_SUCCESS", "keyword": kw, "widget": res_w})
