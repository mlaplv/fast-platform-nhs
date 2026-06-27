import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoContextualLink

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        links = (await db.execute(
            select(SeoContextualLink).where(
                SeoContextualLink.target_node_id == "019eb987-b970-7250-8d1e-7a87a9b626c9"
            )
        )).scalars().all()
        
        print(f"Total links: {len(links)}")
        for l in links:
            created_str = l.created_at.isoformat() if l.created_at else "None"
            print(f"ID: {l.id} | Status: {l.status} | Tenant: {l.tenant_id} | Created: {created_str}")

if __name__ == "__main__":
    asyncio.run(main())
