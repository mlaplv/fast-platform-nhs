
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

async def check_viral_99k():
    slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
    async with async_session_maker() as session:
        stmt = select(ProductBase).where(ProductBase.slug == slug)
        res = await session.execute(stmt)
        p = res.scalar_one_or_none()
        
        if p:
            print(f"Product: {p.name}")
            promo = p.product_metadata.get("viral_suite", {}).get("share_promotion", {})
            print(f"Voucher ID: {promo.get('voucher_id')}")
            print(f"Voucher Label: {promo.get('voucher_label')}")
            print(f"Voucher Subtitle: {promo.get('voucher_subtitle')}")
        else:
            print(f"Product with slug '{slug}' not found.")

if __name__ == "__main__":
    asyncio.run(check_viral_99k())
