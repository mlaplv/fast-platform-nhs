# backend/routers/intent_core.py
import json
import time
import hashlib
import uuid
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, cast

from litestar import Request
from litestar.response import Stream
from litestar.repository.filters import LimitOffset

from backend.schemas.intent import IntentRequest, IntentResponse, IntentAction, RouterTier
from backend.services.routing.intent_orchestrator import orchestrator
from backend.services.ai_engine.core.semantic_shield import SemanticShield
from backend.database.repositories import (
    UserRepository, ChatMessageRepository, VoiceProfileRepository,
    AgentTelemetryLogRepository, OrderRepository, ProductBaseRepository,
    ContentCampaignRepository
)
from backend.constants.action_vi import ACTION_VI
from backend.utils.data_stripper import DataStripper

from .intent_utils import sse, background_save_logs, background_tasks

logger = logging.getLogger("api-gateway")

class IntentStreamCore:
    def __init__(self) -> None:
        self.shield = SemanticShield()

    async def handle_stream(
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
    ) -> Stream:
        """Core logic for streaming intent processing phases via SSE."""

        async def generate() -> AsyncGenerator[bytes, None]:
            start_time = time.monotonic()
            session_id = data.session_id or str(uuid.uuid4())
            user_id: Optional[str] = None

            try:
                # ── Yield STT Listening immediately ──
                yield sse("status", {"step": "stt", "msg": "listening"})

                # Phase 76.3.2: Immediate Transcript Feedback
                if data.query:
                    yield sse("transcript", {"text": data.query})

                # Phase 3 Kill-switch: Empty transcript
                if not data.query or not data.query.strip():
                    logger.warning("[SSE] Empty transcript detected. Yielding SLEEP via SESSION_CTRL.")
                    yield sse("done", {
                        "category": "SESSION_CTRL",
                        "type": "SLEEP",
                        "status": "success",
                        "message": "",
                        "ui_action": ""
                    })

                    task = asyncio.create_task(background_save_logs(
                        session_id=session_id, user_id=None,
                        telemetry_data={
                            "id": str(uuid.uuid4()),
                            "session_id": session_id,
                            "agent_name": "NoiseFilter",
                            "intent_hash": "empty",
                            "input_tokens": 0, "output_tokens": 0, "cost_token": 0.0, "duration_ms": 1
                        },
                        is_noise=True
                    ))
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)
                    return

                # ── Jailbreak scan ──
                if not self.shield.scan(data.query):
                    yield sse("error", {"message": "Lõi nhận thức gián đoạn..."})
                    return

                # ── Resolve user ──
                user_info: Optional[Dict[str, object]] = getattr(request.state, "user", None)
                if user_info:
                    user_id = cast(Optional[str], user_info.get("id"))
                    if not user_id and "sub" in user_info:
                        user = await user_repo.get_one_or_none(email=cast(str, user_info["sub"]))
                        if user:
                            user_id = str(user.id)

                # ── Context ──
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

                # ── Phase 1: Classify ──
                result = await orchestrator.classify(
                    transcript=data.query,
                    user_id=user_id or "default",
                    app_state=cast(Dict[str, object], request.app.state),
                    context=context,
                    screen_context=data.screen_context,
                )

                tier_str = str(result.router_tier.value if result.router_tier and hasattr(result.router_tier, "value") else result.router_tier)

                if tier_str != "1":
                    yield sse("classify", {"status": "thinking"})

                yield sse("classify", {
                    "status": "done",
                    "tier": tier_str,
                    "action": result.action.value if hasattr(result.action, "value") else str(result.action),
                })

                # ── Phase 2: Skill Guard ──
                if user_id and result.status != "error":
                    profile = await profile_repo.get_one_or_none(user_id=user_id)
                    if profile and profile.capabilities:
                        caps: Dict[str, object] = profile.capabilities if isinstance(profile.capabilities, dict) else json.loads(profile.capabilities)
                        action = result.action.value if hasattr(result.action, "value") else str(result.action)
                        check = "READ" if action == "COUNT" else action
                        if not caps.get(check, True):
                            msg = f"Dạ, năng lực '{ACTION_VI.get(action, action)}' đang tạm khóa. Sếp bật lại trong Cài đặt Giọng nói để em hỗ trợ ạ."
                            yield sse("error", {"message": msg, "restricted": True, "action": action})
                            return

                # ── Phase 3: Execute ──
                intent_data: Dict[str, object] = result.data or {}
                result_category = intent_data.get("category")
                intent_type = intent_data.get("intent_type")

                if result.status != "error" and (result_category != "SESSION_CTRL" or intent_type == "UI_NAV"):
                    yield sse("execute", {"status": "working"})

                    action_val = result.action.value if hasattr(result.action, "value") else str(result.action)
                    if intent_type in ["DEEP_ANALYSIS", "UNKNOWN"] or action_val == "ANALYZE":
                        full_message = ""
                        async for chunk in orchestrator.t3_router.stream_reason(
                            data.query, context, screen_context=data.screen_context
                        ):
                            full_message += chunk
                            yield sse("text_delta", {"text": chunk})
                        result.message = full_message
                    else:
                        effective_transcript = cast(str, intent_data.get("effective_transcript", data.query))
                        try:
                            result = await asyncio.wait_for(
                                orchestrator.execute(
                                    classification=result,
                                    transcript=effective_transcript,
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
                            yield sse("error", {"message": "Giao thức kết nối đang bận, Sếp thử lại sau nhé."})
                            return

                # ── Phase 4: Done ──
                intent_data_final: Dict[str, object] = result.data or {}
                yield sse("done", {
                    "status": result.status,
                    "message": result.message or "",
                    "data": intent_data_final,
                    "ui_action": intent_data_final.get("ui_action", ""),
                    "action": result.action.value if hasattr(result.action, "value") else str(result.action),
                    "router_tier": tier_str,
                    "cost_tokens": result.cost_tokens or 0.0,
                    "requires_confirmation": bool(getattr(result, "requires_confirmation", False) or intent_data_final.get("requires_confirmation", False)),
                    "behavior": "listen" if (bool(getattr(result, "requires_confirmation", False) or intent_data_final.get("action") == "STT_CONFIRM")) else "sleep"
                })

                # ── Background: Telemetry + Chat save ──
                ui_action = intent_data_final.get("ui_action")
                data_extra: Dict[str, object] = dict(intent_data_final)
                if "error_trace" in data_extra:
                    data_extra["error_trace"] = DataStripper.truncate_payload(str(data_extra["error_trace"]))

                task = asyncio.create_task(background_save_logs(
                    session_id=session_id, user_id=user_id,
                    data_query=data.query, modality=data.modality,
                    result_message=result.message or "", result_ui_action=cast(Optional[str], ui_action),
                    tier_str=tier_str, data_extra=data_extra,
                    telemetry_data={
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "agent_name": f"TrinityCore-Tier_{tier_str}",
                        "intent_hash": hashlib.sha256(data.query.lower().strip().encode()).hexdigest()[:16],
                        "input_tokens": getattr(result, "input_tokens", 0) or 0,
                        "output_tokens": getattr(result, "output_tokens", 0) or 0,
                        "cost_token": float(result.cost_tokens or 0.0),
                        "duration_ms": int((time.monotonic() - start_time) * 1000)
                    }
                ))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

            except Exception as e:
                logger.exception(f"[SSE Gateway Error] {e}")
                yield sse("error", {"message": "Giao thức kết nối đang bận, Sếp thử lại sau nhé."})

        return Stream(generate(), media_type="text/event-stream")
