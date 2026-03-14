"""SSE Streaming Intent Endpoint — Real-time phased response.

Streams classify → guard → execute phases as Server-Sent Events.
Frontend receives chunks immediately instead of waiting 2-5s for full response.

Format: data: {"phase":"classify|guard|text|done","data":{...}}\n\n
"""
import json
import time
import hashlib
import uuid
from uuid import UUID
import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Union, List

from litestar import Controller, post, Request
from litestar.di import Provide
from litestar.response import Stream
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
from backend.database.models import ChatMessage, AgentTelemetryLog
from backend.database.alchemy_config import alchemy_config
from backend.constants.action_vi import ACTION_VI
from backend.utils.data_stripper import DataStripper

logger = logging.getLogger("api-gateway")

# Pre-created session maker for background tasks (V76)
async_session_maker = alchemy_config.create_session_maker()



def _sse(phase: str, data: Dict[str, object]) -> bytes:
    """Format a Server-Sent Event line."""
    return f"data: {json.dumps({'phase': phase, **data}, ensure_ascii=False)}\n\n".encode("utf-8")


# Global background task tracker for memory safety (V76)
background_tasks = set()

class IntentStreamController(Controller):
    """SSE streaming version of IntentController — phased real-time response."""
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

    @post("/stream")
    async def stream_intent(
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
        """Stream intent processing phases via SSE."""

        async def generate() -> AsyncGenerator[bytes, None]:
            start_time = time.monotonic()
            session_id = data.session_id or str(uuid.uuid4())
            user_id = None # Initialize for log safety

            try:
                # ── Yield STT Listening immediately ──
                yield _sse("status", {"step": "stt", "msg": "listening"})

                # Phase 76.3.2: Immediate Transcript Feedback
                # Bắn ngược transcript về UI ngay lập tức để sếp thấy chữ hiện lên
                if data.query:
                    yield _sse("transcript", {"text": data.query})

                # Phase 3 Kill-switch: Empty transcript (Noise rejection)
                if not data.query or not data.query.strip():
                    logger.warning("[SSE] Empty transcript detected. Yielding SLEEP via SESSION_CTRL.")
                    yield _sse("done", {
                        "category": "SESSION_CTRL",
                        "type": "SLEEP",
                        "status": "success",
                        "message": "",
                        "ui_action": ""
                    })

                    # Log noise rejected in background
                    task = asyncio.create_task(_background_save_logs(
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

                # ── Jailbreak scan (STT corrections removed — Groq Whisper handles accuracy) ──
                if not self.shield.scan(data.query):
                    yield _sse("error", {"message": "Lõi nhận thức gián đoạn..."})
                    return

                # ── Resolve user ──
                user_info = getattr(request.state, "user", None)
                user_id = None
                if user_info:
                    # R01.1 Scout Optimization: Use JWT Payload instead of slow DB Query
                    user_id = user_info.get("id")
                    if not user_id and "sub" in user_info:
                        user = await user_repo.get_one_or_none(email=user_info["sub"])
                        if user:
                            user_id = user.id

                # ── Context ──
                recent_msgs = await chat_repo.list(
                    LimitOffset(limit=10, offset=0),
                    session_id=session_id,
                    order_by=[("created_at", "desc")],
                    deleted_at=None
                )
                context: List[Dict[str, str]] = [
                    {"role": m.role, "content": m.content["text"]}
                    for m in reversed(list(recent_msgs))
                    if isinstance(m.content, dict) and "text" in m.content
                ]

                # ── Phase 1: Classify ──
                yield _sse("classify", {"status": "thinking"})

                result = await orchestrator.classify(
                    transcript=data.query,
                    user_id=user_id,
                    app_state=request.app.state,
                    context=context,
                    screen_context=data.screen_context,
                )

                tier_str = str(result.router_tier.value if hasattr(result.router_tier, "value") else result.router_tier)
                yield _sse("classify", {
                    "status": "done",
                    "tier": tier_str,
                    "action": result.action.value if hasattr(result.action, "value") else str(result.action),
                })

                # ── Phase 2: Skill Guard ──
                if user_id and result.status != "error":
                    profile = await profile_repo.get_one_or_none(user_id=user_id)
                    if profile and profile.capabilities:
                        caps = profile.capabilities if isinstance(profile.capabilities, dict) else json.loads(profile.capabilities)
                        action = result.action.value if hasattr(result.action, "value") else result.action
                        check = "READ" if action == "COUNT" else action
                        if not caps.get(check, True):
                            msg = f"Dạ, năng lực '{ACTION_VI.get(action, action)}' đang tạm khóa. Sếp bật lại trong Cài đặt Giọng nói để em hỗ trợ ạ."
                            yield _sse("error", {"message": msg, "restricted": True, "action": action})
                            return

                # ── Phase 3: Execute — Streaming for Voice Truth 2026 ──
                result_category = (result.data or {}).get("category")
                intent_type = (result.data or {}).get("intent_type")
                
                if result.status != "error" and (result_category != "SESSION_CTRL" or intent_type == "UI_NAV"):
                    yield _sse("execute", {"status": "working"})
                    
                    if intent_type in ["DEEP_ANALYSIS", "UNKNOWN"] or result.action.value == "ANALYZE":
                        # ZERO-LATENCY: Stream text chunks for T3
                        full_message = ""
                        async for chunk in orchestrator.t3_router.stream_reason(
                            data.query, context, screen_context=data.screen_context
                        ):
                            full_message += chunk
                            yield _sse("text_delta", {"text": chunk})
                        
                        # Once done, update the result message for the 'done' phase and saving
                        result.message = full_message
                    else:
                        # Non-reasoning tasks (UI_NAV etc.) are usually fast enough
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
                                timeout=45.0  # Increased to 45s to tolerate TrinityBridge 429 backoff & key rotation
                            )
                        except asyncio.TimeoutError:
                            yield _sse("error", {"message": "Giao thức kết nối đang bận, Sếp thử lại sau nhé."})
                            return

                # ── Phase 4: Done — Full response ──
                yield _sse("done", {
                    "status": result.status,
                    "message": result.message,
                    "data": result.data,
                    "ui_action": (result.data or {}).get("ui_action", ""),
                    "action": result.action.value if hasattr(result.action, "value") else str(result.action),
                    "router_tier": tier_str,
                    "cost_tokens": result.cost_tokens,
                    "requires_confirmation": getattr(result, "requires_confirmation", False),
                })

                # ── Background: Telemetry + Chat save ──
                ui_action = (result.data or {}).get("ui_action")

                # Format extra data with Phase 4 Truncate
                data_extra = dict(result.data or {})
                if "error_trace" in data_extra:
                    data_extra["error_trace"] = DataStripper.truncate_payload(str(data_extra["error_trace"]))

                task = asyncio.create_task(_background_save_logs(
                    session_id=session_id, user_id=user_id,
                    data_query=data.query, modality=data.modality,
                    result_message=result.message, result_ui_action=ui_action,
                    tier_str=tier_str, data_extra=data_extra,
                    telemetry_data={
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "agent_name": f"TrinityCore-Tier_{tier_str}",
                        "intent_hash": hashlib.sha256(data.query.lower().strip().encode()).hexdigest()[:16],
                        "input_tokens": getattr(result, "input_tokens", 0),
                        "output_tokens": getattr(result, "output_tokens", 0),
                        "cost_token": float(result.cost_tokens),
                        "duration_ms": int((time.monotonic() - start_time) * 1000)
                    }
                ))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

            except Exception as e:
                logger.exception(f"[SSE Gateway Error] {e}")
                yield _sse("error", {"message": "Giao thức kết nối đang bận, Sếp thử lại sau nhé."})

        return Stream(generate(), media_type="text/event-stream")


async def _background_save_logs(
    session_id: str,
    user_id: Optional[UUID] = None,
    data_query: str = "",
    modality: str = "text",
    result_message: str = "",
    result_ui_action: str = "",
    tier_str: str = "",
    data_extra: Optional[Dict[str, object]] = None,
    telemetry_data: Optional[Dict[str, object]] = None,
    is_noise: bool = False
) -> None:
    try:
        async with async_session_maker() as session:
            telemetry_repo = AgentTelemetryLogRepository(session=session)
            chat_repo = ChatMessageRepository(session=session)
            
            if telemetry_data:
                await telemetry_repo.add(AgentTelemetryLog(**telemetry_data))
            
            if not is_noise:
                await _save(chat_repo, session_id, "user", data_query, None, modality, user_id=user_id)
                await _save(chat_repo, session_id, "assistant", result_message, result_ui_action, modality, tier_str, user_id=user_id, data_extra=data_extra)
            
            await session.commit()
    except Exception as e:
        logger.error(f"[SSE Background Log Error] {e}")


async def _save(chat_repo: ChatMessageRepository, session_id: str, role: str, content: str, ui_action: Optional[str], modality: str, router_tier: Optional[str] = None, user_id: Optional[UUID] = None, data_extra: Optional[Dict[str, object]] = None) -> None:
    payload = {"text": content}
    if ui_action:   payload["ui_action"] = ui_action
    if router_tier: payload["router_tier"] = router_tier
    if data_extra:
        if data_extra.get("category") == "CONTENT_CREATE":
            # Slim log: only audit-trail fields. Heavy data (keywords/assets/outline)
            # lives in content_campaigns table and is fetched on-demand via API.
            for key in ("category", "campaign_id", "step", "status", "action"):
                if data_extra.get(key) is not None:
                    payload[key] = data_extra[key]
        else:
            payload.update(data_extra)

    await chat_repo.add(ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        role=role,
        content=payload,
        modality=modality or "text",
    ))
