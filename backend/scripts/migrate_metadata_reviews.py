import asyncio
import os
import uuid
from dotenv import load_dotenv

# MUST LOAD DOTENV BEFORE IMPORTING ALCHEMY_CONFIG
load_dotenv()

from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.commerce import ProductBase
from backend.database.models.system import SystemReview, ReviewEntityType

async def migrate_reviews():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        # 1. Lấy tất cả sản phẩm
        result = await session.execute(select(ProductBase))
        products = result.scalars().all()
        
        count = 0
        for product in products:
            metadata = product.product_metadata or {}
            reviews_data = metadata.get("reviews", [])
            
            for r in reviews_data:
                review = SystemReview(
                    id=str(uuid.uuid4()),
                    entity_type=ReviewEntityType.PRODUCT,
                    entity_id=product.id,
                    customer_name=r.get("name", "Unknown"),
                    customer_phone=r.get("phone", ""),
                    customer_location=r.get("location", "Việt Nam"),
                    rating=r.get("rating", 5),
                    content=r.get("content", ""),
                    status="APPROVED", 
                    tenant_id=product.tenant_id
                )
                session.add(review)
                count += 1
        
        await session.commit()
        print(f"Migrated {count} reviews from metadata to system_reviews table.")

if __name__ == "__main__":
    asyncio.run(migrate_reviews())
