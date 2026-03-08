"""SSE Streaming Intent Endpoint — Real-time phased response.

Streams classify → guard → execute phases as Server-Sent Events.
Frontend receives chunks immediately instead of waiting 2-5s for full response.

Format: data: {"phase":"classify|guard|text|done","data":{...}}\n\n
"""
import json
import time
import hashlib
import uuid
import asyncio
import logging
from typing import AsyncGenerator

from litestar import Controller, post, Request
from litestar.di import Provide
from litestar.response import Stream
from litestar.repository.filters import LimitOffset
from shared.schemas.intent import IntentRequest, IntentResponse, IntentAction, RouterTier
from src.services.routing.intent_orchestrator import orchestrator
from ai_engine.core.semantic_shield import SemanticShield
from src.database.repositories import (
    UserRepository, ChatMessageRepository, VoiceProfileRepository,
    AgentTelemetryLogRepository, OrderRepository, ProductBaseRepository,
    ContentCampaignRepository,
    provide_user_repo, provide_chat_repo, provide_voice_repo,
    provide_telemetry_repo, provide_order_repo, provide_product_repo,
    provide_campaign_repo
)
from src.database.models import ChatMessage, AgentTelemetryLog
from src.constants.action_vi import ACTION_VI

logger = logging.getLogger("api-gateway")

ACTION_VI = {
    "READ":    "Truy xuất Dữ liệu",
    "COUNT":   "Truy xuất Số liệu",
    "MUTATE":  "Chỉnh sửa Hệ thống",
    "ANALYZE": "Suy luận Chuyên sâu",
}


def _sse(phase: str, data: dict) -> bytes:
    """Format a Server-Sent Event line."""
    return f"data: {json.dumps({'phase': phase, **data}, ensure_ascii=False)}\n\n".encode("utf-8")


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

    def __init__(self, **kwargs):
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

            try:
                # ── Jailbreak scan (STT corrections removed — Groq Whisper handles accuracy) ──
                if not self.shield.scan(data.query):
                    yield _sse("error", {"message": "Lõi nhận thức gián đoạn..."})
                    return

                # ── Resolve user ──
                user_info = getattr(request.state, "user", None)
                user_id = None
                if user_info and "sub" in user_info:
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
                context = [
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
                                    modality=data.modality
                                ),
                                timeout=20.0
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
                try:
                    await telemetry_repo.add(AgentTelemetryLog(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        agent_name=f"TrinityCore-Tier_{tier_str}",
                        intent_hash=hashlib.sha256(data.query.lower().strip().encode()).hexdigest()[:16],
                        input_tokens=getattr(result, "input_tokens", 0),
                        output_tokens=getattr(result, "output_tokens", 0),
                        cost_token=float(result.cost_tokens),
                        duration_ms=int((time.monotonic() - start_time) * 1000)
                    ))
                    await telemetry_repo.session.commit()
                except Exception:
                    pass

                ui_action = (result.data or {}).get("ui_action")
                try:
                    await _save(chat_repo, session_id, "user", data.query, None, data.modality, user_id=user_id)
                    await _save(chat_repo, session_id, "assistant", result.message, ui_action, data.modality, tier_str, user_id=user_id)
                except Exception:
                    pass

            except Exception as e:
                logger.exception(f"[SSE Gateway Error] {e}")
                yield _sse("error", {"message": "Giao thức kết nối đang bận, Sếp thử lại sau nhé."})

        return Stream(generate(), media_type="text/event-stream")


async def _save(chat_repo, session_id, role, content, ui_action, modality, router_tier=None, user_id=None):
    payload = {"text": content}
    if ui_action:   payload["ui_action"] = ui_action
    if router_tier: payload["router_tier"] = router_tier
    await chat_repo.add(ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        role=role,
        content=payload,
        modality=modality or "text",
    ))
    await chat_repo.session.commit()
