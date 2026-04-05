import json, time, hashlib, uuid, asyncio, logging
from typing import Optional, Dict, List, Union
from uuid import UUID
from litestar import Controller, post, Request
from litestar.di import Provide
from litestar.repository.filters import LimitOffset
from backend.schemas.intent import IntentRequest, IntentResponse, IntentAction, RouterTier
from backend.services.routing.intent_orchestrator import orchestrator
from backend.services.ai_engine.core.semantic_shield import SemanticShield
from backend.database.repositories import (
    UserRepository, ChatMessageRepository, VoiceProfileRepository, 
    AgentTelemetryLogRepository, OrderRepository, ProductBaseRepository,
    ContentCampaignRepository,
    provide_user_repo, provide_chat_repo, provide_voice_repo, 
    provide_telemetry_repo, provide_order_repo, provide_product_repo,
    provide_campaign_repo
)
from backend.database.models import User, ChatMessage, AgentTelemetryLog
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

# Tên tiếng Việt của từng IntentAction — dùng trong Skill Guard thông báo lỗi
from backend.constants.action_vi import ACTION_VI

# ui_action → target entity (dùng trong heuristic fallback)
UI_ACTION_TARGET = {
    "show_order_management":   "order",
    "show_product_management": "product",
    "show_user_management":    "user",
    "show_user_table":         "user",
    "show_revenue_chart":      "revenue",
}

# Keywords kích hoạt heuristic COUNT (check trên combined_lower = gốc + sau-STT)
COUNT_KEYWORDS = ["bao nhiêu", "mấy", "tổng số", "dân số", "doanh thu", "doanh số"]


class IntentController(Controller):
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]
    """
    Phễu Lọc 3 Tầng — API Gateway Entry Point
    Tier 1 (Heuristic) → Tier 2 (Semantic SLM) → Tier 3 (Cloud LLM)
    """
    path = "/api/v1/intent"
    dependencies = {
        "user_repo": Provide(provide_user_repo),
        "chat_repo": Provide(provide_chat_repo),
        "profile_repo": Provide(provide_voice_repo),
        "telemetry_repo": Provide(provide_telemetry_repo),
        "order_repo": Provide(provide_order_repo),
        "product_repo": Provide(provide_product_repo),
        "campaign_repo": Provide(provide_campaign_repo),
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.shield = SemanticShield()

    @post("/")
    async def process_intent(
        self, 
        request: Request, 
        data: IntentRequest,
        user_repo: UserRepository,
        chat_repo: ChatMessageRepository,
        profile_repo: VoiceProfileRepository,
        telemetry_repo: AgentTelemetryLogRepository,
        order_repo: OrderRepository,
        product_repo: ProductBaseRepository,
        campaign_repo: ContentCampaignRepository,
    ) -> IntentResponse:
        """
        Phễu Lọc 3 Tầng — [THIẾT QUÂN LUẬT] Fully DI-based.
        """
        start_time = time.monotonic()
        session_id = data.session_id or str(uuid.uuid4())

        try:
            # ── Jailbreak scan (STT corrections removed — Groq Whisper handles accuracy) ──
            if not self.shield.scan(data.query):
                return _error("Lõi nhận thức gián đoạn...")

            # ── Resolve user_id từ JWT ──
            user_info = getattr(request.state, "user", None)
            user_id = None
            if user_info:
                # Rule R86: Prefer direct ID from JWT for performance and consistency
                user_id = user_info.get("id")
                if not user_id and "sub" in user_info:
                    user = await user_repo.get_one_or_none(email=user_info["sub"])
                    if user:
                        user_id = user.id

            # ── Lịch sử hội thoại (10 tin) ──
            recent_msgs = await chat_repo.list(
                LimitOffset(limit=10, offset=0),
                session_id=session_id, 
                order_by=[("created_at", "desc")], 
                deleted_at=None
            )
            
            context = [
                {"role": m.role, "content": m.content["text"]}
                for m in reversed(list(recent_msgs))
                if isinstance(m.content, dict) and "text" in m.content
            ]

            # ── TRINITY PHASE 1: Classification (Dispatcher) ──
            # Orchestrator handles T1 (Heuristic) and T2 (LLM Dispatcher)
            result = await orchestrator.classify(
                transcript=data.query,
                user_id=user_id,
                app_state=request.app.state,
                context=context,
                screen_context=data.screen_context,
                modality=data.modality
            )

            # ── TRINITY PHASE 2: Skill Guard (Constitutional Protection) ──
            # Guard runs BEFORE expensive Data Injection/Reasoning
            intent_data = result.data or {}
            intent_type = intent_data.get("intent_type")
            result_category = intent_data.get("category")
            
            if user_id and result.status != "error" and result_category != "SESSION_CTRL":
                profile = await profile_repo.get_one_or_none(user_id=user_id)
                if profile and profile.capabilities:
                    caps = profile.capabilities if isinstance(profile.capabilities, dict) else json.loads(profile.capabilities)
                    action = result.action.value if hasattr(result.action, "value") else result.action
                    check = "READ" if action == "COUNT" else action
                    if not caps.get(check, True):
                        result.status  = "error"
                        result.message = f"Dạ, năng lực '{ACTION_VI.get(action, action)}' đang tạm khóa. Sếp bật lại trong Cài đặt Giọng nói để em hỗ trợ ạ."
                        result.data    = {"restricted": True, "action": action}

            # ── TRINITY PHASE 3: Execution (Provider -> Refiner) ──
            # Only execute Trinity Loop or Tier 3 if NOT restricted
            # BẮT BUỘC: Bỏ qua Execute cho SESSION_CTRL (Wake/Sleep) — đã hoàn thành ở T1
            # Tuy nhiên, UI_NAV cần Execute để Inject dữ liệu (ví dụ: Biểu đồ)
            
            if result.status != "error" and (result_category != "SESSION_CTRL" or intent_type == "UI_NAV"):
                try:
                    # GLOBAL TIMEOUT GUARD: Force response within 20s to prevent hanging
                    result = await asyncio.wait_for(
                        orchestrator.execute(
                            classification=result,
                            transcript=data.query,
                            context=context,
                            screen_context=data.screen_context,
                            user_repo=user_repo,
                            order_repo=order_repo,
                            product_repo=product_repo,
                            campaign_repo=campaign_repo,
                            modality=data.modality,
                            user_id=user_id # Propagate identity for R86
                        ),
                        timeout=45.0 # Increased to 45s to tolerate TrinityBridge 429 backoff & key rotation
                    )
                except asyncio.TimeoutError:
                    logger.error(f"[Gateway Timeout] Request hung too long: {data.query}")
                    return _error("Giao thức kết nối đang bận, Sếp đợi em một chút hoặc thử lại sau nhé.")

            tier_str = str(result.router_tier.value if hasattr(result.router_tier, "value") else result.router_tier)

            # ── Telemetry (background) ──
            try:
                await telemetry_repo.add(
                    AgentTelemetryLog(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        agent_name=f"TrinityCore-Tier_{tier_str}",
                        intent_hash=hashlib.sha256(data.query.lower().strip().encode()).hexdigest()[:16],
                        input_tokens=getattr(result, "input_tokens", 0),
                        output_tokens=getattr(result, "output_tokens", 0),
                        cost_token=float(result.cost_tokens),
                        duration_ms=int((time.monotonic() - start_time) * 1000)
                    )
                )
                await telemetry_repo.session.commit()
            except Exception as telemetry_error:
                logger.error(f"[Telemetry Error] Failed to log agent performance: {telemetry_error}")

            # ── Message Persistence (Background) ──
            ui_action = (result.data or {}).get("ui_action")
            action_val = result.action.value if hasattr(result.action, "value") else result.action
            
            asyncio.create_task(self._save_message(chat_repo, session_id, "user", data.query, None, data.modality, user_id=user_id))
            
            # Rule R86: Selective Persistence — Skip assistant save if Responder handles it (e.g. Content Factory)
            if action_val != "CONTENT_CREATE":
                asyncio.create_task(self._save_message(chat_repo, session_id, "assistant", result.message, ui_action, data.modality, tier_str, user_id=user_id, data_extra=result.data))

            return result

        except Exception as e:
            logger.exception(f"[Gateway Error] {e}")
            return _error("Giao thức kết nối đang bận, Sếp đợi em một chút hoặc thử lại sau nhé.")

    async def _save_message(self, chat_repo: ChatMessageRepository, session_id: str, role: str, content: str, ui_action: Optional[str], modality: str, router_tier: Optional[str] = None, user_id: Optional[UUID] = None, data_extra: Optional[Dict[str, object]] = None) -> None:
        payload = {"text": content}
        if ui_action:    payload["ui_action"]   = ui_action
        if router_tier:  payload["router_tier"]  = router_tier
        if data_extra:
            if data_extra.get("category") == "CONTENT_CREATE":
                # Slim log: only audit-trail fields, heavy data lives in content_campaigns
                for key in ("category", "campaign_id", "step", "status", "action"):
                    if data_extra.get(key) is not None:
                        payload[key] = data_extra[key]
            else:
                payload.update(data_extra)
        try:
            await chat_repo.add(
                ChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    user_id=user_id,
                    role=role,
                    content=payload,
                    modality=modality or "text",
                )
            )
            await chat_repo.session.commit()
        except Exception as e:
            logger.error(f"[ChatMessage] {e}")


def _error(msg: str) -> IntentResponse:
    """Shortcut trả lỗi chuẩn — tránh lặp 3 field mỗi lần."""
    return IntentResponse(status="error", action=IntentAction.READ, message=msg,
                          router_tier=None, cost_tokens=0.0)
