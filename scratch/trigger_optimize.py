import asyncio
import os
import sys

# Add workspace to path
sys.path.append("/app")

from backend.services.ai_service import ai_service
from backend.database.alchemy_config import alchemy_config
from sqlalchemy import select
from backend.database.models import User

async def run():
    async with alchemy_config.create_session_maker()() as s:
        u = (await s.execute(select(User))).scalars().first()
        if not u:
            print("No user found")
            return
        print(f"Triggering Auto-Optimize for user: {u.id}")
        res = await ai_service.auto_optimize_stack(s, u.id)
        print(f"Result: {res}")

if __name__ == "__main__":
    asyncio.run(run())
