import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config
from sqlalchemy import text

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await db.execute(text("SELECT id, title, content FROM articles LIMIT 10"))
        rows = res.all()
        for r in rows:
            print(f"ID: {r.id}")
            print(f"Title: {r.title}")
            print(f"Content Type/Prefix: {type(r.content)} | {repr(r.content[:200]) if r.content else 'None'}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(run())
