import asyncio
import os
import sys

PROJECT_ROOT = "/app"
sys.path.insert(0, PROJECT_ROOT)

from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import SupportChatHistory
from sqlalchemy import select, func

async def check_history():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        cnt_stmt = select(func.count()).select_from(SupportChatHistory)
        cnt = (await db.execute(cnt_stmt)).scalar()
        print(f"Total rows in support_chat_histories: {cnt}")
        
        stmt = select(SupportChatHistory).order_by(SupportChatHistory.created_at.desc()).limit(5)
        res = await db.execute(stmt)
        rows = res.scalars().all()
        for r in rows:
            print(f"Row ID: {r.id} | Session: {r.session_id} | Role: {r.role} | Created: {r.created_at}")

if __name__ == "__main__":
    asyncio.run(check_history())
