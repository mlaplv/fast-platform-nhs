import asyncio
import sys
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoContextualLink, SeoNode

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        links = (await db.execute(
            select(SeoContextualLink)
        )).scalars().all()
        
        print(f"Total links: {len(links)}")
        for l in links:
            print(f"ID: {l.id} | Article: {l.source_article_id} | Target: {l.target_node_id} | Anchor: {l.anchor_text} | Type: {l.matched_entity_type} | Status: {l.status} | Created: {l.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
