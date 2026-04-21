import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import SupportChatHistory
from backend.utils.security import GeminiSecurity
from sqlalchemy import select

async def check():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        stmt = select(SupportChatHistory).where(SupportChatHistory.session_id == 'test-check-1').order_by(SupportChatHistory.created_at.desc())
        items = (await db.execute(stmt)).scalars().all()
        for i in items:
            print(f"Role: {i.role}, Msg: {GeminiSecurity.decrypt(i.content)}")

if __name__ == "__main__":
    asyncio.run(check())
