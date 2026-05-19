import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
engine = create_async_engine(db_url)

async def check_brands():
    async with engine.connect() as conn:
        print("=== UNIQUE ATTRIBUTES KEYS ===")
        # Get sample of attributes
        res = await conn.execute(text("SELECT attributes FROM product_bases WHERE attributes IS NOT NULL LIMIT 20"))
        keys = set()
        for row in res.fetchall():
            if row[0]:
                keys.update(row[0].keys())
        print(f"Detected Keys in attributes: {keys}")

        print("\n=== DISTINCT VALUES FOR 'brand' OR 'Thương hiệu' ===")
        # Query distinct values
        res_brand = await conn.execute(text("SELECT DISTINCT attributes->>'brand' FROM product_bases WHERE attributes->>'brand' IS NOT NULL"))
        print("Distinct 'brand' values:")
        for r in res_brand.fetchall():
            print(f"- {r[0]}")

        res_th = await conn.execute(text("SELECT DISTINCT attributes->>'Thương hiệu' FROM product_bases WHERE attributes->>'Thương hiệu' IS NOT NULL"))
        print("Distinct 'Thương hiệu' values:")
        for r in res_th.fetchall():
            print(f"- {r[0]}")

        print("\n=== MATCHING PRODUCTS FOR 'White Label' ===")
        res_match = await conn.execute(text("""
            SELECT id, name, attributes->>'brand', attributes->>'Thương hiệu' 
            FROM product_bases 
            WHERE (attributes->>'brand' ILIKE '%White%' OR attributes->>'Thương hiệu' ILIKE '%White%')
        """))
        rows = res_match.fetchall()
        print(f"Found {len(rows)} matching products:")
        for r in rows:
            print(f"ID: {r[0]} | Name: {r[1]} | brand: {r[2]} | Thương hiệu: {r[3]}")

if __name__ == "__main__":
    asyncio.run(check_brands())
