import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, update
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

async def generate_review_kg_job(ctx: Dict[str, object], review_id: str) -> None:
    """
    Elite V2.2: Asynchronous Knowledge Graph Generation.
    Offloads heavy LLM entity extraction from HTTP transaction to background worker.
    """
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models.system import SystemReview
    from backend.services.xohi.creative_studio.operatives.kg_generator import generate_knowledge_graph
    from sqlalchemy.orm.attributes import flag_modified
    
    logger.info(f"🧬 [Review KG Job] Starting entity extraction for review {review_id} in background.")
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            review = await db.get(SystemReview, review_id)
            if not review:
                logger.warning(f"🧬 [Review KG Job] Review {review_id} not found.")
                return
                
            # Call LLM externally without holding active HTTP transactions
            kg_data = await generate_knowledge_graph(
                content=review.content,
                topic=f"Đánh giá từ {review.customer_name} cho {review.entity_type} {review.entity_id}"
            )
            
            # Explicit update in separate transaction
            if not review.attributes:
                review.attributes = {}
            review.attributes["knowledge_graph"] = kg_data
            flag_modified(review, "attributes")
            
            await db.commit()
            logger.info(f"🧬 [Review KG Job] Successfully generated and stored Knowledge Graph for review {review_id}.")
        except Exception as e:
            logger.error(f"🧬 [Review KG Job] Failed to generate Knowledge Graph: {e}")
            await db.rollback()


async def cleanup_old_notifications(ctx: Dict[str, object]) -> None:
    """
    Elite V2.2: Retention Policy Enforcement for Notifications.
    1. Loads configuration from Redis cache (fallback to system_settings / default: 7 days soft delete, 14 days hard delete).
    2. Performs soft delete for notifications older than soft_delete_days.
    3. Performs hard delete for soft-deleted notifications older than hard_delete_days in chunks of 5000.
    """
    logger.info("[Cleanup Notifications] Starting execution...")
    
    from backend.database.models.system import SystemSetting, Notification
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            soft_days = 7
            hard_days = 14
            
            try:
                from backend.services.xohi_memory import xohi_memory
                import json
                cached = await xohi_memory.client.get("system:notification_retention")
                if cached:
                    config = json.loads(cached)
                    soft_days = int(config.get("soft_delete_days", 7))
                    hard_days = int(config.get("hard_delete_days", 14))
                    logger.info("[Cleanup Notifications] Loaded retention policy from Redis cache.")
                else:
                    stmt = select(SystemSetting).where(SystemSetting.key == "notification_retention")
                    setting = (await db.execute(stmt)).scalar_one_or_none()
                    if setting and isinstance(setting.value, dict):
                        soft_days = int(setting.value.get("soft_delete_days", 7))
                        hard_days = int(setting.value.get("hard_delete_days", 14))
                        await xohi_memory.client.set("system:notification_retention", json.dumps(setting.value))
            except Exception as e:
                logger.warning(f"[Cleanup Notifications] Failed to read settings from Redis, falling back to DB/Defaults: {e}")
                from sqlalchemy import select
                stmt = select(SystemSetting).where(SystemSetting.key == "notification_retention")
                setting = (await db.execute(stmt)).scalar_one_or_none()
                if setting and isinstance(setting.value, dict):
                    soft_days = int(setting.value.get("soft_delete_days", 7))
                    hard_days = int(setting.value.get("hard_delete_days", 14))
                
            logger.info(f"[Cleanup Notifications] Retention configuration: soft={soft_days} days, hard={hard_days} days.")
            
            now = datetime.now(timezone.utc)
            soft_cutoff = now - timedelta(days=soft_days)
            hard_cutoff = now - timedelta(days=hard_days)
            
            # Step 1: Soft Delete (Set deleted_at for active notifications older than soft_cutoff)
            soft_stmt = (
                update(Notification)
                .where(Notification.deleted_at == None)
                .where(Notification.created_at < soft_cutoff)
                .values(deleted_at=now)
            )
            soft_res = await db.execute(soft_stmt)
            await db.commit()
            
            # Step 2: Hard Delete (Purge soft-deleted notifications older than hard_cutoff in chunks to release locks)
            from sqlalchemy import select
            total_hard_deleted = 0
            while True:
                subq = (
                    select(Notification.id)
                    .where(Notification.deleted_at != None)
                    .where(Notification.deleted_at < hard_cutoff)
                    .limit(5000)
                    .scalar_subquery()
                )
                hard_stmt = delete(Notification).where(Notification.id.in_(subq))
                hard_res = await db.execute(hard_stmt)
                count = hard_res.rowcount
                total_hard_deleted += count
                await db.commit()
                if count < 5000:
                    break
            
            logger.info(
                f"[Cleanup Notifications] Process completed. "
                f"Soft-deleted: {soft_res.rowcount} notifications. "
                f"Hard-deleted: {total_hard_deleted} notifications."
            )
        except Exception as e:
            logger.error(f"[Cleanup Notifications] Failed during cleanup execution: {e}")
            await db.rollback()

