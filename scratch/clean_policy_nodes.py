import asyncio
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.alchemy_config import alchemy_config
from sqlalchemy import text

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # 1. Find invalid article nodes
        res = await db.execute(text("""
            SELECT n.id, n.node_label, a.category 
            FROM seo_nodes n
            JOIN articles a ON n.entity_id = a.id
            WHERE n.entity_type = 'ARTICLE' 
              AND a.category != 'Bài viết'
              AND n.deleted_at IS NULL
        """))
        rows = res.all()
        print(f"Found {len(rows)} invalid article nodes (not in category 'Bài viết') to clean up.")
        
        if not rows:
            print("No invalid nodes found. Database is already clean.")
            return

        now = datetime.now(timezone.utc)
        cleaned_count = 0
        
        for r in rows:
            node_id = r.id
            print(f"Cleaning: {r.node_label} (category: {r.category})")
            
            # Soft delete node
            await db.execute(text("""
                UPDATE seo_nodes 
                SET deleted_at = :now, updated_at = :now 
                WHERE id = :node_id
            """), {"now": now, "node_id": node_id})
            
            # Hard delete edges connected to this node
            edge_res = await db.execute(text("""
                DELETE FROM seo_edges 
                WHERE source_node_id = :node_id OR target_node_id = :node_id
            """), {"node_id": node_id})
            
            print(f"  - Deleted {edge_res.rowcount} edges.")
            cleaned_count += 1
            
        await db.commit()
        print(f"Successfully cleaned {cleaned_count} SEO nodes and their edges.")

if __name__ == "__main__":
    asyncio.run(run())
