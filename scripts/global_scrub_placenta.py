import asyncio
import logging
from sqlalchemy import text
from backend.database.alchemy_config import alchemy_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("global-scrub-placenta")

async def run_global_scrub():
    engine = alchemy_config.get_engine()
    async with engine.begin() as conn:
        # Get list of all tables
        tables_res = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        ))
        tables = [r[0] for r in tables_res.fetchall()]

        logger.info(f"Starting global DB scrubbing for {len(tables)} tables...")

        total_updates = 0

        for table in tables:
            # Get columns and types
            cols_res = await conn.execute(text(
                f"SELECT column_name, data_type FROM information_schema.columns "
                f"WHERE table_schema='public' AND table_name='{table}'"
            ))
            cols = cols_res.fetchall()

            for col_name, data_type in cols:
                if data_type in ("text", "character varying", "character", "jsonb", "json"):
                    try:
                        if data_type in ("jsonb", "json"):
                            # For json/jsonb columns
                            query = (
                                f"UPDATE {table} "
                                f"SET {col_name} = regexp_replace({col_name}::text, 'nhau\\s+thai', 'Placenta', 'gi')::{data_type} "
                                f"WHERE {col_name}::text ~* 'nhau\\s+thai'"
                            )
                        else:
                            # For text/varchar columns
                            query = (
                                f"UPDATE {table} "
                                f"SET {col_name} = regexp_replace({col_name}, 'nhau\\s+thai', 'Placenta', 'gi') "
                                f"WHERE {col_name} ~* 'nhau\\s+thai'"
                            )

                        res = await conn.execute(text(query))
                        updated_rows = res.rowcount
                        if updated_rows > 0:
                            logger.info(f"✅ Updated Table '{table}', Column '{col_name}' ({data_type}): {updated_rows} rows.")
                            total_updates += updated_rows
                    except Exception as e:
                        logger.error(f"Error scrubbing Table '{table}', Column '{col_name}': {e}")

        logger.info(f"Global scrubbing complete. Total columns updated: {total_updates}")

if __name__ == "__main__":
    asyncio.run(run_global_scrub())
