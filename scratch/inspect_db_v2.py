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
                # Search for Miccosmo Hurry Harry products
                res = await conn.execute(text("SELECT name, sku, product_metadata FROM product_bases WHERE sku = '968123703603' OR name ILIKE '%Hurry Harry%'"))
                rows = res.fetchall()
                if rows:
                    for row in rows:
                        print(f"NAME: {row[0]}")
                        print(f"SKU: {row[1]}")
                        print(f"METADATA: {json.dumps(row[2], indent=2, ensure_ascii=False)}")
                else:
                    print("No Hurry Harry products found in product_bases")
            await engine.dispose()
            return
        except Exception as e:
            print(f"Failed {host}: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(run())
