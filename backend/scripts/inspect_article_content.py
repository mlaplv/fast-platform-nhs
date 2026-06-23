import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.article import Article

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        slug = "miccosmo-hurry-harry-hand-balm-giai-phap-duong-tay-chuyen-sau"
        stmt = select(Article).where(Article.slug == slug)
        article = await db.scalar(stmt)
        if article:
            print(f"Article ID: {article.id}")
            print(f"Title: {article.title}")
            print("--- CONTENT ---")
            print(article.content[:2000] if article.content else "No content")
        else:
            print("Article not found!")

if __name__ == "__main__":
    asyncio.run(main())
