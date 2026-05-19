import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
engine = create_async_engine(db_url)

async def inspect_columns():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'product_bases'"))
        rows = res.fetchall()
        for r in rows:
            print(f"Column: {r[0]} | Type: {r[1]}")

if __name__ == "__main__":
    asyncio.run(inspect_columns())
