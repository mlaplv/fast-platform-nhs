import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoContextualLink, SeoNode
from backend.database.models.content import Article
from backend.database import current_tenant_id

async def main():
    current_tenant_id.set("osmo.vn")
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db_session:
        pillar_node_id = "019eb987-b970-7250-8d1e-7a87a9b626c9"
        tenant = "osmo.vn"
        
        pillar = await db_session.scalar(
            select(SeoNode).where(
                SeoNode.id == pillar_node_id,
                SeoNode.is_pillar == True,
                SeoNode.tenant_id == tenant,
                SeoNode.deleted_at.is_(None)
            )
        )
        if not pillar:
            print("Pillar not found!")
            return
            
        print(f"Pillar Label: {pillar.node_label}")
        
        query = (
            select(SeoContextualLink, Article.title)
            .select_from(SeoContextualLink)
            .outerjoin(Article, SeoContextualLink.source_article_id == Article.id)
            .where(
                SeoContextualLink.target_node_id == pillar_node_id,
                SeoContextualLink.tenant_id == tenant,
            )
            .order_by(SeoContextualLink.created_at.desc())
        )
        res = await db_session.execute(query)
        rows = res.all()
        
        print(f"API rows returned: {len(rows)}")
        for l, article_title in rows:
            print(f"  Link ID: {l.id} | Article: {article_title} | Status: {l.status}")

if __name__ == "__main__":
    asyncio.run(main())
