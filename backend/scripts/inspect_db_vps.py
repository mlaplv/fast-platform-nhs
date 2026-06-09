import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text

# Add project root to python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker

async def main():
    async with async_session_maker() as session:
        # Get all tables
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
              AND table_name != 'alembic_version'
            ORDER BY table_name;
        """)
        
        result = await session.execute(query)
        tables = [row[0] for row in result.fetchall()]
        
        print(f"=== DATABASE TABLES INSPECTION ({len(tables)} tables) ===")
        for table in tables:
            try:
                count_query = text(f'SELECT COUNT(*) FROM "{table}";')
                count_res = await session.execute(count_query)
                count = count_res.scalar()
                print(f"Table: {table:<30} | Rows: {count}")
            except Exception as e:
                print(f"Table: {table:<30} | Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
