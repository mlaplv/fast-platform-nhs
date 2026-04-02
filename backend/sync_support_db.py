
import asyncio
import os
from dotenv import load_dotenv

# Load .env BEFORE importing backend modules that use env vars
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"))

from backend.database import engine
from backend.database.models.system import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-sync")

async def sync():
    try:
        logger.info("[Database] Starting schema sync...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[Database] Sync Complete.")
    except Exception as e:
        logger.error(f"[Database] Sync Failed: {e}")

if __name__ == "__main__":
    asyncio.run(sync())
