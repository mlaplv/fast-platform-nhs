import asyncio
from sqlalchemy import select
from backend.database import alchemy_config
from backend.database.models import MediaRegistry

async def check():
    m = alchemy_config.create_session_maker()
    async with m() as s:
        stmt = select(MediaRegistry.tenant_id).limit(10)
        res = await s.execute(stmt)
        print(f"Tenants in Registry: {res.scalars().all()}")

if __name__ == "__main__":
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
    asyncio.run(check())
