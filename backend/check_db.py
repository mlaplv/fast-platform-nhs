import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'categories' AND column_name = 'category_metadata'"))
        exists = res.scalar() is not None
        print(f"COLUMN EXISTS: {exists}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
