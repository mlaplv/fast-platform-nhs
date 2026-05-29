import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import UnifiedAgentTask

logger = logging.getLogger("arq-worker")

async def cleanup_old_tasks(ctx: Dict[str, object]) -> None:
    """
    Elite V2.2: Retention Policy Enforcement (3-day limit).
    Deletes tasks and logs older than 3 days to protect SSD space.
    """
    logger.info("[Cleanup] Starting 3-day retention enforcement...")
    
    from backend.constants.infra import INFRA_RETENTION_DAYS
    # Calculate cutoff (Standard Elite Retention Policy)
    cutoff = datetime.now(timezone.utc) - timedelta(days=INFRA_RETENTION_DAYS)
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            # Delete tasks older than 3 days
            stmt = delete(UnifiedAgentTask).where(UnifiedAgentTask.created_at < cutoff)
            result = await db.execute(stmt)
            await db.commit()
            
            count = result.rowcount
            logger.info(f"[Cleanup] Successfully purged {count} old tasks from DB.")
        except Exception as e:
            logger.error(f"[Cleanup] Failed to purge old tasks: {e}")
            await db.rollback()

async def helen_follow_up_job(ctx: Dict[str, object], session_id: str) -> None:
    """
    Elite V2.2: Proactive Support Engagement.
    Scheduled 1 hour after Helen's reply to re-engage silent users.
    """
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models.system import SupportChatHistory
    from sqlalchemy import select, desc
    
    logger.info(f"🌸 [Helen Follow-up] Checking session {session_id} for proactive reminder.")
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            # Check last message role
            stmt = (
                select(SupportChatHistory)
                .where(SupportChatHistory.session_id == session_id)
                .order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id))
                .limit(1)
            )
            res = await db.execute(stmt)
            last_msg = res.scalar_one_or_none()
            
            if last_msg and last_msg.role == "assistant":
                # Helen was the last speaker, and the user hasn't responded for 1 hour
                logger.info(f"🌸 [Helen Follow-up] User silent for 1h in {session_id}. Triggering Helen...")
                
                # Late import to avoid circular dependencies
                from backend.services.commerce.operatives.support_agent import support_agent
                from backend.schemas.support import SupportRequest
                
                from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER
                # Special internal trigger message (Elite V2.2)
                trigger_req = SupportRequest(
                    message=HELEN_FOLLOW_UP_TRIGGER,
                    session_id=session_id,
                    product_slug=last_msg.product_slug
                )
                
                # Inject a 'thought' event via event_bus before processing
                from backend.services.event_bus import event_bus
                await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang chủ động chăm sóc Quý khách..."})
                
                # This will run the AI logic (Layer 2) and emit SUPPORT_RESPONSE_READY
                await support_agent.process_brain_logic(trigger_req, db)
                await db.commit()
            else:
                logger.info(f"🌸 [Helen Follow-up] Execution skipped: User already replied or no history for {session_id}.")
        except Exception as e:
            logger.error(f"🌸 [Helen Follow-up] CRITICAL FAILURE: {e}")
            await db.rollback()

async def helen_self_learning_job(ctx: Dict[str, object]) -> None:
    """
    Elite V3.5: Arq-based batch processor for automated chat transcript distillation.
    Extracts Q&A candidate structures from recent conversations.
    """
    logger.info("🧠 [Self-Learning Job] Commencing chat transcript distillation sequence...")
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            from backend.services.commerce.self_learning import helen_self_learning
            stats = await helen_self_learning.run_auto_learning(db, limit_sessions=50)
            logger.info(f"🧠 [Self-Learning Job] Finished thưa sếp: Scanned={stats.get('scanned')}, Synthesized={stats.get('synthesized')}, Persisted={stats.get('persisted_to_sandbox')}")
        except Exception as e:
            logger.error(f"🧠 [Self-Learning Job] Distillation process failed: {e}")
            await db.rollback()
