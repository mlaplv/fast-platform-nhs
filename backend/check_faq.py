import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT category_metadata FROM categories WHERE slug = 'kem-duong'"))
        row = res.first()
        if row:
            print(f"METADATA FOR KEM-DUONG: {row[0]}")
        else:
            print("CATEGORY KEM-DUONG NOT FOUND")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
