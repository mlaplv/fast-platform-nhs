import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models import Category
from sqlalchemy import select, insert

async def run():
    async with alchemy_config.create_session_maker()() as s:
        res = await s.execute(select(Category).where(Category.slug == "products"))
        row = res.scalar_one_or_none()
        if not row:
            # Create a virtual "All Products" category
            stmt = insert(Category).values(
                id="cat_all_products",
                name="Tất cả sản phẩm",
                slug="products",
                description="Danh mục tổng hợp toàn bộ sản phẩm của hệ thống",
                position=0,
                show_on_mobile=True,
                show_on_desktop=True
            )
            await s.execute(stmt)
            await s.commit()
            print("✅ 'products' category created.")
        else:
            print("ℹ️ 'products' category already exists.")

if __name__ == "__main__":
    asyncio.run(run())
