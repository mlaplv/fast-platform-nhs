import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.content import Article
from backend.services.seo_contextual_linker import seo_contextual_linker

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        art_id = "019eaf37-5078-76db-9111-9a40388527ba"
        article = await db.scalar(select(Article).where(Article.id == art_id))
        if not article:
            print("Article not found")
            return
            
        print(f"TITLE: {article.title}")
        sentences = seo_contextual_linker._split_sentences(article.content)
        for i, s in enumerate(sentences):
            print(f"[{i}] {s['text']}")

if __name__ == "__main__":
    asyncio.run(main())
