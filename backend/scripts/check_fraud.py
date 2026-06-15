import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import select

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
from backend.database.models.ads import ClickFraudEvent

async def main():
    async with async_session_maker() as session:
        stmt = select(ClickFraudEvent).order_by(ClickFraudEvent.created_at.desc())
        res = await session.execute(stmt)
        events = res.scalars().all()
        print(f"Total events: {len(events)}")
        for e in events:
            print(f"ID: {e.id} | Created: {e.created_at} | IP: {e.ip_address} | Verdict: {e.verdict} | Reported: {e.reported_to_google} | Batch: {e.investigation_batch_id}")

if __name__ == "__main__":
    asyncio.run(main())
