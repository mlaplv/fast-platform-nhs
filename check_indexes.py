
import asyncio
from sqlalchemy import text
from backend.database import async_session_maker

async def check_orders_indexes():
    async with async_session_maker() as session:
        # Lấy thông tin index của bảng orders
        query = text("""
            SELECT
                i.relname AS index_name,
                a.attname AS column_name
            FROM
                pg_class t,
                pg_class i,
                pg_index ix,
                pg_attribute a
            WHERE
                t.oid = ix.indrelid
                AND i.oid = ix.indexrelid
                AND a.attrelid = t.oid
                AND a.attnum = ANY(ix.indkey)
                AND t.relkind = 'r'
                AND t.relname = 'orders'
            ORDER BY
                t.relname,
                i.relname;
        """)
        result = await session.execute(query)
        rows = result.fetchall()

        print("Indexes on 'orders' table:")
        for row in rows:
            print(f"- Index: {row.index_name}, Column: {row.column_name}")

if __name__ == "__main__":
    asyncio.run(check_orders_indexes())
