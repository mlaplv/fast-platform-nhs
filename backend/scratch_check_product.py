import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.commerce import ProductBase

async def check():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        print("Checking ProductBase...")
        # Lấy tất cả products có slug tương tự
        stmt = select(ProductBase).where(ProductBase.slug.ilike('%miccosmo%'))
        res = await db.execute(stmt)
        products = res.scalars().all()
        print(f"Found {len(products)} products with slug containing 'miccosmo':")
        for p in products:
            print(f"- ID: {p.id}, Name: {p.name}, Slug: {p.slug}, Status: {p.status}, Deleted: {p.deleted_at}")

        # Lấy tất cả products
        stmt_all = select(ProductBase)
        res_all = await db.execute(stmt_all)
        all_p = res_all.scalars().all()
        print(f"Total products in DB: {len(all_p)}")
        for p in all_p:
            print("="*40)
            print(f"Name: {p.name}")
            print(f"SEO Title: {p.seo_title}")
            print(f"Short Desc: {p.short_description}")
            print(f"Attributes: {p.attributes}")

if __name__ == "__main__":
    asyncio.run(check())
