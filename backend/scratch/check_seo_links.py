import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode, SeoContextualLink

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        stmt_links = select(SeoContextualLink.tenant_id).distinct()
        res_links = await db.execute(stmt_links)
        print("LINK TENANTS:", res_links.scalars().all())

        stmt_nodes = select(SeoNode.tenant_id).distinct()
        res_nodes = await db.execute(stmt_nodes)
        print("NODE TENANTS:", res_nodes.scalars().all())

if __name__ == "__main__":
    asyncio.run(main())
