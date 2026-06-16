import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode, SeoEdge
from backend.database.models.content import Article
import re

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        pillar_id = '019eb987-b978-7101-82ed-bdb3966878ad'
        pillar = await db.scalar(select(SeoNode).where(SeoNode.id == pillar_id))
        
        edges = (await db.execute(
            select(SeoEdge.target_node_id).where(
                SeoEdge.source_node_id == pillar_id,
                SeoEdge.tenant_id == "osmo.vn"
            )
        )).scalars().all()

        nodes = (await db.execute(
            select(SeoNode.entity_id).where(
                SeoNode.id.in_(edges),
                SeoNode.entity_type == "ARTICLE",
                SeoNode.tenant_id == "osmo.vn",
                SeoNode.deleted_at.is_(None)
            )
        )).scalars().all()

        article_ids = list(set(nodes))
        print(f"Total cluster articles: {len(article_ids)}")

        for art_id in article_ids:
            article = await db.scalar(
                select(Article).where(Article.id == art_id, Article.deleted_at.is_(None))
            )
            if not article:
                continue

            content = article.content
            slug = pillar.node_slug
            escaped_slug = re.escape(slug)
            pattern = rf'href=["\'](?:https?://[^"\']*)?/{escaped_slug}(?:\.html)?(?:[?#][^"\']*)?["\']'
            already_linked = bool(re.search(pattern, content))
            
            print(f"- Article: '{article.title}' ({art_id})")
            print(f"  Already linked: {already_linked}")

if __name__ == "__main__":
    asyncio.run(main())
