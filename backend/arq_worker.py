import asyncio
import logging
from typing import Any, Dict
from arq import Retry
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.agent_base import AGENT_REGISTRY
from backend.services.event_bus import event_bus
from backend.infra.arq_config import get_redis_settings

# Ensure all operatives are imported so they register themselves
# (Rule R0.2: Implicit Discovery via Heritage Registry)
import backend.services.commerce.operatives.support_agent
# Note: XOHI agents are also registered but we only call them if agent_id matches.

logger = logging.getLogger("arq-worker")

async def run_agent_task(ctx: Dict[str, Any], agent_id: str, task_id: str, session_id: str, payload: Dict[str, Any]) -> None:
    """
    Elite V2.2: Universal Agent Task Handler (The Brain Worker).
    Runs any registered agent operative in a background process.
    """
    logger.info(f"[Worker] Starting task {task_id} for agent {agent_id}")
    
    # 1. Instantiate the correct operative from the Heritage Registry
    agent_cls = AGENT_REGISTRY.get(agent_id)
    if not agent_cls:
        logger.error(f"[Worker] Agent {agent_id} not found in registry.")
        return

    # 2. Create isolated resource lifecycle (R00 - Dispose Protocol)
    # Each task gets its own DB session to prevent state leakage.
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            agent = agent_cls(agent_id=agent_id)
            
            # 3. Execute the heavy AI logic (RAG + TrinityBridge)
            # We bypass the controller and call the operative directly.
            # We reconstruct the Request object mock if needed, but for arq 
            # we typically pass clean dicts.
            from backend.schemas.support import SupportRequest
            
            # Map payload back to schema for type safety
            request = SupportRequest(**payload)
            
            # R76: Execute the heavy logic directly (bypass the controller/enqueue cycle)
            if hasattr(agent, "process_brain_logic"):
                result = await agent.process_brain_logic(request=request, db=db)
            else:
                # Fallback for simple agents that don't have split tiers
                result = await agent.chat(request=request, db=db)

            
            # 4. Notify the CNS (Central Nervous System) via EventBus
            # This triggers the Pulse SSE stream to update the Client UI.
            if hasattr(result, "model_dump"):
                result_data = result.model_dump()
            else:
                result_data = dict(result)

            await event_bus.emit("SUPPORT_RESPONSE_READY", {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "result": result_data,
                "status": "DONE"
            })
            
            logger.info(f"[Worker] Task {task_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"[Worker] Task {task_id} failed: {e}")
            # Emit failure signal so UI can show error state
            await event_bus.emit("SUPPORT_RESPONSE_READY", {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "status": "FAILED",
                "error": str(e)
            })
            # Optional: Automatic retry for transient Network/API errors
            raise Retry(defer=10)

async def startup(ctx: Dict[str, Any]) -> None:
    logger.info("[Worker] Arq Worker starting up... Elite V2.2 Protocol Active.")
    # Initialize shared resources like TrinityBridge if needed
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    await trinity_bridge.initialize()

async def shutdown(ctx: Dict[str, Any]) -> None:
    logger.info("[Worker] Arq Worker shutting down.")

class WorkerSettings:
    """Arq Worker Configuration (Standardized)."""
    functions = [run_agent_task]
    redis_settings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10  # Protection for 2GB RAM
    job_timeout = 180  # AI can be slow (RAG + Reasoning)
