import asyncio
import os
from sqlalchemy import text

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

# IMPORTANT: Override DATABASE_URL for local migration if it points to 'db'
db_url = os.getenv("DATABASE_URL")
if db_url and "@db:5432" in db_url:
    os.environ["DATABASE_URL"] = db_url.replace("@db:5432", "@localhost:5432")
    print("Corrected DATABASE_URL to use 'localhost' instead of 'db' for local execution.")

from backend.database.alchemy_config import alchemy_config

async def migrate():
    engine = alchemy_config.get_engine()
    async with engine.begin() as conn:
        print(f"Connecting to {alchemy_config._url}...")
        
        # Add category
        try:
            await conn.execute(text("ALTER TABLE vouchers ADD COLUMN category VARCHAR DEFAULT 'DISCOUNT'"))
            print("Added column 'category'")
        except Exception as e:
            print(f"Column 'category' error: {e}")

        # Add is_default
        try:
            await conn.execute(text("ALTER TABLE vouchers ADD COLUMN is_default BOOLEAN DEFAULT FALSE"))
            print("Added column 'is_default'")
        except Exception as e:
            print(f"Column 'is_default' error: {e}")

        # Add priority
        try:
            await conn.execute(text("ALTER TABLE vouchers ADD COLUMN priority INTEGER DEFAULT 0"))
            print("Added column 'priority'")
        except Exception as e:
            print(f"Column 'priority' error: {e}")

    await engine.dispose()
    print("Migration finished.")

if __name__ == "__main__":
    asyncio.run(migrate())
