import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def run():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT name, sku, attributes->>'brand' as brand_attr, product_metadata->>'brand' as brand_meta FROM product_bases WHERE sku = '968123703603'"))
        row = res.fetchone()
        if row:
            print(f"NAME: {row[0]}")
            print(f"SKU: {row[1]}")
            print(f"BRAND_ATTR: {row[2]}")
            print(f"BRAND_META: {row[3]}")
        else:
            print("Product NOT FOUND")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
