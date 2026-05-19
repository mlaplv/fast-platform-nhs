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

from sqlalchemy import text
from backend.database import async_session_maker

async def delete_temp_categories():
    async with async_session_maker() as session:
        # Delete child first, then parents to avoid Foreign Key constraints
        print("Executing deletion of temporary categories...")
        # We delete child first
        res1 = await session.execute(text("DELETE FROM categories WHERE id = 'test_child_d04ce4'"))
        print(f"Deleted child test_child_d04ce4: {res1.rowcount} row(s)")
        
        # We delete parents
        res2 = await session.execute(text("DELETE FROM categories WHERE id IN ('test_parent_a34f9a', 'test_parent_fbb536')"))
        print(f"Deleted parents (test_parent_a34f9a, test_parent_fbb536): {res2.rowcount} row(s)")
        
        await session.commit()
        print("Transaction committed successfully.")

if __name__ == "__main__":
    asyncio.run(delete_temp_categories())
