import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
engine = create_async_engine(db_url)

async def check_metadata_keys():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, product_metadata FROM product_bases WHERE deleted_at IS NULL"))
        rows = res.fetchall()
        for r in rows:
            meta = r[2] or {}
            # Check keys recursively or directly
            found_keys = []
            for k in meta.keys():
                if "brand" in k.lower() or "thương hiệu" in k.lower():
                    found_keys.append(k)
            if found_keys:
                print(f"ID: {r[0]} | Name: {r[1]} has metadata keys: {found_keys} with values {[meta[k] for k in found_keys]}")

if __name__ == "__main__":
    asyncio.run(check_metadata_keys())
