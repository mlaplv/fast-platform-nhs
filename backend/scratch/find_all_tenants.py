import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://", 1)

async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("--- Scanning for tenant_id columns ---")
        sql = text("SELECT table_name FROM information_schema.columns WHERE column_name = 'tenant_id' AND table_schema = 'public';")
        res = await conn.execute(sql)
        tables = [r[0] for r in res]
        print(f"Total tables found: {len(tables)}")
        
        for table in tables:
            count_sql = text(f"SELECT count(*) FROM {table} WHERE tenant_id = 'smartshop';")
            try:
                count_res = await conn.execute(count_sql)
                count = count_res.scalar()
                if count > 0:
                    print(f"Table: {table:<30} | Records with 'smartshop': {count}")
            except Exception:
                pass
                
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
