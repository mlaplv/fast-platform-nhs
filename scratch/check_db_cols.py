import asyncio
import os
import sys
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

async def check():
    from backend.database.alchemy_config import alchemy_config
    try:
        async with alchemy_config.create_session_maker()() as s:
            res = await s.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'product_bases'"))
            cols = [r[0] for r in res.fetchall()]
            print(f"Columns: {cols}")
            
            if 'market_data' in cols:
                print("✅ market_data column exists")
            else:
                print("❌ market_data column MISSING")
                
            if 'last_market_sync' in cols:
                print("✅ last_market_sync column exists")
            else:
                print("❌ last_market_sync column MISSING")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
