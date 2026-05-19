import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import async_session_maker
from backend.services.commerce.category import CategoryService

async def main():
    async with async_session_maker() as session:
        # Clear cache first to be sure
        await CategoryService._invalidate_cache()
        response = await CategoryService.list_categories(session)
        print("Total Roots:", response.total)
        def print_tree(cats, level=0):
            for c in cats:
                print("  " * level + f"- {c.name} (ID: {c.id}, children: {len(c.children)})")
                print_tree(c.children, level + 1)
        print_tree(response.data)

asyncio.run(main())
