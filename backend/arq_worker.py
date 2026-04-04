import asyncio
import logging
from typing import Dict
from arq import Retry
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import UnifiedAgentTask
from backend.services.ai_engine.core.agent_base import AGENT_REGISTRY
from backend.services.event_bus import event_bus
from backend.infra.arq_config import get_redis_settings
from sqlalchemy import update
from datetime import datetime, timezone

# Ensure all operatives are imported so they register themselves (R0.2)
import backend.services.commerce.operatives.support_agent
import backend.services.xohi.creative_studio.operatives.plagiarism_cop
from backend.infra.jobs import cleanup_old_tasks
# Add other XoHi agents to ensure registration if needed

logger = logging.getLogger("neural-worker")

async def run_agent_task(ctx: Dict[str, object], agent_id: str, task_id: str, session_id: str, payload: Dict[str, object]) -> None:
    """
    Elite V2.2: Universal Agent Task Handler (The Brain Worker).
    Runs any registered agent operative in a background process with DB persistence.
    """
    from sqlalchemy import select, update
    from backend.database import current_tenant_id
    from backend.services.ai_engine.core.semantic_cache import semantic_cache

    t0 = datetime.now(timezone.utc)
    job_try = ctx.get('job_try', 1)
    logger.info(f"🧠 [Neural Worker] Starting task {task_id} (Try {job_try}) for agent {agent_id} (S: {session_id})")
    
    session_maker = alchemy_config.create_session_maker()
    token_ctx = None

    try:
        # [R00 - DISPOSE] Check Semantic Cache BEFORE touching heavy resources
        cached_res = await semantic_cache.get_cached_result(agent_id, payload)
        if cached_res:
            async with session_maker() as cache_db:
                await cache_db.execute(
                    update(UnifiedAgentTask)
                    .where(UnifiedAgentTask.task_id == task_id)
                    .values(status="DONE", result=cached_res, completed_at=datetime.now(timezone.utc))
                )
                await cache_db.commit()
            
            # Emit signals for cached result
            await event_bus.emit("AGENT_TASK_COMPLETED", {"task_id": task_id, "session_id": session_id, "agent_id": agent_id, "status": "DONE"})
            if agent_id == "support_agent":
                await event_bus.emit("SUPPORT_RESPONSE_READY", {"session_id": session_id, "task_id": task_id, "reply": cached_res.get("reply"), "intent": cached_res.get("intent"), "status": "DONE"})
            return

        # 1. Update status to RUNNING in DB and RESTORE TENANT CONTEXT
        async with session_maker() as db:
            stmt = select(UnifiedAgentTask).where(UnifiedAgentTask.task_id == task_id)
            res = await db.execute(stmt)
            task_obj = res.scalar_one_or_none()
            
            if not task_obj:
                logger.error(f"[Worker] Task {task_id} not found in DB.")
                return

            # Standardize Multi-Tenancy (Elite V2.2)
            token_ctx = current_tenant_id.set(task_obj.tenant_id or "default")
            
            task_obj.status = "RUNNING"
            await db.commit()

        # 2. Instantiate the correct operative from the Heritage Registry
        agent_cls = AGENT_REGISTRY.get(agent_id)
        if not agent_cls:
            error_msg = f"Agent {agent_id} not found in registry."
            logger.error(f"[Worker] {error_msg}")
            async with session_maker() as db:
                await db.execute(
                    update(UnifiedAgentTask)
                    .where(UnifiedAgentTask.task_id == task_id)
                    .values(status="FAILED", error=error_msg, completed_at=datetime.now(timezone.utc))
                )
                await db.commit()
            return

        # 3. Create isolated resource lifecycle (R00 - Dispose Protocol)
        async with session_maker() as db:
            agent = agent_cls(agent_id=agent_id)
            
            # Dynamic Schema Mapping (Elite V2.2 Rule R88)
            schema_cls = agent.get_schema()
            if schema_cls:
                request = schema_cls(**payload)
            else:
                request = payload if isinstance(payload, dict) else payload

            # 4. Execute the heavy AI logic
            if hasattr(agent, "process_brain_logic"):
                result = await agent.process_brain_logic(request=request, db=db)
            else:
                result = await agent.chat(request=request, db=db)

            # 5. Save results to DB
            result_data = result.model_dump() if hasattr(result, "model_dump") else (result.dict() if hasattr(result, "dict") else dict(result))
            
            await db.execute(
                update(UnifiedAgentTask)
                .where(UnifiedAgentTask.task_id == task_id)
                .values(status="DONE", result=result_data, completed_at=datetime.now(timezone.utc))
            )

            # [Elite 2026] Cache successful result
            await semantic_cache.set_cached_result(agent_id, payload, result_data)

            await db.commit()

            # 6. Universal Completion Signal (Central Nervous System)
            await event_bus.emit("AGENT_TASK_COMPLETED", {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "status": "DONE"
            })
            
            if agent_id == "support_agent":
                await event_bus.emit("SUPPORT_RESPONSE_READY", {
                    "session_id": session_id,
                    "task_id": task_id,
                    "reply": result_data.get("reply"),
                    "intent": result_data.get("intent"),
                    "status": "DONE"
                })
            
            duration = (datetime.now(timezone.utc) - t0).total_seconds()
            logger.info(f"✅ [Neural Worker] Task {task_id} completed successfully in {duration:.2f}s.")
            
    except Exception as e:
        logger.error(f"❌ [Worker] Task {task_id} failed during execution: {e}", exc_info=True)
        # Rollback is handled by session_maker's async context but we update status as FAILED
        try:
            async with session_maker() as fail_db:
                await fail_db.execute(
                    update(UnifiedAgentTask)
                    .where(UnifiedAgentTask.task_id == task_id)
                    .values(
                        status="FAILED", 
                        error=str(e), 
                        completed_at=datetime.now(timezone.utc)
                    )
                )
                await fail_db.commit()
        except Exception as dbe:
            logger.critical(f"💀 [Worker] CRITICAL: Could not update task {task_id} status to FAILED: {dbe}")

        # Emit failure signal
        await event_bus.emit("AGENT_TASK_COMPLETED", {
            "task_id": task_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "FAILED",
            "error": str(e)
        })
        
        # [Elite V2.2] Exponential Backoff for transient Network/API errors
        error_str = str(e).lower()
        if any(trigger in error_str for trigger in ["429", "timeout", "overloaded", "limiter"]):
            # Calc exponential backoff: 30s, 60s, 120s...
            defer_time = 15 * (2 ** (job_try - 1))
            logger.warning(f"🔄 [Worker] Retrying task {task_id} in {defer_time}s due to transient error: {e}")
            raise Retry(defer=defer_time)
    finally:
        if token_ctx:
            current_tenant_id.reset(token_ctx)

async def startup(ctx: Dict[str, object]) -> None:
    logger.info("🚀 [Neural Worker] Arq Worker starting up... Elite V2.2 Protocol Active.")
    # Initialize shared resources like TrinityBridge if needed
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    await trinity_bridge.initialize()

async def shutdown(ctx: Dict[str, object]) -> None:
    logger.info("[Worker] Arq Worker shutting down.")

from arq import cron

class WorkerSettings:
    """Arq Base Configuration (Elite V2.2)."""
    functions = [run_agent_task]
    redis_settings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    # Tuning for 4GB RAM VPS
    max_jobs = 20  
    job_timeout = 300
    keep_result = 3600

class WorkerHighSettings(WorkerSettings):
    """Priority Worker for Helen (Client Support)."""
    queue_name = "high"
    functions = [run_agent_task]
    redis_settings = get_redis_settings() # Explicitly call again to be safe
    max_jobs = 10

class WorkerDefaultSettings(WorkerSettings):
    """Standard Worker for XoHi (Creative Studio)."""
    queue_name = "default"
    functions = [run_agent_task]
    redis_settings = get_redis_settings() # Explicitly call again to be safe
    max_jobs = 5
    cron_jobs = [
        # Schedule cleanup at 3:00 AM every day
        cron(cleanup_old_tasks, hour=3, minute=0)
    ]
