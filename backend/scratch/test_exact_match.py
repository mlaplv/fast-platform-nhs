import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, or_

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
engine = create_async_engine(db_url)

async def test_exact_match():
    async with engine.connect() as conn:
        print("=== TEST EXACT MATCH 'White Label' ===")
        res = await conn.execute(text("""
            SELECT id, name, attributes->>'Thương hiệu'
            FROM product_bases
            WHERE attributes->>'Thương hiệu' = 'White Label'
        """))
        rows = res.fetchall()
        print(f"Exact match '=' count: {len(rows)}")
        for r in rows:
            print(f"- {r[1]}")

        print("\n=== TEST EXACT MATCH 'White+Label' ===")
        res2 = await conn.execute(text("""
            SELECT id, name, attributes->>'Thương hiệu'
            FROM product_bases
            WHERE attributes->>'Thương hiệu' = 'White+Label'
        """))
        rows2 = res2.fetchall()
        print(f"Exact match with '+' count: {len(rows2)}")

if __name__ == "__main__":
    asyncio.run(test_exact_match())
