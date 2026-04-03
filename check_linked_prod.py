import asyncio
from sqlalchemy import select
from backend.database import alchemy_config
from backend.database.models import MediaUsage, MediaRegistry

async def check():
    m = alchemy_config.create_session_maker()
    async with m() as s:
        stmt = select(MediaRegistry.file_path).join(MediaUsage, MediaUsage.asset_id == MediaRegistry.id).where(MediaUsage.entity_id == 'prod_hoi_nach_hong_son')
        res = await s.execute(stmt)
        print(f"Linked Path: {res.scalars().all()}")

if __name__ == "__main__":
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
    asyncio.run(check())
