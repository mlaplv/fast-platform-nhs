import asyncio
import os
import sys

sys.path.insert(0, "/app")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform")

async def main():
    print("Starting manual SEO fields migration...")
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        print("Executing ALTER TABLE statements...")
        await conn.execute(text("ALTER TABLE seo_contextual_links ADD COLUMN IF NOT EXISTS link_title VARCHAR(255);"))
        await conn.execute(text("ALTER TABLE seo_contextual_links ADD COLUMN IF NOT EXISTS link_target VARCHAR(20);"))
        print("SEO fields migration successful!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
