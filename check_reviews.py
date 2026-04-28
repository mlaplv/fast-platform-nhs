import asyncio
import os
from sqlalchemy import select, func
from backend.database import async_session_maker
from backend.database.models.system import SystemReview

async def check_reviews():
    async with async_session_maker() as session:
        stmt = select(func.count()).select_from(SystemReview).where(SystemReview.entity_type == 'CATEGORY')
        count = await session.scalar(stmt)
        print(f"Total CATEGORY reviews: {count}")
        
        stmt = select(SystemReview.entity_id).where(SystemReview.entity_type == 'CATEGORY').limit(5)
        res = await session.execute(stmt)
        ids = res.scalars().all()
        print(f"Sample Category IDs with reviews: {ids}")

if __name__ == "__main__":
    asyncio.run(check_reviews())
