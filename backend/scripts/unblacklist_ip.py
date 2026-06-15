import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import delete

# Add project root to python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker
from backend.database.models.ads import IPBlacklist

async def main():
    async with async_session_maker() as session:
        stmt = delete(IPBlacklist).where(IPBlacklist.ip_address == "127.0.0.1")
        res = await session.execute(stmt)
        await session.commit()
        print("Successfully removed 127.0.0.1 from IPBlacklist")

if __name__ == "__main__":
    asyncio.run(main())
