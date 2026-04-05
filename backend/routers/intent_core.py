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
        """Core logic for streaming intent processing phases via SSE (Standardized V2.2)."""

        async def generate() -> AsyncGenerator[bytes, None]:
            from backend.routers.intent_utils import async_session_maker
            
            start_time_mono = time.monotonic()
            session_id = data.session_id or str(uuid.uuid4())
            user_id: Optional[str] = None
            
            # R82.1: Lifecycle Management
            max_age = 300  # 5-minute hard cut-off for intent streams (Real-time safety)

            classify_task: Optional[asyncio.Task] = None
            exec_task: Optional[asyncio.Task] = None

            # [Elite V2.2] Total Session Control: Use a local session for the entire stream lifecycle.
            # This bypasses DI-scoped session leaks during abrupt cancellations.
            async with async_session_maker() as session:
                # Initialize local repositories
                l_user_repo = UserRepository(session=session)
                l_chat_repo = ChatMessageRepository(session=session)
                l_profile_repo = VoiceProfileRepository(session=session)
                l_order_repo = OrderRepository(session=session)
                l_product_repo = ProductBaseRepository(session=session)
                l_campaign_repo = ContentCampaignRepository(session=session)

                try:
                    # ── Yield initial protocol signal ──
                    yield sse("sync", {"status": "connected"})
                    yield sse("status", {"step": "stt", "msg": "listening"})

                    # Phase 76.3.2: Immediate Transcript Feedback
                    if data.query:
                        yield sse("transcript", {"text": data.query})

                    # Phase 3 Kill-switch: Empty transcript
                    if not data.query or not data.query.strip():
                        logger.warning("[SSE] Empty transcript detected.")
                        yield sse("done", {
                            "category": "SESSION_CTRL",
                            "type": "SLEEP",
                            "status": "success",
                            "message": "",
                            "ui_action": ""
                        })
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
                            user = await l_user_repo.get_one_or_none(email=cast(str, user_info["sub"]))
                            if user:
                                user_id = str(user.id)

                    # ── Context ──
                    recent_msgs = await l_chat_repo.list(
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
                    # R82: Heartbeat Wrapper for AI Wait
                    async def run_classify():
                        return await orchestrator.classify(
                            db=session,
                            transcript=data.query,
                            user_id=user_id or "default",
                            app_state=cast(Dict[str, object], request.app.state),
                            context=context,
                            screen_context=data.screen_context,
                        )
                    
                    classify_task = asyncio.create_task(run_classify())
                    while not classify_task.done():
                        try:
                            result = await asyncio.wait_for(asyncio.shield(classify_task), timeout=15.0)
                        except asyncio.TimeoutError:
                            # R82: Standardized Heartbeat during AI Thinking
                            yield b": ping (thinking)\n\n"
                            # Check max age
                            if (time.monotonic() - start_time_mono) > max_age:
                                classify_task.cancel()
                                yield sse("error", {"message": "Dịch vụ phản hồi quá chậm, Sếp thử lại nhé."})
                                return
                    
                    result = cast(IntentResponse, classify_task.result())
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
                        profile = await l_profile_repo.get_one_or_none(user_id=user_id)
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
                            # Reasoning stream already acts as heartbeat by yielding chunks
                            async for chunk in orchestrator.t3_router.stream_reason(
                                data.query, context, screen_context=data.screen_context
                            ):
                                full_message += chunk
                                yield sse("text_delta", {"text": chunk})
                            result.message = full_message
                        else:
                            effective_transcript = cast(str, intent_data.get("effective_transcript", data.query))
                            
                            # R82: Heartbeat Wrapper for AI Execution with Nuclear Session Isolation
                            async def run_execute():
                                # We use a nested safe context for the execution task
                                async with async_session_maker() as t_session:
                                    t_user_repo = UserRepository(session=t_session)
                                    t_order_repo = OrderRepository(session=t_session)
                                    t_product_repo = ProductBaseRepository(session=t_session)
                                    t_campaign_repo = ContentCampaignRepository(session=t_session)
                                    
                                    res_exec = await orchestrator.execute(
                                        classification=result,
                                        transcript=effective_transcript,
                                        context=context,
                                        screen_context=data.screen_context,
                                        user_repo=t_user_repo,
                                        order_repo=t_order_repo,
                                        product_repo=t_product_repo,
                                        campaign_repo=t_campaign_repo,
                                        modality=data.modality,
                                        user_id=user_id
                                    )
                                    await t_session.commit()
                                    return res_exec
                            
                            exec_task = asyncio.create_task(run_execute())
                            while not exec_task.done():
                                try:
                                    result = await asyncio.wait_for(asyncio.shield(exec_task), timeout=15.0)
                                except asyncio.TimeoutError:
                                    yield b": ping (working)\n\n"
                                    if (time.monotonic() - start_time_mono) > max_age:
                                        exec_task.cancel()
                                        yield sse("error", {"message": "Thời gian xử lý vượt quá giới hạn."})
                                        return
                            
                            result = cast(IntentResponse, exec_task.result())

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

                    # ── Background Logging ──
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
                            "duration_ms": int((time.monotonic() - start_time_mono) * 1000)
                        }
                    ))
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)

                    # Commit the main stream session before finishing
                    await session.commit()

                except (asyncio.CancelledError, GeneratorExit):
                    logger.debug(f"[SSE] Stream disconnected for session {session_id}")
                    return
                except Exception as e:
                    logger.exception(f"[SSE Gateway Error] {e}")
                    yield sse("error", {"message": "Giao thức kết nối đang bận, Sếp thử lại sau nhé."})
                finally:
                    # [R82.2] Hard Cleanup for Shielded Tasks
                    # We use asyncio.shield to ensure cleanup is non-interruptible
                    async def safe_cleanup():
                        nonlocal classify_task, exec_task
                        for t in [classify_task, exec_task]:
                            if t and not t.done():
                                t.cancel()
                                try:
                                    await t
                                except asyncio.CancelledError:
                                    pass
                                except Exception as cleanup_error:
                                    logger.error(f"[Cleanup Error] Task failed to cancel gracefully: {cleanup_error}")
                        classify_task = None
                        exec_task = None

                    await asyncio.shield(safe_cleanup())

        # R90: Explicit SSE Headers
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        }
        return Stream(generate(), media_type="text/event-stream", headers=headers)
