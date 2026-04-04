import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import UnifiedAgentTask

logger = logging.getLogger("arq-worker")

async def cleanup_old_tasks(ctx: dict) -> None:
    """
    Elite V2.2: Retention Policy Enforcement (3-day limit).
    Deletes tasks and logs older than 3 days to protect SSD space.
    """
    logger.info("[Cleanup] Starting 3-day retention enforcement...")
    
    # Calculate cutoff (3 days ago)
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    
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
