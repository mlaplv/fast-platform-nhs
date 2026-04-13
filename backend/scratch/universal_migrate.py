import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://", 1)

async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("--- Universal Migration: smartshop -> micsmo.com ---")
        sql = text("SELECT table_name FROM information_schema.columns WHERE column_name = 'tenant_id' AND table_schema = 'public';")
        res = await conn.execute(sql)
        tables = [r[0] for r in res]
        
        for table in tables:
            try:
                update_sql = text(f"UPDATE {table} SET tenant_id = 'micsmo.com' WHERE tenant_id = 'smartshop';")
                update_res = await conn.execute(update_sql)
                if update_res.rowcount > 0:
                    print(f"Table: {table:<30} | Migrated {update_res.rowcount} records.")
            except Exception as e:
                print(f"Table: {table:<30} | Error: {e}")
                
        print("\n--- Final Verification ---")
        for table in tables:
            try:
                check_sql = text(f"SELECT count(*) FROM {table} WHERE tenant_id = 'smartshop';")
                check_res = await conn.execute(check_sql)
                count = check_res.scalar()
                if count > 0:
                    print(f"WARNING: {table} still has {count} 'smartshop' records!")
            except Exception:
                pass
                
    await engine.dispose()
    print("\nUniversal Migration Completed Successfully.")

if __name__ == "__main__":
    asyncio.run(main())
