import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.seo import SeoNode, SeoContextualLink
from backend.database.models.content import Article

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        stmt = select(SeoContextualLink).where(SeoContextualLink.id == '019ecda5-0e35-74a1-847b-e7ca802301a2')
        link = await db.scalar(stmt)
        if link:
            art = await db.scalar(select(Article).where(Article.id == link.source_article_id))
            target_node = await db.scalar(select(SeoNode).where(SeoNode.id == link.target_node_id))
            print(f"Link ID: {link.id}")
            print(f"Article Title: '{art.title}'")
            print(f"Target Pillar: '{target_node.node_label}'")
            print(f"Anchor Text: '{link.anchor_text}'")
            print(f"Original Sentence: '{link.original_sentence}'")
            print(f"Linked Sentence: '{link.linked_sentence}'")
            print(f"AI Reasoning: '{link.ai_reasoning}'")
            print(f"Confidence: {link.ai_confidence}")
        else:
            print("Link not found")

if __name__ == "__main__":
    asyncio.run(main())
