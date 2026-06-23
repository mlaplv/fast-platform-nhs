import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models import ProductBase
import re

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
        stmt = select(ProductBase).where(ProductBase.slug == slug)
        product = await db.scalar(stmt)
        if product:
            print(f"Product ID: {product.id}")
            print(f"Name: {product.name}")
            print("--- DESCRIPTION SNIPPET ---")
            desc = product.description or ""
            print(desc[:1000])
            print("--- ALL LINKS IN DESCRIPTION ---")
            links = re.findall(r'<a\s+[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', desc, re.IGNORECASE | re.DOTALL)
            print(f"Found {len(links)} links:")
            for idx, (href, anchor) in enumerate(links):
                print(f"[{idx+1}] href: {href} | anchor: {repr(anchor)}")
        else:
            print("Product not found!")

if __name__ == "__main__":
    asyncio.run(main())
