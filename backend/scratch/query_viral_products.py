
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

async def check_viral_products():
    print(f"Connecting to: {db_url}")
    try:
        async with async_session_maker() as session:
            stmt = select(ProductBase)
            res = await session.execute(stmt)
            products = res.scalars().all()
            
            print("\nViral Configuration in Products:")
            found = False
            for p in products:
                meta = p.product_metadata or {}
                viral = meta.get("share_promotion") or meta.get("viral_suite")
                if viral:
                    found = True
                    print(f"\n- Product: {p.name} (ID: {p.id})")
                    print(f"  Viral Config: {json.dumps(viral, indent=4, ensure_ascii=False)}")
            
            if not found:
                print("No products with viral configuration found.")
    except Exception as e:
        print(f"\n❌ DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_viral_products())
