import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database import async_session_maker
from src.database.models import Role

async def check_all():
    async with async_session_maker() as session:
        stmt = select(Role).options(selectinload(Role.permissions))
        res = await session.execute(stmt)
        roles = res.scalars().all()
        for r in roles:
            print(f"ROLE_ID: {r.id}, CODE: {r.code}")
            print(f"  PERMS: {[p.code for p in r.permissions]}")

if __name__ == "__main__":
    asyncio.run(check_all())
