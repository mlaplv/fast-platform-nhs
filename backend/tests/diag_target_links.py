import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoContextualLink

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await db.execute(select(SeoContextualLink).where(SeoContextualLink.target_node_id == "019eb987-b996-7388-8ab2-479eb8f5bdfe"))
        links = res.scalars().all()
        print(f"Links targeting 019eb987-b996-7388-8ab2-479eb8f5bdfe: {len(links)}")
        for l in links:
            print(f" -> Link ID: {l.id} | Anchor: {l.anchor_text} | Status: {l.status}")

if __name__ == "__main__":
    asyncio.run(main())
