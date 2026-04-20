import asyncio
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

from backend.database.models import Category
from backend.services.commerce.category import CategoryService
from backend.schemas.category import UpdateCategoryRequest, CategoryMetadata
from backend.schemas.product import FaqItem

# DB URL from environment for Docker compatibility
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform")

@pytest.mark.asyncio
async def test_category_faq_persistence_and_sync():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Create a test category
        cat_id = str(uuid.uuid4())
        test_cat = Category(
            id=cat_id,
            name="Test FAQ Sync",
            slug=f"test-faq-{cat_id[:8]}",
            category_metadata={"faqs": []}
        )
        session.add(test_cat)
        await session.commit()
        
        # 2. Update with FAQ
        faq_data = [
            FaqItem(question="Q1", answer="A1"),
            FaqItem(question="Q2", answer="A2")
        ]
        update_req = UpdateCategoryRequest(
            metadata=CategoryMetadata(faqs=faq_data)
        )
        
        response = await CategoryService.update_category(session, cat_id, update_req)
        
        # 3. Verify Response structure (Elite V2.2 Compliance)
        assert response.ok is True
        # Check metadata from response.data (CategoryResponse)
        # CategoryResponse.metadata is CategoryMetadata object
        assert len(response.data.metadata.faqs) == 2
        assert response.data.metadata.faqs[0].question == "Q1"
        
        # 4. Verify DB persistence
        stmt = select(Category).where(Category.id == cat_id)
        res = await session.execute(stmt)
        # Expire session to force reload from DB
        session.expire(test_cat)
        db_cat = await session.get(Category, cat_id)
        
        db_metadata = db_cat.category_metadata
        assert "faqs" in db_metadata
        assert len(db_metadata["faqs"]) == 2
        assert db_metadata["faqs"][0]["question"] == "Q1"
        
        # Cleanup
        await session.delete(db_cat)
        await session.commit()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_category_faq_persistence_and_sync())
