import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import json

async def run():
    # Try common ports
    for host in ["localhost", "db"]:
        try:
            engine = create_async_engine(f'postgresql+asyncpg://postgres:postgres@{host}:5432/fast_platform')
            async with engine.connect() as conn:
                res = await conn.execute(text("SELECT name, sku, product_metadata FROM products WHERE sku = '968123703603' OR name LIKE '%Hurry Harry%' LIMIT 1"))
                row = res.fetchone()
                if row:
                    print(f"NAME: {row[0]}")
                    print(f"SKU: {row[1]}")
                    print(f"METADATA: {json.dumps(row[2], indent=2, ensure_ascii=False)}")
                    return
            await engine.dispose()
        except Exception as e:
            continue
    print("Product not found in DB or DB unreachable")

if __name__ == "__main__":
    asyncio.run(run())
