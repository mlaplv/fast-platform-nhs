import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models import ProductBase

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
        stmt = select(ProductBase).where(ProductBase.slug == slug)
        product = await db.scalar(stmt)
        if product:
            print("Attributes:")
            print(product.attributes)
            print("\nProduct Metadata:")
            print(product.product_metadata)
        else:
            print("Product not found!")

if __name__ == "__main__":
    asyncio.run(main())
