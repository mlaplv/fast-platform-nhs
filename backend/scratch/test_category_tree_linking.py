import asyncio
import os
import sys

project_root = "/home/lv/Desktop/fast-platform-core"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

db_url = os.getenv("DATABASE_URL")
if db_url and "@db:" in db_url:
    db_url = db_url.replace("@db:", "@localhost:")
os.environ["DATABASE_URL"] = db_url

from redis.asyncio import Redis
import backend.services.xohi_memory
backend.services.xohi_memory.xohi_memory.client = Redis.from_url("redis://localhost:6379/0")

from backend.database import async_session_maker, current_tenant_id
from backend.services.commerce.category import category_service

async def main():
    async with async_session_maker() as session:
        current_tenant_id.set("default")
        await category_service._invalidate_cache()
        response = await category_service.list_categories(session)
        print("Total Roots:", response.total)
        def print_tree(cats, level=0):
            for c in cats:
                print("  " * level + f"- {c.name} (ID: {c.id}, children: {len(c.children)})")
                print_tree(c.children, level + 1)
        print_tree(response.data)

if __name__ == "__main__":
    asyncio.run(main())
