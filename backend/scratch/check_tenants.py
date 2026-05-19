import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
engine = create_async_engine(db_url)

async def check_tenants():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, tenant_id FROM product_bases WHERE deleted_at IS NULL"))
        rows = res.fetchall()
        for r in rows:
            print(f"ID: {r[0]} | Name: {r[1]} | tenant_id: {r[2]}")

if __name__ == "__main__":
    asyncio.run(check_tenants())
