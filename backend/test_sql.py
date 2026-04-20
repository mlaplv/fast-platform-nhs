import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.database.models import Category
from sqlalchemy import select, update

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create
        new_cat = Category(id="test_sql_1", name="Test SQL", slug="test-sql-1", category_metadata={"faqs": [{"q": "1"}]})
        session.add(new_cat)
        await session.commit()
        print("CREATED")

        # Update
        new_meta = {"faqs": [{"q": "2"}]}
        stmt = update(Category).where(Category.id == "test_sql_1").values(category_metadata=new_meta)
        await session.execute(stmt)
        await session.commit()
        print("UPDATED RAW")

        # Fetch
        stmt = select(Category).where(Category.id == "test_sql_1")
        res = await session.execute(stmt)
        cat = res.scalar_one()
        print(f"FETCHED: {cat.category_metadata}")

        # Delete
        from sqlalchemy import delete
        await session.execute(delete(Category).where(Category.id == "test_sql_1"))
        await session.commit()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
