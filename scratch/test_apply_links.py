import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config, current_tenant_id
from backend.services.seo_contextual_linker import seo_contextual_linker
from backend.database.models.content import Article
from backend.database.models.seo import SeoContextualLink
from sqlalchemy import select

async def run():
    session_maker = alchemy_config.create_session_maker()
    current_tenant_id.set("osmo.vn")
    async with session_maker() as db:
        article_id = "art_aging_strategies"
        print(f"Applying approved links for article {article_id}...")
        
        # Call the application service
        res = await seo_contextual_linker.apply_approved_links(db, article_id)
        await db.commit()
        print(f"Result: {res}")
        
        # Verify if article content now contains the link
        db.expire_all()
        article = await db.scalar(select(Article).where(Article.id == article_id))
        link = await db.scalar(select(SeoContextualLink).where(SeoContextualLink.source_article_id == article_id))
        
        print(f"Link status in DB: {link.status}")
        contains_link = "sge-contextual-link" in (article.content or "")
        print(f"Article content contains injected link? {contains_link}")
        if contains_link:
            # print snippet
            print("Snippet of article content:")
            idx = article.content.find("sge-contextual-link")
            print(article.content[max(0, idx - 100):min(len(article.content), idx + 200)])

if __name__ == "__main__":
    asyncio.run(run())
