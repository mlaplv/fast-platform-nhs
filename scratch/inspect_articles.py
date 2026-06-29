import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import async_session_maker
from backend.database.models import Article, User

async def main():
    async with async_session_maker() as session:
        # Check users
        user_res = await session.execute(select(User.id, User.name, User.email))
        users = user_res.all()
        print("--- USERS ---")
        for u in users:
            print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}")
            
        # Check articles
        art_res = await session.execute(
            select(
                Article.id, Article.title, Article.author_id, Article.views, Article.created_at
            ).limit(5)
        )
        articles = art_res.all()
        print("\n--- ARTICLES ---")
        for a in articles:
            print(f"ID: {a.id}, Title: {a.title[:30]}, AuthorID: {a.author_id}, Views: {a.views}, CreatedAt: {a.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
