
import asyncio
import os
import sys
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
from backend.database.models.promotion import Voucher

async def check_vouchers():
    print(f"Connecting to: {db_url}")
    try:
        async with async_session_maker() as session:
            stmt = select(Voucher).where(Voucher.id == "VIRAL99K")
            res = await session.execute(stmt)
            voucher = res.scalar_one_or_none()
            
            if voucher:
                print(f"\n✅ FOUND VOUCHER:")
                print(f"ID: {voucher.id}")
                print(f"Title: {voucher.title}")
                print(f"Subtitle: {voucher.subtitle}")
                print(f"Value: {voucher.value}")
                print(f"Is Active: {voucher.is_active}")
            else:
                print("\n❌ Voucher VIRAL99K not found in DB.")
                
                # List all vouchers to see what's there
                print("\nListing all vouchers in DB:")
                stmt_all = select(Voucher)
                res_all = await session.execute(stmt_all)
                vouchers = res_all.scalars().all()
                if not vouchers:
                    print("No vouchers found at all.")
                for v in vouchers:
                    print(f"- {v.id}: {v.title} ({v.value})")
    except Exception as e:
        print(f"\n❌ DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_vouchers())
