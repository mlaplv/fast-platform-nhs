
import asyncio
import os
import sys
import json
from pathlib import Path
from sqlalchemy import select
from dotenv import load_dotenv

# Fix python path
project_root = "/home/lv/Desktop/fast-platform-core"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load .env
load_dotenv(os.path.join(project_root, ".env"))

# Override DB URL for local execution if needed
db_url = os.getenv("DATABASE_URL")
if db_url and "@db:" in db_url:
    db_url = db_url.replace("@db:", "@localhost:")
os.environ["DATABASE_URL"] = db_url

from backend.database import async_session_maker
from backend.database.models import ProductBase

async def check_target_product():
    slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
    async with async_session_maker() as session:
        stmt = select(ProductBase).where(ProductBase.slug == slug)
        res = await session.execute(stmt)
        p = res.scalar_one_or_none()
        
        if p:
            print(f"Product: {p.name}")
            print(f"Metadata: {json.dumps(p.product_metadata, indent=4, ensure_ascii=False)}")
        else:
            print(f"Product with slug '{slug}' not found.")
            # Search by partial slug
            stmt2 = select(ProductBase).where(ProductBase.slug.like("%hurry-harry-premium-neck-cream-rich-40gr%"))
            res2 = await session.execute(stmt2)
            p2 = res2.scalar_one_or_none()
            if p2:
                print(f"Found partial match: {p2.name}")
                print(f"Slug: {p2.slug}")
                print(f"Metadata: {json.dumps(p2.product_metadata, indent=4, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(check_target_product())
