import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models import Category
from sqlalchemy import select, insert, delete

async def run():
    async with alchemy_config.create_session_maker()() as s:
        # First, find a category from micsmo.com to confirm tenant_id
        res = await s.execute(select(Category).where(Category.tenant_id == "micsmo.com").limit(1))
        sample = res.scalar_one_or_none()
        tenant = "micsmo.com" if sample else "default"
        
        # Clean up the previous 'default' one to avoid confusion if needed, 
        # but better to just add the correct one.
        
        res = await s.execute(select(Category).where(Category.slug == "products", Category.tenant_id == tenant))
        row = res.scalar_one_or_none()
        if not row:
            # Create a virtual "All Products" category for the active tenant
            stmt = insert(Category).values(
                id=f"cat_all_products_{tenant.replace('.', '_')}",
                name="Tất cả sản phẩm",
                slug="products",
                description="Danh mục tổng hợp toàn bộ sản phẩm của hệ thống",
                position=0,
                show_on_mobile=True,
                show_on_desktop=True,
                tenant_id=tenant
            )
            await s.execute(stmt)
            await s.commit()
            print(f"✅ 'products' category created for tenant '{tenant}'.")
        else:
            print(f"ℹ️ 'products' category already exists for tenant '{tenant}'.")

if __name__ == "__main__":
    asyncio.run(run())
