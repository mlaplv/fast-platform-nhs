
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
    async with async_session_maker() as session:
        stmt = select(ProductBase)
        res = await session.execute(stmt)
        products = res.scalars().all()
        
        print("Searching for VIRAL99K in Product Metadata:")
        for p in products:
            meta_str = json.dumps(p.product_metadata or {}, ensure_ascii=False)
            if "VIRAL99K" in meta_str:
                print(f"\n✅ MATCH FOUND: {p.name} (ID: {p.id})")
                print(f"Metadata: {json.dumps(p.product_metadata, indent=4, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(check_viral_99k())
