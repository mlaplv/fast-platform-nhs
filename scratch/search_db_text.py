import asyncio
from sqlalchemy import text
from backend.database.alchemy_config import alchemy_config

async def search_db():
    terms = [
        "HN_TikTok.mp4",
        "video-hn.mp4",
        "hn_007.png",
        "logo.png",
        "vn-voucher.webp",
        "logo_transparent.webp",
        "co--che",
        "3444c7cc-0db2-4d12-a",
        "9beee9eb-9e0e-4363"
    ]
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        # Get list of all tables
        tables_result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """))
        tables = [row[0] for row in tables_result]
        
        print(f"Searching for terms in {len(tables)} tables...")
        
        for table in tables:
            # Get text/json/jsonb columns for this table
            cols_result = await session.execute(text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND table_schema = 'public'
                  AND (data_type IN ('character varying', 'text', 'json', 'jsonb')
                       OR data_type LIKE 'char%')
            """))
            cols = [row[0] for row in cols_result]
            if not cols:
                continue
                
            for col in cols:
                for term in terms:
                    query = text(f"""
                        SELECT COUNT(*) FROM "{table}" 
                        WHERE CAST("{col}" AS TEXT) ILIKE :term
                    """)
                    try:
                        count = await session.scalar(query, {"term": f"%{term}%"})
                        if count > 0:
                            print(f"🔍 Found {count} matches in Table: {table}, Column: {col} for term: '{term}'")
                    except Exception as e:
                        # Some tables/columns might have issues, ignore
                        pass

if __name__ == "__main__":
    asyncio.run(search_db())
