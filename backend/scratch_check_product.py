import asyncio
from sqlalchemy import select
from backend.database.config import alchemy_config
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
        stmt_all = select(ProductBase.name, ProductBase.slug, ProductBase.status, ProductBase.deleted_at)
        res_all = await db.execute(stmt_all)
        all_p = res_all.all()
        print(f"Total products in DB: {len(all_p)}")
        for name, slug, status, deleted in all_p[:30]:
            print(f"  * {name} | Slug: {slug} | Status: {status} | Deleted: {deleted}")

if __name__ == "__main__":
    asyncio.run(check())
