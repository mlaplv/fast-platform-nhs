import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoContextualLink

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await db.execute(select(SeoContextualLink).order_by(SeoContextualLink.created_at.desc()))
        links = res.scalars().all()
        print(f"Total links in DB: {len(links)}")
        for l in links:
            st = l.status if isinstance(l.status, str) else l.status.value
            print(f"ID: {l.id} | Tenant: {l.tenant_id} | Status: {st} | Entity: {l.matched_entity_name} | Article: {l.source_article_id} | Node: {l.target_node_id}")

if __name__ == "__main__":
    asyncio.run(main())
