import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://", 1)

async def fix():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("FORCE Sync: Moving all Users and Roles to 'micsmo.com'")
        # 1. Update Users
        res1 = await conn.execute(text("UPDATE users SET tenant_id = 'micsmo.com';"))
        print(f"Updated {res1.rowcount} users.")
        
        # 2. Update Roles
        res2 = await conn.execute(text("UPDATE roles SET tenant_id = 'micsmo.com';"))
        print(f"Updated {res2.rowcount} roles.")
        
        # 3. Update any other missed tables from previous research
        tables = ["system_reviews", "appointments", "orders", "categories", "product_bases"]
        for t in tables:
            try:
                r = await conn.execute(text(f"UPDATE {t} SET tenant_id = 'micsmo.com';"))
                print(f"Force-sync table {t}: {r.rowcount} records.")
            except:
                pass
                
    await engine.dispose()
    print("Repair Completed.")

if __name__ == "__main__":
    asyncio.run(fix())
