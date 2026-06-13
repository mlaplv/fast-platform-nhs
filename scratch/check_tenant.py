import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config
from sqlalchemy import text

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await db.execute(text("SELECT id, tenant_id FROM seo_contextual_links"))
        print("seo_contextual_links:")
        for r in res.all():
            print(f"- ID: {r.id}, Tenant ID: {r.tenant_id}")
            
        res2 = await db.execute(text("SELECT id, tenant_id FROM articles WHERE id = 'art_aging_strategies'"))
        print("articles:")
        for r in res2.all():
            print(f"- ID: {r.id}, Tenant ID: {r.tenant_id}")

if __name__ == "__main__":
    asyncio.run(run())
