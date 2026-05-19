import asyncio
import os
import sys
import uuid
from dotenv import load_dotenv

project_root = "/home/lv/Desktop/fast-platform-core"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv(os.path.join(project_root, ".env"))

db_url = os.getenv("DATABASE_URL")
if db_url and "@db:" in db_url:
    db_url = db_url.replace("@db:", "@localhost:")
os.environ["DATABASE_URL"] = db_url

# Override Redis URL for local execution
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from backend.database import async_session_maker
from backend.database.models import Category
from backend.services.commerce.category import CategoryService

async def test_full_lifecycle():
    async with async_session_maker() as session:
        # Create a parent category
        parent_id = f"test_parent_{uuid.uuid4().hex[:6]}"
        parent = Category(
            id=parent_id,
            name="Test Temporary Parent",
            slug=f"temp-parent-{uuid.uuid4().hex[:6]}",
            position=0
        )
        session.add(parent)
        await session.commit()
        print(f"Created Parent Category: {parent_id}")

        # Check if parent is deletable (should be, since it has no products and no children)
        deletable, blocked = await CategoryService._check_deletable(session, [parent_id], include_soft_deleted_children=True)
        print(f"Is parent hard-deletable? {'Yes' if parent_id in deletable else 'No'} (Expected: Yes)")

        # Now, create a child category under it
        child_id = f"test_child_{uuid.uuid4().hex[:6]}"
        child = Category(
            id=child_id,
            name="Test Temporary Child",
            slug=f"temp-child-{uuid.uuid4().hex[:6]}",
            parent_id=parent_id,
            position=0
        )
        session.add(child)
        await session.commit()
        print(f"Created Child Category: {child_id} under {parent_id}")

        # Check parent deletability again (should be BLOCKED because it now has a child)
        deletable, blocked = await CategoryService._check_deletable(session, [parent_id], include_soft_deleted_children=True)
        print(f"Is parent hard-deletable now? {'Yes' if parent_id in deletable else 'No'} (Expected: No, blocked)")

        # Check child deletability (should be Yes, since child is a leaf and has no products)
        deletable, blocked = await CategoryService._check_deletable(session, [child_id], include_soft_deleted_children=True)
        print(f"Is child hard-deletable? {'Yes' if child_id in deletable else 'No'} (Expected: Yes)")

        # Hard-delete the child category first using the service
        print("Invoking hard deletion of child category via service...")
        await CategoryService.hard_delete_category(session, child_id)
        await session.commit()
        print("Child category hard-deleted successfully.")

        # Check parent deletability again after hard-delete of child (should be Yes, because child is fully deleted!)
        deletable, blocked = await CategoryService._check_deletable(session, [parent_id], include_soft_deleted_children=True)
        print(f"Is parent hard-deletable after child hard-deleted? {'Yes' if parent_id in deletable else 'No'} (Expected: Yes)")

        # Hard-delete the parent category (purge it from DB)
        print("Hard-deleting the parent category...")
        await CategoryService.hard_delete_category(session, parent_id)
        await session.commit()
        print("Database cleanup & flow verification finished successfully.")

if __name__ == "__main__":
    asyncio.run(test_full_lifecycle())
