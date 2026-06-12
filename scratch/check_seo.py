import asyncio
import sys
import os

# Add parent directory to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.session import alchemy_config
from sqlalchemy import text

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await db.execute(text("""
            SELECT n.id, n.node_label, a.category 
            FROM seo_nodes n
            JOIN articles a ON n.entity_id = a.id
            WHERE n.entity_type = 'ARTICLE' 
              AND a.category != 'Bài viết'
              AND n.deleted_at IS NULL
        """))
        rows = res.all()
        print(f"Found {len(rows)} invalid article nodes:")
        for r in rows:
            print(f"- {r.node_label} (category: {r.category})")

if __name__ == "__main__":
    asyncio.run(run())
