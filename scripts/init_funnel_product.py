import asyncio
import uuid
from sqlalchemy import select
from backend.database.models.commerce import ProductBase
from backend.database.session import async_session_factory

async def init_product():
    async with async_session_factory() as session:
        # Check if product exists
        stmt = select(ProductBase).where(ProductBase.slug == "dac-tri-hoi-nach")
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            print("Product 'dac-tri-hoi-nach' not found. Creating...")
            new_product = ProductBase(
                id=str(uuid.uuid4()),
                name="Xịt Đặc Trị Hôi Nách Clinical Nano",
                description="Công nghệ Nano Bạc 2026 độc quyền từ Clinical Labs. Khô thoáng tức thì, bảo vệ 72H, không để lại vệt vàng trên áo.",
                price=299000.0,
                stock=500,
                status="PUBLISHED",
                slug="dac-tri-hoi-nach",
                seo_title="Xịt Đặc Trị Hôi Nách Clinical Nano - Dứt Điểm Sau 1 Liệu Trình",
                seo_description="Công nghệ Nano Bạc 2026, bảo vệ 72H, không vệt vàng áo.",
                images=["https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8?auto=format&fit=crop&q=80&w=800"] # Reliable placeholder for test
            )
            session.add(new_product)
            await session.commit()
            print(f"Created product: {new_product.id}")
        else:
            print(f"Product already exists: {product.id}")

if __name__ == "__main__":
    asyncio.run(init_product())
