import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import ProductBase

async def main():
    async with async_session_maker() as session:
        stmt = select(ProductBase)
        res = await session.execute(stmt)
        products = res.scalars().all()
        print(f"Total Products: {len(products)}")
        for p in products:
            meta = p.product_metadata or {}
            share_promo = meta.get("share_promotion") or {}
            viral_suite = meta.get("viral_suite") or {}
            print(
                f"ID: {p.id}, Name: {p.name}, "
                f"share_promotion: {share_promo}, "
                f"viral_suite: {viral_suite}"
            )

if __name__ == "__main__":
    asyncio.run(main())
