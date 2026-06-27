import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoContextualLink
from sqlalchemy import select

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        links = (await db.execute(select(SeoContextualLink).where(SeoContextualLink.target_node_id == '019eb987-b970-7250-8d1e-7a87a9b626c9'))).scalars().all()
        for l in links:
            print(l.id)
            print(repr(l.created_at))

if __name__ == "__main__":
    asyncio.run(main())
