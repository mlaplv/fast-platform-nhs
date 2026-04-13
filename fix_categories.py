import asyncio
import os
from sqlalchemy import select, update
from backend.database import async_session_maker
from backend.database.models import Article
from dotenv import load_dotenv

# Load env to connect to DB
load_dotenv(os.path.abspath(".env"))

async def fix_categories():
    async with async_session_maker() as session:
        # Check
        stmt = select(Article.category).distinct()
        res = await session.execute(stmt)
        cats = res.scalars().all()
        print(f"Categories found: {cats}")

        # Update if necessary
        if "Tin tức" in cats:
            print("Found 'Tin tức', updating to 'Bài viết'...")
            stmt = update(Article).where(Article.category == "Tin tức").values(category="Bài viết")
            await session.execute(stmt)
            await session.commit()
            print("Updated!")
        else:
            print("No 'Tin tức' category found.")

if __name__ == "__main__":
    asyncio.run(fix_categories())
