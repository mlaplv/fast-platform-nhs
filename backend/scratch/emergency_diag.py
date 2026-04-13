import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://", 1)

async def diag():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("--- DB STATE ---")
        res = await conn.execute(text("SELECT tenant_id, count(*) FROM product_bases GROUP BY tenant_id;"))
        print(f"Product Distribution: {res.all()}")
        
        res = await conn.execute(text("SELECT tenant_id, count(*) FROM users GROUP BY tenant_id;"))
        print(f"User Distribution: {res.all()}")
    
    from backend.constants.tenants import DOMAIN_TENANT_MAP, APP_DOMAIN, DEFAULT_TENANT_ID
    print("\n--- APP CONFIG ---")
    print(f"APP_DOMAIN: {APP_DOMAIN}")
    print(f"DEFAULT_TENANT_ID: {DEFAULT_TENANT_ID}")
    print(f"DOMAIN_TENANT_MAP: {DOMAIN_TENANT_MAP}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diag())
