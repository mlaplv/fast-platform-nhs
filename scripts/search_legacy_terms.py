import asyncio
import logging
from sqlalchemy import text
from backend.database.alchemy_config import alchemy_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("search-legacy-terms")

async def search_terms():
    engine = alchemy_config.get_engine()
    async with engine.connect() as conn:
        # Get list of all tables
        tables_res = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        ))
        tables = [r[0] for r in tables_res.fetchall()]

        logger.info(f"Discovered {len(tables)} tables: {tables}")

        for table in tables:
            # Get columns and types
            cols_res = await conn.execute(text(
                f"SELECT column_name, data_type FROM information_schema.columns "
                f"WHERE table_schema='public' AND table_name='{table}'"
            ))
            cols = cols_res.fetchall()

            for col_name, data_type in cols:
                # Check text/char columns
                if data_type in ("text", "character varying", "character", "jsonb", "json"):
                    try:
                        if data_type in ("jsonb", "json"):
                            # Cast json to text for search
                            query = f"SELECT count(*) FROM {table} WHERE {col_name}::text ILIKE :term"
                        else:
                            query = f"SELECT count(*) FROM {table} WHERE {col_name} ILIKE :term"
                        
                        count_res = await conn.execute(text(query), {"term": "%nhau thai%"})
                        count = count_res.scalar()
                        if count > 0:
                            logger.info(f"🔍 FOUND: Table '{table}', Column '{col_name}' ({data_type}) has {count} matches containing 'nhau thai'")
                    except Exception as e:
                        logger.warning(f"Error checking table '{table}' column '{col_name}': {e}")

if __name__ == "__main__":
    asyncio.run(search_terms())
