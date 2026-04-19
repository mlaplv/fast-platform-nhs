import asyncio
import os

# Manually load .env BEFORE importing alchemy_config
if not os.getenv("DATABASE_URL"):
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("#") or not "=" in line:
                    continue
                k, v = line.strip().split("=", 1)
                os.environ[k] = v.strip('"').strip("'")
            print("Loaded environment variables from .env")
    except Exception as e:
        print(f"Error loading .env: {e}")

# Fix host for local run
db_url = os.getenv("DATABASE_URL")
if db_url and "@db:5432" in db_url:
    os.environ["DATABASE_URL"] = db_url.replace("@db:5432", "@localhost:5432")
    print("Corrected DATABASE_URL for local execution.")

from sqlalchemy import text
from backend.database.alchemy_config import alchemy_config

async def sync_data():
    engine = alchemy_config.get_engine()
    async with engine.begin() as conn:
        print(f"Connecting to {alchemy_config._url}...")
        print("Synchronizing voucher category with types...")
        
        # 1. Update Shipping
        res1 = await conn.execute(text("UPDATE vouchers SET category = 'SHIPPING' WHERE type = 'SHIPPING'"))
        print(f"Updated {res1.rowcount} shipping vouchers.")
        
        # 2. Update Discount
        res2 = await conn.execute(text("UPDATE vouchers SET category = 'DISCOUNT' WHERE type IN ('FIXED', 'PERCENT')"))
        print(f"Updated {res2.rowcount} discount vouchers.")
        
    await engine.dispose()
    print("Data synchronization finished.")

if __name__ == "__main__":
    asyncio.run(sync_data())
