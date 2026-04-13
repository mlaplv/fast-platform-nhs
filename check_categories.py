import asyncio
import os
from sqlalchemy import select, func
from backend.database import async_session_maker
from backend.database.models import Article
from dotenv import load_dotenv

# Load env to connect to DB
load_dotenv(os.path.abspath(".env"))

async def check_categories():
    async with async_session_maker() as session:
        # Get count of articles for different categories
        stmt = select(Article.category, func.count(Article.id)).group_by(Article.category)
        result = await session.execute(stmt)
        categories = result.all()
        print("Categories found in articles table:")
        for cat, count in categories:
            print(f"- {cat}: {count}")

if __name__ == "__main__":
    asyncio.run(check_categories())
