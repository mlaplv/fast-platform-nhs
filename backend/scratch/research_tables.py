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
        print("Scaning for tenant_id columns...")
        sql = text("SELECT table_name FROM information_schema.columns WHERE column_name = 'tenant_id' AND table_schema = 'public';")
        res = await conn.execute(sql)
        tables = [r[0] for r in res]
        
        metadata = []
        for table in tables:
            try:
                count_res = await conn.execute(text(f"SELECT count(*) FROM {table} WHERE tenant_id = 'smartshop'"))
                count_smartshop = count_res.scalar()
                
                count_default_res = await conn.execute(text(f"SELECT count(*) FROM {table} WHERE tenant_id = 'default' or tenant_id IS NULL"))
                count_other = count_default_res.scalar()
                
                metadata.append({
                    "table": table,
                    "smartshop": count_smartshop,
                    "other": count_other
                })
            except Exception:
                pass
        
        # Sort by impact
        metadata.sort(key=lambda x: x["smartshop"], reverse=True)
        for m in metadata:
            print(f"Table: {m['table']:<30} | smartshop: {m['smartshop']:<5} | default/null: {m['other']}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
