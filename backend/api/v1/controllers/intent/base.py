# backend/api/v1/controllers/intent/base.py
import json
import time
import hashlib
import uuid
import asyncio
import logging
from typing import Optional, Dict, List, cast
from uuid import UUID

from litestar import Controller, post, Request
from litestar.di import Provide
from litestar.repository.filters import LimitOffset

from backend.api.v1.schemas.intent import IntentRequest, IntentResponse, IntentAction
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
from backend.database.models import AgentTelemetryLog
from backend.core.constants.action_vi import ACTION_VI
from .utils import save_message

logger = logging.getLogger("api-gateway")

class IntentController(Controller):
    """
    Phễu Lọc 3 Tầng — API Gateway Entry Point
    Tier 1 (Heuristic) -> Tier 2 (Semantic SLM) -> Tier 3 (Cloud LLM)
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

    def __init__(self, **kwargs: object) -> None:
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
        """Standard non-streaming intent processing."""
        start_time = time.monotonic()
        session_id = data.session_id or str(uuid.uuid4())

        try:
            if not self.shield.scan(data.query):
                return self._error("Lõi nhận thức gián đoạn...")

            user_info: Optional[Dict[str, object]] = getattr(request.state, "user", None)
            user_id: Optional[str] = None
            if user_info:
                user_id = cast(Optional[str], user_info.get("id"))
                if not user_id and "sub" in user_info:
                    user = await user_repo.get_one_or_none(email=cast(str, user_info["sub"]))
                    if user:
                        user_id = user.id

            recent_msgs = await chat_repo.list(
                LimitOffset(limit=10, offset=0),
                session_id=session_id,
                order_by=[("created_at", "desc")],
                deleted_at=None
            )

            context: List[Dict[str, object]] = [
                {"role": m.role, "content": cast(Dict[str, object], m.content)["text"]}
                for m in reversed(list(recent_msgs))
                if isinstance(m.content, dict) and "text" in m.content
            ]

            result = await orchestrator.classify(
                transcript=data.query,
                user_id=user_id or "default",
                app_state=cast(Dict[str, object], request.app.state),
                context=context,
                screen_context=data.screen_context,
                modality=data.modality
            )

            if user_id and result.status != "error":
                profile = await profile_repo.get_one_or_none(user_id=user_id)
                if profile and profile.capabilities:
                    caps: Dict[str, object] = profile.capabilities if isinstance(profile.capabilities, dict) else json.loads(profile.capabilities)
                    action = result.action.value if hasattr(result.action, "value") else str(result.action)
                    check = "READ" if action == "COUNT" else action
                    if not caps.get(check, True):
                        result.status = "error"
                        result.message = f"Dạ, năng lực '{ACTION_VI.get(action, action)}' đang tạm khóa. Sếp bật lại trong Cài đặt Giọng nói để em hỗ trợ ạ."
                        result.data = {"restricted": True, "action": action}

            intent_data: Dict[str, object] = result.data or {}
            intent_type = intent_data.get("intent_type")
            result_category = intent_data.get("category")

            if result.status != "error" and (result_category != "SESSION_CTRL" or intent_type == "UI_NAV"):
                try:
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
                            user_id=user_id
                        ),
                        timeout=45.0
                    )
                except asyncio.TimeoutError:
                    return self._error("Giao thức kết nối đang bận, Sếp thử lại sau nhé.")

            tier_str = str(result.router_tier.value if result.router_tier and hasattr(result.router_tier, "value") else result.router_tier)

            try:
                await telemetry_repo.add(
                    AgentTelemetryLog(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        agent_name=f"TrinityCore-Tier_{tier_str}",
                        intent_hash=hashlib.sha256(data.query.lower().strip().encode()).hexdigest()[:16],
                        input_tokens=getattr(result, "input_tokens", 0) or 0,
                        output_tokens=getattr(result, "output_tokens", 0) or 0,
                        cost_token=float(result.cost_tokens or 0.0),
                        duration_ms=int((time.monotonic() - start_time) * 1000)
                    )
                )
                await telemetry_repo.session.commit()
            except Exception:
                pass

            ui_action = cast(Dict[str, object], result.data or {}).get("ui_action")
            action_val = result.action.value if hasattr(result.action, "value") else str(result.action)

            asyncio.create_task(save_message(chat_repo, session_id, "user", data.query, None, data.modality, user_id=user_id))
            if action_val != "CONTENT_CREATE":
                asyncio.create_task(save_message(chat_repo, session_id, "assistant", result.message or "", cast(Optional[str], ui_action), data.modality, tier_str, user_id=user_id, data_extra=result.data))

            return result

        except Exception as e:
            logger.exception(f"[Gateway Error] {e}")
            return self._error("Giao thức kết nối đang bận, Sếp thử lại sau nhé.")

    def _error(self, msg: str) -> IntentResponse:
        return IntentResponse(status="error", action=IntentAction.READ, message=msg,
                              router_tier=None, cost_tokens=0.0)
