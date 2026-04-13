import os
import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path: sys.path.insert(0, project_root)

import asyncio
from backend.database import async_session_maker
from backend.database.models import Article
from sqlalchemy import select

async def check():
    async with async_session_maker() as session:
        res = await session.execute(select(Article.title).where(Article.category == "Chính sách"))
        policies = res.scalars().all()
        print(f"Existing policies: {policies}")

if __name__ == "__main__":
    asyncio.run(check())
