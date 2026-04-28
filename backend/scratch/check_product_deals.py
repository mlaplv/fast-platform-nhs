
import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import ProductBase
import json

async def check():
    async with async_session_maker() as session:
        query = select(ProductBase).where(ProductBase.name.like("%Beppin Body Virgin White Serum%"))
        product = (await session.execute(query)).scalar_one_or_none()
        if product:
            print(f"Product: {product.name}")
            print(f"Metadata: {json.dumps(product.product_metadata, indent=2, ensure_ascii=False)}")
            
            # Check variants too
            from backend.database.models.commerce import ProductVariant
            query_v = select(ProductVariant).where(ProductVariant.product_id == product.id)
            variants = (await session.execute(query_v)).scalars().all()
            for v in variants:
                print(f"Variant: {v.sku}, Attributes: {v.attributes}")
        else:
            print("Product not found")

if __name__ == "__main__":
    asyncio.run(check())
