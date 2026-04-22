import sqlite3
import json
import time
# Actually it's Postgres.
import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import UnifiedAgentTask

async def check_task():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        for _ in range(10):
            stmt = select(UnifiedAgentTask).order_by(UnifiedAgentTask.created_at.desc()).limit(1)
            task = await db.scalar(stmt)
            if task and task.status == "DONE":
                print(f"Task Result: {task.result['reply']}")
                return
            print("Waiting for task...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(check_task())
