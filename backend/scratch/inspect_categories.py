import asyncio
import os
import sys
import json
from dotenv import load_dotenv

project_root = "/home/lv/Desktop/fast-platform-core"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv(os.path.join(project_root, ".env"))

db_url = os.getenv("DATABASE_URL")
if db_url and "@db:" in db_url:
    db_url = db_url.replace("@db:", "@localhost:")
os.environ["DATABASE_URL"] = db_url

from sqlalchemy import text
from backend.database import async_session_maker

async def inspect_db():
    ids = ["test_child_d04ce4", "test_parent_a34f9a", "test_parent_fbb536"]
    async with async_session_maker() as session:
        query = text(
            "SELECT id, name, slug, parent_id, tenant_id, deleted_at, show_on_mobile, show_on_desktop, position, created_at "
            "FROM categories WHERE id = ANY(:ids)"
        )
        res = await session.execute(query, {"ids": ids})
        rows = res.all()
        
        print("--- INSPECT CATEGORIES ---")
        for row in rows:
            print({
                "id": row.id,
                "name": row.name,
                "slug": row.slug,
                "parent_id": row.parent_id,
                "tenant_id": row.tenant_id,
                "deleted_at": str(row.deleted_at) if row.deleted_at else None,
                "show_on_mobile": row.show_on_mobile,
                "show_on_desktop": row.show_on_desktop,
                "position": row.position,
                "created_at": str(row.created_at) if row.created_at else None
            })

if __name__ == "__main__":
    asyncio.run(inspect_db())
