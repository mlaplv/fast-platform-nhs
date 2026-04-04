import os
import asyncio
import uuid
import logging

# [CRITICAL] Setup environment BEFORE any backend imports
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"

from datetime import datetime, timezone
from sqlalchemy import select
from backend.services.commerce.operatives.support_agent import support_agent
from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import UnifiedAgentTask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("async-verify")

async def verify():
    print("\n" + "="*80)
    print("🚀 ELITE V2.2 ASYNC ARCHITECTURE VERIFICATION (Phases 1-4)")
    print("="*80 + "\n")

    session_id = f"test-session-{uuid.uuid4().hex[:6]}"
    
    # 1. Test Helen (HIGH PRIORITY)
    print(f"[HELEN] Enqueueing high-priority task for session {session_id}...")
    helen_payload = {"message": "Dư vấn nách", "session_id": session_id, "product_slug": "hoi-nach-helen"}
    h_task_id = await support_agent.enqueue_chat(helen_payload, session_id)
    print(f"✅ Helen task enqueued: {h_task_id}")

    # 2. Test XoHi (DEFAULT PRIORITY)
    print(f"\n[XOHI] Enqueueing standard task for session {session_id}...")
    xohi = PlagiarismCop()
    xohi_payload = {"campaign_id": "test-campaign-123", "force": True} # Note: may fail if ID doesn't exist but we check task status
    x_task_id = await xohi.enqueue_chat(xohi_payload, session_id)
    print(f"✅ XoHi task enqueued: {x_task_id}")

    # 3. Verification in DB
    print("\n[DB] Verifying task persistence...")
    await asyncio.sleep(2) # Give it a moment
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        for tid, label in [(h_task_id, "Helen"), (x_task_id, "XoHi")]:
            stmt = select(UnifiedAgentTask).where(UnifiedAgentTask.task_id == tid)
            res = await db.execute(stmt)
            task = res.scalar_one_or_none()
            if task:
                print(f"✨ {label} Task {tid}: Status={task.status}")
                if task.status == "FAILED":
                    print(f"   ❌ Error: {task.error}")
            else:
                print(f"❌ {label} Task {tid} NOT FOUND in DB!")

    print("\n[WORKER] Waiting for worker to process (Check docker logs if it hangs)...")
    await asyncio.sleep(10)
    
    async with session_maker() as db:
        for tid, label in [(h_task_id, "Helen"), (x_task_id, "XoHi")]:
            stmt = select(UnifiedAgentTask).where(UnifiedAgentTask.task_id == tid)
            res = await db.execute(stmt)
            task = res.scalar_one_or_none()
            if task and task.status in ["DONE", "FAILED"]:
                print(f"🏁 {label} Task {tid}: Status={task.status}")
                if task.status == "DONE":
                    print(f"   📦 Result keys: {list(task.result.keys()) if task.result else 'None'}")
                else:
                    print(f"   ❌ Error: {task.error}")

    print("\n" + "="*80)
    print("🏁 ASYNC VERIFICATION COMPLETED")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(verify())
