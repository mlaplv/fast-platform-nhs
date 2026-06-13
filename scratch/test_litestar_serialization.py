import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config, current_tenant_id
from litestar.serialization import encode_json

async def run():
    token = current_tenant_id.set("osmo.vn")
    session_maker = alchemy_config.create_session_maker()
    try:
        async with session_maker() as db:
            from sqlalchemy import select
            from backend.database.models.seo import SeoContextualLink, SeoNode
            
            article_id = "art_aging_strategies"
            query = (
                select(SeoContextualLink, SeoNode.node_label)
                .select_from(SeoContextualLink)
                .outerjoin(SeoNode, SeoContextualLink.target_node_id == SeoNode.id)
                .where(SeoContextualLink.source_article_id == article_id)
            )
            res = await db.execute(query)
            rows = res.all()
            
            links_data = []
            for l, target_label in rows:
                st = l.status if isinstance(l.status, str) else l.status.value
                links_data.append({
                    "id": l.id,
                    "status": st,
                })
            
            # Serialize using Litestar's standard JSON encoder
            encoded = encode_json(links_data)
            print("Serialized links:")
            print(encoded.decode())
    finally:
        current_tenant_id.reset(token)

if __name__ == "__main__":
    asyncio.run(run())
