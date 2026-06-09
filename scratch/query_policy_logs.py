import asyncio
import os
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.ads import AIPolicyAuditLog

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        stmt = select(AIPolicyAuditLog)
        res = await session.execute(stmt)
        logs = res.scalars().all()
        print(f"Total audit logs found: {len(logs)}")
        for log in logs[:20]:
            print(f"ID: {log.id}, AdGroup: {log.ad_group_id}, Score: {log.score}, Created: {log.created_at}")

if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if db_url and "@db:" in db_url:
        os.environ["DATABASE_URL"] = db_url.replace("@db:", "@127.0.0.1:")
    asyncio.run(main())
