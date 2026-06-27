import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoContextualLink, SeoNode
from backend.database.models.content import Article

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        node = await db.get(SeoNode, "019eb970-7250-8d1e-7a87a9b626c9")
        # Wait, the pillar_id in metadata was "019eb987-b970-7250-8d1e-7a87a9b626c9"
        # Let's search by label/ID
        nodes = (await db.execute(
            select(SeoNode).where(
                (SeoNode.id == "019eb987-b970-7250-8d1e-7a87a9b626c9") |
                (SeoNode.node_label.like("%Whitening Cream%"))
            )
        )).scalars().all()
        
        for n in nodes:
            print(f"Pillar: {n.node_label} | ID: {n.id}")
            links = (await db.execute(
                select(SeoContextualLink).where(SeoContextualLink.target_node_id == n.id)
            )).scalars().all()
            
            print(f"Total links in DB: {len(links)}")
            for l in links:
                article = await db.get(Article, l.source_article_id)
                a_title = article.title if article else "Unknown Article"
                print(f"  Link ID: {l.id}")
                print(f"    Source: {a_title} (ID: {l.source_article_id})")
                print(f"    Anchor: {l.anchor_text}")
                print(f"    Status: {l.status}")
                print(f"    Confidence: {l.ai_confidence}")
                print(f"    Content Hash: {l.content_hash}")
                print("-" * 45)

if __name__ == "__main__":
    asyncio.run(main())
