import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
engine = create_async_engine(db_url)

async def check_all_products():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, status, attributes->>'brand', attributes->>'Thương hiệu' FROM product_bases WHERE deleted_at IS NULL"))
        rows = res.fetchall()
        print(f"Total active products in database: {len(rows)}")
        for r in rows:
            print(f"ID: {r[0]} | Name: {r[1]} | status: {r[2]} | brand: {r[3]} | Thương hiệu: {r[4]}")

if __name__ == "__main__":
    asyncio.run(check_all_products())
