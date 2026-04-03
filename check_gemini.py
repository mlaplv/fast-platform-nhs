import asyncio
from sqlalchemy import select
from backend.database import alchemy_config
from backend.database.models import MediaRegistry

async def check():
    m = alchemy_config.create_session_maker()
    async with m() as s:
        stmt = select(MediaRegistry).where(MediaRegistry.file_path.ilike('%Gemini%'))
        res = await s.execute(stmt)
        for row in res.scalars().all():
            print(f"ID: {row.id} | Path: {row.file_path} | Linked: {row.is_linked} | Created: {row.created_at}")

if __name__ == "__main__":
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
    asyncio.run(check())
