import asyncio
from sqlalchemy import text
from backend.database import async_session_maker

async def main():
    async with async_session_maker() as session:
        stmt = text("SELECT id, name, product_metadata, tenant_id FROM product_bases")
        res = await session.execute(stmt)
        products = res.all()
        print(f"Total Raw Products: {len(products)}")
        for p in products:
            meta = p.product_metadata or {}
            share_promo = meta.get("share_promotion") or {}
            viral_suite = meta.get("viral_suite") or {}
            print(
                f"ID: {p.id}, Name: {p.name}, tenant_id: {p.tenant_id}, "
                f"share_promotion: {share_promo}, "
                f"viral_suite: {viral_suite}"
            )

if __name__ == "__main__":
    asyncio.run(main())
