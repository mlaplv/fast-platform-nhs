import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode, SeoContextualLink

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # Get all pending links
        stmt = select(SeoContextualLink).where(SeoContextualLink.status == "pending")
        res = await db.execute(stmt)
        links = res.scalars().all()
        print(f"TOTAL PENDING LINKS IN DB: {len(links)}")
        for l in links:
            stmt_node = select(SeoNode.node_label).where(SeoNode.id == l.target_node_id)
            lbl = await db.scalar(stmt_node)
            print(f"- ID: {l.id}, Created: {l.created_at}, Target: '{lbl}', Anchor: {l.anchor_text}")

if __name__ == "__main__":
    asyncio.run(main())
