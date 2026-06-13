import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config
from sqlalchemy import text

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # 1. Tìm bài viết theo tiêu đề
        title_pattern = "%Cách phân biệt và chọn mua Miccosmo beppin body virgin white serum%"
        res = await db.execute(text("""
            SELECT id, title, content 
            FROM articles 
            WHERE title LIKE :pattern AND deleted_at IS NULL
        """), {"pattern": title_pattern})
        articles = res.all()
        print(f"Articles matching pattern (total {len(articles)}):")
        for a in articles:
            print(f"- ID: {a.id}")
            print(f"  Title: {a.title}")
            print(f"  Content length: {len(a.content or '')}")
            
            # 2. Check contextual links for this article
            res_links = await db.execute(text("""
                SELECT id, anchor_text, target_url, status, original_sentence, linked_sentence 
                FROM seo_contextual_links 
                WHERE source_article_id = :art_id
            """), {"art_id": a.id})
            links = res_links.all()
            print(f"  Contextual links found (total {len(links)}):")
            for l in links:
                print(f"    * ID: {l.id}")
                print(f"      Anchor: {l.anchor_text} -> {l.target_url}")
                print(f"      Status: {l.status}")
                print(f"      Original sentence: {l.original_sentence}")
                print(f"      Proposed linked sentence: {l.linked_sentence}")

if __name__ == "__main__":
    asyncio.run(run())
