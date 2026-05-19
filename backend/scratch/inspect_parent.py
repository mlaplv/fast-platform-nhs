import asyncio
import os
import sys
from dotenv import load_dotenv

project_root = "/home/lv/Desktop/fast-platform-core"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv(os.path.join(project_root, ".env"))

db_url = os.getenv("DATABASE_URL")
if db_url and "@db:" in db_url:
    db_url = db_url.replace("@db:", "@localhost:")
os.environ["DATABASE_URL"] = db_url

from backend.database import async_session_maker
from backend.database.models import Category
from sqlalchemy import select

async def inspect_parent():
    async with async_session_maker() as session:
        stmt = select(Category).where(Category.id == "test_parent_fbb536")
        res = await session.execute(stmt)
        cat = res.scalar_one_or_none()
        if cat:
            print("--- test_parent_fbb536 ---")
            print(f"ID: {cat.id}")
            print(f"Name: {cat.name}")
            print(f"Slug: {cat.slug}")
            print(f"Parent: {cat.parent_id}")
            print(f"Deleted: {cat.deleted_at}")
            print(f"Tenant: {cat.tenant_id}")
            print(f"Position: {cat.position}")
        else:
            print("Category test_parent_fbb536 not found!")

if __name__ == "__main__":
    asyncio.run(inspect_parent())
