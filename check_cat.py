from sqlalchemy import select
from backend.database.models import Article
from backend.database.session import AsyncSessionLocal
import asyncio

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Article.category).distinct())
        print(f"Categories: {result.scalars().all()}")
asyncio.run(main())
