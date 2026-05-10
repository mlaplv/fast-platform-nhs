
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

async def update_to_99k():
    slug = "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co"
    async with async_session_maker() as session:
        stmt = select(ProductBase).where(ProductBase.slug == slug)
        res = await session.execute(stmt)
        p = res.scalar_one_or_none()
        
        if p:
            print(f"Updating Product: {p.name}")
            meta = p.product_metadata or {}
            
            # Update share_promotion
            if "viral_suite" in meta:
                meta["viral_suite"]["share_promotion"]["voucher_id"] = "VIRAL99K"
                meta["viral_suite"]["share_promotion"]["voucher_label"] = "Giảm 99.000₫"
                meta["viral_suite"]["share_promotion"]["share_text"] = "Bí quyết tỏa sáng cùng Miccosmo Hurry Harry Premium Neck Cream Rich 40gr - Kem dưỡng sáng cổ! Cùng chia sẻ để nhận ưu đãi 99K nhé! 🌸"
            
            p.product_metadata = meta
            session.add(p)
            await session.commit()
            print("✅ Successfully updated to VIRAL99K and synced labels.")
        else:
            print(f"Product with slug '{slug}' not found.")

if __name__ == "__main__":
    asyncio.run(update_to_99k())
