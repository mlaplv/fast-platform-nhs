import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config
from sqlalchemy import text

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # 1. Count links by status
        res = await db.execute(text("SELECT status, COUNT(*) FROM seo_contextual_links GROUP BY status"))
        print("Link status distribution:")
        for status, count in res.all():
            print(f"- {status}: {count}")
        
        # 2. Check applied links
        res = await db.execute(text("""
            SELECT id, anchor_text, target_url, source_article_id, original_sentence 
            FROM seo_contextual_links 
            WHERE status = 'APPLIED' 
            LIMIT 5
        """))
        rows = res.all()
        print(f"\nApplied links sample (total {len(rows)}):")
        for r in rows:
            print(f"- {r.anchor_text} -> {r.target_url} (Article ID: {r.source_article_id})")
            print(f"  Sentence: {r.original_sentence}")

        # 3. Check if any article content actually contains '<a href='
        res = await db.execute(text("""
            SELECT id, title, content 
            FROM articles 
            WHERE content LIKE '%<a href=%' 
            LIMIT 5
        """))
        articles = res.all()
        print(f"\nArticles containing '<a href=' in content (total {len(articles)}):")
        for a in articles:
            print(f"- {a.title} (ID: {a.id})")
            # show a snippet of content where link is located
            idx = a.content.find("<a href=")
            print(f"  Snippet: ... {a.content[max(0, idx-50):idx+150]} ...")

if __name__ == "__main__":
    asyncio.run(run())
