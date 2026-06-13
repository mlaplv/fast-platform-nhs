import asyncio
import sys
import os
import hashlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config, current_tenant_id
from backend.services.seo_contextual_linker import seo_contextual_linker
from backend.database.models.content import Article
from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus
from sqlalchemy import select

async def run():
    session_maker = alchemy_config.create_session_maker()
    current_tenant_id.set("osmo.vn")
    async with session_maker() as db:
        article_id = "art_aging_strategies"
        
        # Load the article and link
        article = await db.scalar(select(Article).where(Article.id == article_id))
        link = await db.scalar(select(SeoContextualLink).where(SeoContextualLink.source_article_id == article_id))
        
        print("Initial state:")
        print(f"- Article content length: {len(article.content)}")
        print(f"- Link status: {link.status}")
        
        # Clean the article content first (remove any previously injected link to start fresh)
        # We will replace the injected <a> tag back to the original sentence
        if "sge-contextual-link" in article.content:
            print("Removing existing injected link to reset test state...")
            clean_content = article.content.replace(
                '<a href="/miccosmo-beppin-body-virgin-white-serum-30g" class="sge-contextual-link" data-sge-source="ai">Miccosmo Beppin Body Virgin White Serum</a>',
                'Miccosmo Beppin Body Virgin White Serum'
            )
            article.content = clean_content
            await db.commit()
            print("Reset complete.")
        
        # Let's artificially modify the article content so the hash is mismatching
        # We append a small comment at the end
        modified_content = article.content + "\n<!-- test_stale_modification -->"
        article.content = modified_content
        await db.commit()
        
        # Set link status to APPROVED and content_hash to something else (e.g. "invalid_hash")
        link.status = SeoContextualLinkStatus.APPROVED
        link.content_hash = "stale_hash_placeholder"
        await db.commit()
        
        print("\nSetup complete for stale hash test:")
        print(f"- Current Article MD5 hash: {hashlib.md5(article.content.encode()).hexdigest()}")
        print(f"- Contextual Link content_hash in DB: {link.content_hash} (should mismatch)")
        print(f"- Contextual Link status: {link.status}")
        
        # Now run apply_approved_links
        print("\nRunning apply_approved_links...")
        res = await seo_contextual_linker.apply_approved_links(db, article_id)
        await db.commit()
        print(f"Result: {res}")
        
        # Verify the outcome
        db.expire_all()
        article_after = await db.scalar(select(Article).where(Article.id == article_id))
        link_after = await db.scalar(select(SeoContextualLink).where(SeoContextualLink.source_article_id == article_id))
        
        print(f"\nFinal State:")
        print(f"- Link status: {link_after.status}")
        contains_link = "sge-contextual-link" in (article_after.content or "")
        print(f"- Article contains injected link? {contains_link}")
        
        if link_after.status == SeoContextualLinkStatus.APPLIED and contains_link:
            print("\nSUCCESS: Link successfully applied despite stale content hash!")
        else:
            print("\nFAILED: Link was not applied.")

if __name__ == "__main__":
    asyncio.run(run())
