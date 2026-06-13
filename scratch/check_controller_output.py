import asyncio
import sys
import os
import json
import hashlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config, current_tenant_id
from sqlalchemy import select
from backend.database.models.seo import SeoContextualLink, SeoNode
from backend.database.models.content import Article

async def run():
    token = current_tenant_id.set("osmo.vn")
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db_session:
            article_id = "art_aging_strategies"
            article = await db_session.scalar(
                select(Article).where(Article.id == article_id, Article.deleted_at.is_(None))
            )
            if not article:
                print("Article not found!")
                return
            
            current_hash = hashlib.md5((article.content or "").encode()).hexdigest()
            
            query = (
                select(SeoContextualLink, SeoNode.node_label)
                .select_from(SeoContextualLink)
                .outerjoin(SeoNode, SeoContextualLink.target_node_id == SeoNode.id)
                .where(
                    SeoContextualLink.source_article_id == article_id,
                    SeoContextualLink.tenant_id == "osmo.vn",
                )
                .order_by(SeoContextualLink.sentence_index.asc())
            )
            res = await db_session.execute(query)
            rows = res.all()
            
            stats = {"pending": 0, "approved": 0, "rejected": 0, "applied": 0}
            links_data = []
            
            for l, target_label in rows:
                st = l.status if isinstance(l.status, str) else l.status.value
                print(f"DEBUG: st={st!r}, type={type(st)}, value={getattr(st, 'value', None)!r}")
                if st in stats:
                    stats[st] += 1
                else:
                    print(f"WARNING: st {st!r} NOT in stats keys {list(stats.keys())}")
                
                links_data.append({
                    "id": l.id,
                    "status": st,
                })
            
            print("Stats:", stats)
            print("Links:", links_data)
    finally:
        current_tenant_id.reset(token)

if __name__ == "__main__":
    asyncio.run(run())
