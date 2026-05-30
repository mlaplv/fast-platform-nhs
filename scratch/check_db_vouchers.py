import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Append project root to path
sys.path.append("/home/lv/Desktop/fast-platform-core")

async def main():
    database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
    # Try localhost first
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT id, title, is_viral, is_active FROM vouchers"))
            vouchers = res.fetchall()
            print("--- Vouchers in DB ---")
            for v in vouchers:
                print(f"ID: {v[0]}, Title: {v[1]}, is_viral: {v[2]}, is_active: {v[3]}")
    except Exception as e:
        print(f"Localhost failed: {e}")
        # Try docker network container name db
        database_url_db = "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform"
        engine_db = create_async_engine(database_url_db)
        try:
            async with engine_db.connect() as conn:
                res = await conn.execute(text("SELECT id, title, is_viral, is_active FROM vouchers"))
                vouchers = res.fetchall()
                print("--- Vouchers in DB (via db host) ---")
                for v in vouchers:
                    print(f"ID: {v[0]}, Title: {v[1]}, is_viral: {v[2]}, is_active: {v[3]}")
        except Exception as ex:
            print(f"Both failed. Host 'db' error: {ex}")

if __name__ == "__main__":
    asyncio.run(main())
