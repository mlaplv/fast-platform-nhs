import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def check():
    db_url = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/fast_platform')
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT key, value FROM system_settings"))
        rows = res.fetchall()
        for row in rows:
            print(f"KEY: {row[0]}")
            print(f"VALUE: {json.dumps(row[1], indent=2, ensure_ascii=False)}")
            print("-" * 50)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
