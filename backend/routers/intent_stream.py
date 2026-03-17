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
from litestar.response import Stream

from backend.schemas.intent import IntentRequest, IntentResponse, IntentAction, RouterTier
from backend.services.routing.intent_orchestrator import orchestrator
from backend.services.ai_engine.core.semantic_shield import SemanticShield
from backend.services.user_service import user_service
from backend.services.chat_service import chat_service
from backend.services.telemetry_service import telemetry_service
from backend.services.xohi_memory import xohi_memory
from backend.database.models import ChatMessage, AgentTelemetryLog
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.alchemy_config import alchemy_config
from backend.constants.action_vi import ACTION_VI
from backend.utils.data_stripper import DataStripper

logger = logging.getLogger("api-gateway")

# Pre-created session maker for background tasks (V76)
async_session_maker = alchemy_config.create_session_maker()


def _sse(phase: str, data: Dict[str, object]) -> bytes:
    """Format a Server-Sent Event line."""
    return f"data: {json.dumps({'phase': phase, **data}, ensure_ascii=False)}\n\n".encode("utf-8")


class IntentStreamController(Controller):
    """SSE streaming version of IntentController — phased real-time response."""
    path = "/api/v1/intent"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.shield = SemanticShield()

    @post("/stream")
    async def stream_intent(
        self,
        request: Request,
        data: IntentRequest,
        db_session: AsyncSession,
    ) -> Stream:
        """Stream intent processing phases via SSE."""

        async def generate() -> AsyncGenerator[bytes, None]:
            start_time = time.monotonic()
            session_id = data.session_id or str(uuid.uuid4())
            user_id = None

            try:
                # ── Yield STT Listening immediately ──
                yield _sse("status", {"step": "stt", "msg": "listening"})

                # Phase 76.3.2: Immediate Transcript Feedback
                if data.query:
                    yield _sse("transcript", {"text": data.query})

                # Phase 3 Kill-switch: Empty transcript
                if not data.query or not data.query.strip():
                    yield _sse("done", {
                        "category": "SESSION_CTRL",
                        "type": "SLEEP",
                        "status": "success",
                        "message": "",
                        "ui_action": ""
                    })
                    return

                # ── Jailbreak scan ──
                if not self.shield.scan(data.query):
                    yield _sse("error", {"message": "Lõi nhận thức gián đoạn..."})
                    return

                # ── Resolve user ──
                user_info = getattr(request.state, "user", None)
                if user_info:
                    user_id = user_info.get("id")
                    if not user_id and "sub" in user_info:
                        user = await user_service.get_user_by_email(db_session, user_info["sub"])
                        if user:
                            user_id = str(user.id)

                # ── Lịch sử hội thoại (Elite V2.2 Service-based) ──
                context = await chat_service.get_recent_messages(db_session, session_id, limit=10)

                # ── Phase 1: Classify ──
                result = await orchestrator.classify(
                    transcript=data.query,
                    user_id=user_id,
                    app_state=request.app.state,
                    context=context,
                    screen_context=data.screen_context,
                )

                tier_str = str(result.router_tier.value if hasattr(result.router_tier, "value") else result.router_tier)

                if tier_str != "1":
                    yield _sse("classify", {"status": "thinking"})

                yield _sse("classify", {
                    "status": "done",
                    "tier": tier_str,
                    "action": result.action.value if hasattr(result.action, "value") else str(result.action),
                })

                # ── Phase 2: Skill Guard (XOHI Zero-Hydration) ──
                if user_id and result.status != "error":
                    profile = await xohi_memory.get_voice_profile(user_id)
                    if profile and profile.get("capabilities"):
                        caps = profile["capabilities"] if isinstance(profile["capabilities"], dict) else json.loads(profile["capabilities"])
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

                    if intent_type in ["DEEP_ANALYSIS", "UNKNOWN"] or result.action == IntentAction.ANALYZE:
                        # ZERO-LATENCY: Stream text chunks for T3
                        full_message = ""
                        async for chunk in orchestrator.t3_router.stream_reason(
                            data.query, context, screen_context=data.screen_context
                        ):
                            full_message += chunk
                            yield _sse("text_delta", {"text": chunk})
                        result.message = full_message
                    else:
                        effective_transcript = (result.data or {}).get("effective_transcript", data.query)
                        try:
                            result = await asyncio.wait_for(
                                orchestrator.execute(
                                    classification=result,
                                    transcript=effective_transcript,
                                    context=context,
                                    screen_context=data.screen_context,
                                    db_session=db_session,
                                    modality=data.modality,
                                    user_id=user_id
                                ),
                                timeout=45.0
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
                    "requires_confirmation": getattr(result, "requires_confirmation", False) or result.data.get("requires_confirmation", False),
                    "behavior": "listen" if (getattr(result, "requires_confirmation", False) or result.data.get("action") == "STT_CONFIRM") else "sleep"
                })

                # ── Background: Ghost Auditing ──
                asyncio.create_task(_ghost_audit(
                    session_id=session_id,
                    user_id=user_id,
                    query=data.query,
                    result=result,
                    tier_str=tier_str,
                    start_time=start_time,
                    modality=data.modality
                ))

            except Exception as e:
                logger.exception(f"[SSE Gateway Error] {e}")
                yield _sse("error", {"message": "Giao thức kết nối đang bận, Sếp thử lại sau nhé."})

        return Stream(generate(), media_type="text/event-stream")


async def _ghost_audit(
    session_id: str,
    user_id: Optional[str],
    query: str,
    result: IntentResponse,
    tier_str: str,
    start_time: float,
    modality: str = "text"
) -> None:
    """Non-blocking persistence using Services (Elite V2.2)"""
    try:
        async with async_session_maker() as session:
            # 1. Telemetry
            await telemetry_service.log_telemetry(
                session,
                session_id,
                f"TrinityCore-Tier_{tier_str}",
                hashlib.sha256(query.lower().strip().encode()).hexdigest()[:16],
                getattr(result, "input_tokens", 0),
                getattr(result, "output_tokens", 0),
                float(result.cost_tokens),
                int((time.monotonic() - start_time) * 1000)
            )

            # 2. Chat Persistence
            # User message
            await chat_service.save_message(session, session_id, "user", query, user_id=user_id, modality=modality)

            # Assistant message
            action_val = result.action.value if hasattr(result.action, "value") else result.action
            if action_val != "CONTENT_CREATE":
                ui_action = (result.data or {}).get("ui_action")
                payload_extra = {"ui_action": ui_action, "router_tier": tier_str, **(result.data or {})}
                await chat_service.save_message(
                    session, session_id, "assistant", result.message,
                    user_id=user_id, modality=modality, data_extra=payload_extra
                )
    except Exception as e:
        logger.error(f"[Ghost Audit Error] {e}")

