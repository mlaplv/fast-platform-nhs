"""
Nano Orchestrator — Bộ điều phối 3 Tầng (Tier 2 → Tier 3)
==========================================================
Core dispatcher: Semantic Router → Local SLM → Cloud LLM Fallback.
Ghi telemetry vào AgentTelemetryLog (R19) sau mỗi request.

Note: Tier 1 (Heuristic) được xử lý tại API Gateway (IntentController)
trước khi request đến đây. Orchestrator chỉ nhận request đã qua Tier 1.
"""
import asyncio
import hashlib
import json
import logging
import os
import random
import time
import uuid

from pydantic import ValidationError

from shared.schemas.intent import IntentAction, IntentRequest, IntentResponse
from .vector_memory import VectorMemory
from .nanobot import NanoBot
from ai_engine.core.semantic_router import SemanticRouter
from ai_engine.core.local_executor import LocalExecutor
from ai_engine.core.m2m_guard import M2MGuard
from ai_engine.core.redis_memory import RedisMemory
from ai_engine.core.memory_worker import MemoryWorker

logger = logging.getLogger("nano_orchestrator")

TIER2_CONFIDENCE_THRESHOLD = 0.85
TIER3_FALLBACK_THRESHOLD = 0.80
MAX_A2A_TURNS = int(os.getenv("MAX_A2A_TURNS", "5"))

def _intent_hash(query: str) -> str:
    return hashlib.sha256(query.lower().strip().encode()).hexdigest()[:16]

class NanoOrchestrator:
    def __init__(self) -> None:
        self.semantic_router = SemanticRouter()
        self.local_executor = LocalExecutor()
        self.nanobot = NanoBot()
        self.m2m_guard = M2MGuard()
        self.redis_mem = RedisMemory()
        self.worker = MemoryWorker()

    async def process(self, request: IntentRequest) -> IntentResponse:
        start_time, session_id = time.monotonic(), request.session_id or str(uuid.uuid4())
        intent_hash_val, response, resolved_tier = _intent_hash(request.query), None, 3

        await self.m2m_guard.check_circuit_breaker(session_id)

        key = f"a2a:turns:{session_id}"
        try: # R10: A2A Deadlock Guard
            if (turn_count := int(await self.m2m_guard.redis.get(key) or 0)) >= MAX_A2A_TURNS:
                raise PermissionError(f"[A2A PANIC] Limit exceeded ({turn_count}/{MAX_A2A_TURNS}).")
            await self.m2m_guard.redis.incr(key)
            await self.m2m_guard.redis.expire(key, 86400)
        except AttributeError: pass

        try:
            # 1. Redis Memory: Sliding Window (N=6) & Slot-Filling
            history = await self.redis_mem.get_history(session_id)
            partial = await self.redis_mem.get_partial_intent(session_id)
            
            if partial:
                request.query = f"[CONTEXT: {json.dumps(partial)}] {request.query}"
                await self.redis_mem.clear_partial_intent(session_id)

            # 2. Intent Detection (Tier 2 Semantic Router)
            try:
                intent_name, conf = await self.semantic_router.classify(request.query)
            except Exception as e:
                logger.warning(f"[Tier 2] Semantic Router failed, falling back: {e}")
                intent_name, conf = "unknown", 0.0
            
            # 3. Context Retrieval (RAG - Phase 3)
            from src.database import db
            rag_context = ""
            
            # Specialized Knowledge Retrieval
            if intent_name == "product_search" or "sản phẩm" in request.query.lower():
                rag_context += f"\n--- THÔNG TIN SẢN PHẨM ---\n{await VectorMemory.search(request.query, db, context_type='product')}"
            
            if intent_name == "article_search" or any(x in request.query.lower() for x in ["chính sách", "quy định", "tin tức"]):
                rag_context += f"\n--- CHÍNH SÁCH & TIN TỨC ---\n{await VectorMemory.search(request.query, db, context_type='article')}"
            
            # Long-term memory logic could be added here as well
            
            # Augment system prompt or message with context
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history])
            augmented_query = f"Lịch sử:\n{history_str}\n\nTri thức hiện có:{rag_context}\n\nHãy trả lời yêu cầu này của người dùng: {request.query}"
            
            original_query = request.query
            request.query = augmented_query
            response = await self.nanobot.analyze(request)
            
            # 4. Handle Slot-Filling (Test Case 2)
            if "cần thêm thông tin" in response.message.lower() or response.data.get("ui_action") == "AWAIT_CLARIFICATION":
                await self.redis_mem.store_partial_intent(session_id, {"last_query": original_query})
            
            # 5. Save turn to Redis (Sliding Window N=6)
            await self.redis_mem.add_message(session_id, "user", original_query)
            await self.redis_mem.add_message(session_id, "assistant", response.message)

            # 6. Background Worker: Fact Extraction (Test Case 3)
            new_history = await self.redis_mem.get_history(session_id)
            asyncio.create_task(self.worker.summarize_and_store(session_id, new_history))
            resolved_tier = 3

        except Exception as e:
            logger.error(f"[Orchestrator] Error: {e}")
            response = IntentResponse(status="error", action=IntentAction.READ, message=f"Error: {e}", router_tier=3)

        finally:
            cost = response.cost_tokens if response else 0.0
            await self._log_telemetry(session_id, intent_hash_val, cost, int((time.monotonic() - start_time) * 1000), resolved_tier)
            await self.m2m_guard.report_burn(session_id, int(cost))

        return response

    async def stream_process(self, request: IntentRequest):
        """Streaming Generator bằng LiteLLM (Tier 3), có fallback qua Tier 2"""
        from litellm import acompletion
        import os
        
        start_time, session_id = time.monotonic(), request.session_id or str(uuid.uuid4())
        intent_hash_val = _intent_hash(request.query)
        resolved_tier = 3

        # 1. Thử Tier 2 (Semantic) trước khi gọi Cloud LLM
        try:
            intent_name, conf = await self.semantic_router.classify(request.query)
            logger.info(f"[Tier2 Stream] intent={intent_name}, conf={conf:.3f}")
            if conf >= TIER2_CONFIDENCE_THRESHOLD:
                # Local Executor
                t2_response = await self.local_executor.execute(intent_name, request.query)
                if t2_response and t2_response.message:
                    resolved_tier = 2
                    yield t2_response.message
                    # Fire telemetry for Tier 2 and return
                    import asyncio
                    asyncio.create_task(self._log_telemetry(session_id, intent_hash_val, 0.0, int((time.monotonic() - start_time) * 1000), 2))
                    return
        except Exception as e:
            logger.warning(f"[Tier2 Stream] Fallback loop due to: {e}")

        # 2. Tier 3 (Cloud LLM Stream) with Key Rotation Fallback
        model_name = os.getenv("CLOUD_LLM_MODEL") or f"gemini/{os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview')}"
        api_keys = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]
        if not api_keys:
            api_keys = [None]
            
        response = None
        last_error = None
        
        for key in api_keys:
            try:
                response = await acompletion(
                    model=model_name,
                    messages=[{"role": "user", "content": request.query}],
                    api_key=key,
                    stream=True
                )
                break
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if getattr(e, "status_code", 500) in (401, 429) or "quota" in err_str or "auth" in err_str or "key" in err_str:
                    logger.warning(f"[Tier3 Stream] Key ended with '{str(key)[-4:] if key else None}' failed/exhausted. Rotating to next key...")
                    continue
                break
                
        if response is None and last_error:
            logger.error(f"[Tier3 Stream] All AI keys exhausted or failed: {last_error}")
            yield "Hệ thống AI đang quá tải lượt truy cập. Vui lòng thử lại sau vài giây."
            return
        
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
                
        # Fire and forget telemetry
        cost = getattr(response, "_hidden_params", {}).get("response_cost", 0.0)
        import asyncio
        asyncio.create_task(self._log_telemetry(session_id, intent_hash_val, cost, int((time.monotonic() - start_time) * 1000), 3))
        asyncio.create_task(self.m2m_guard.report_burn(session_id, int(cost)))

    async def process_with_memory(self, transcript: str, context_window: list) -> IntentResponse:
        """
        GIAI ĐOẠN 2: Nano-Core Vector Retrieval & Augmented Generation
        """
        try:
            from src.database import db # Import db client
            
            # 1. Tra cứu trí nhớ dài hạn (PGVector)
            memory_ctx = await VectorMemory.search(transcript, db)
            
            # 2. Nhồi vào prompt (Augmented Generation)
            augmented_query = f"Bối cảnh trí nhớ:\n{memory_ctx}\n\nNgười dùng mới nói: {transcript}"
            
            # 3. Chạy qua NanoBot Tier 3
            bot = NanoBot()
            return await bot.analyze(IntentRequest(query=augmented_query, modality="voice"))
        except Exception as e:
            logger.error(f"[NanoOrchestrator] Error parsing memory logic: {e}")
            from shared.schemas.intent import IntentAction
            return IntentResponse(
                status="error",
                action=IntentAction.READ,
                message="Oops! Hệ thống tư duy của tôi gặp chút rắc rối, sếp đợi một lát thử lại nhé.",
                data={},
                router_tier=3,
                cost_tokens=0.0
            )

    async def _log_telemetry(self, session_id: str, intent_hash: str, cost: float, duration_ms: int, tier: int) -> None:
        try:
            from src.database import db
            await db.agenttelemetrylog.create(data={
                "sessionId": session_id,
                "agentName": f"NanoOrchestrator-Tier{tier}",
                "intentHash": intent_hash,
                "inputTokens": int(tier > 2),
                "outputTokens": int(tier > 2),
                "costToken": cost,
                "durationMs": duration_ms,
            })
        except Exception as e:
            logger.warning(f"[Telemetry] Failed: {e}")
