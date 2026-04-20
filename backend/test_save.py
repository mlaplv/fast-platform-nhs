import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.database.models import Category
from backend.schemas.category import CreateCategoryRequest, CategoryMetadata
from backend.services.commerce.category import CategoryService
from sqlalchemy import select

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Create a dummy category
        metadata = {"faqs": [{"question": "Hỏi?", "answer": "Đáp."}]}
        data = CreateCategoryRequest(
            name="Test FAQ Save",
            slug="test-faq-save",
            metadata=CategoryMetadata(faqs=[{"question": "Hỏi?", "answer": "Đáp."}])
        )
        print(f"REQUEST METADATA: {data.metadata.model_dump()}")
        
        res = await CategoryService.create_category(session, data)
        cat_id = res.id
        print(f"CREATED CAT ID: {cat_id}")
        
        # 2. Fetch it back
        stmt = select(Category).where(Category.id == cat_id)
        result = await session.execute(stmt)
        cat = result.scalar_one()
        print(f"FETCHED METADATA: {cat.category_metadata}")
        
        # Clean up
        from sqlalchemy import delete
        await session.execute(delete(Category).where(Category.id == cat_id))
        await session.commit()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
