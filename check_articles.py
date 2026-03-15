
import asyncio
from sqlalchemy import select
from backend.database.models import Article, ContentCampaign
from backend.database.alchemy_config import alchemy_config

async def check():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        print("\n--- [LATEST ARTICLES] ---")
        stmt = select(Article).order_by(Article.created_at.desc()).limit(5)
        res = await session.execute(stmt)
        articles = res.scalars().all()
        for a in articles:
            print(f"ID: {a.id} | Title: {a.title} | Created: {a.created_at}")

        print("\n--- [LATEST CAMPAIGNS] ---")
        stmt = select(ContentCampaign).order_by(ContentCampaign.created_at.desc()).limit(3)
        res = await session.execute(stmt)
        campaigns = res.scalars().all()
        for c in campaigns:
            print(f"ID: {c.id} | Status: {c.status} | Title in Topic: {c.topic_data.get('title') if c.topic_data else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(check())
