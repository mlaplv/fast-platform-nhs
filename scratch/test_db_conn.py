import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import json

async def run():
    # Try common ports
    for host in ["localhost", "db"]:
        try:
            # Use sync engine for simple check or fix the async one
            engine = create_async_engine(f'postgresql+asyncpg://postgres:postgres@{host}:5432/fast_platform')
            async with engine.connect() as conn:
                res = await conn.execute(text("SELECT name, sku FROM products LIMIT 5"))
                rows = res.fetchall()
                for row in rows:
                    print(f"FOUND: {row[0]} | {row[1]}")
            await engine.dispose()
            return
        except Exception as e:
            print(f"Failed {host}: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(run())
