import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode, SeoContextualLink

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        pillar_id = '019eb987-b978-7101-82ed-bdb3966878ad'
        stmt = select(SeoContextualLink).where(SeoContextualLink.target_node_id == pillar_id)
        res = await db.execute(stmt)
        links = res.scalars().all()
        print(f"Total links for Beppin Body in DB: {len(links)}")
        for l in links:
            print(f"- ID: {l.id}, Status: {l.status}, Article ID: {l.source_article_id}")

if __name__ == "__main__":
    asyncio.run(main())
