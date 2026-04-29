import asyncio
import os
from dotenv import load_dotenv

# Load .env before any database imports
load_dotenv()

# Elite V2.2: Resolve name resolution issue when running outside Docker
if os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL").replace("@db:5432", "@localhost:5432")

from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.content import Category

async def check_category():
    async with async_session_maker() as session:
        stmt = select(Category).where(Category.slug == 'kem-duong')
        res = await session.execute(stmt)
        cat = res.scalar_one_or_none()
        if cat:
            print(f"Category found: ID={cat.id}, Name={cat.name}, Slug={cat.slug}")
        else:
            print("Category 'kem-duong' NOT found in DB")
            
        stmt = select(Category.slug).limit(10)
        res = await session.execute(stmt)
        slugs = res.scalars().all()
        print(f"All category slugs: {slugs}")

if __name__ == "__main__":
    asyncio.run(check_category())
