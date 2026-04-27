import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models import Category
from sqlalchemy import select

async def run():
    async with alchemy_config.create_session_maker()() as s:
        res = await s.execute(select(Category))
        rows = res.scalars().all()
        print(f"Categories found: {len(rows)}")
        for r in rows:
            print(f"- {r.slug} (ID: {r.id}, Tenant: {r.tenant_id})")

if __name__ == "__main__":
    asyncio.run(run())
