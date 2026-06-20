import os
import sys
import asyncio
from pathlib import Path

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker
from backend.database.models import User
from sqlalchemy import select

async def main():
    async with async_session_maker() as session:
        stmt = select(User.id, User.email, User.username, User.status, User.tenant_id)
        res = await session.execute(stmt)
        users = res.all()
        print("="*50)
        print("DATABASE USERS:")
        print("="*50)
        for u in users:
            print(f"ID: {u.id} | Email: {u.email} | Username: {u.username} | Status: {u.status} | Tenant: {u.tenant_id}")

if __name__ == "__main__":
    asyncio.run(main())
