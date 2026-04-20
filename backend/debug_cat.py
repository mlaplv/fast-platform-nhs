import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, category_metadata FROM categories WHERE slug = 'kem-duong'"))
        row = res.first()
        if row:
            print(f"ID: {row[0]}")
            print(f"NAME: {row[1]}")
            import json
            print(f"METADATA TYPE: {type(row[2])}")
            print(f"METADATA: {row[2]}")
        else:
            print("NOT FOUND")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
