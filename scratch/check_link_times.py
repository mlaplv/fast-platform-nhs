import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config
from sqlalchemy import text

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await db.execute(text("""
            SELECT id, status, updated_at, reviewed_by 
            FROM seo_contextual_links 
            WHERE status IN ('APPROVED', 'REJECTED')
        """))
        rows = res.all()
        print("Approved/Rejected links:")
        for r in rows:
            print(f"- ID: {r.id}, Status: {r.status}, Updated At: {r.updated_at}, Reviewed By: {r.reviewed_by}")

if __name__ == "__main__":
    asyncio.run(run())
