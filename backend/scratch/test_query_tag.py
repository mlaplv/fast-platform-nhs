import asyncio
from backend.database import async_session_maker
from backend.services.article_service import provide_article_service
from backend.services.article_vector_service import provide_article_vector_service

async def test():
    service = provide_article_service(provide_article_vector_service())
    session = async_session_maker()
    async with session() as s:
        res = await service.list_articles(s, tag='peel & build da')
        print('Result count:', len(res.data), 'Total:', res.total)
        for article in res.data:
            print(f"- Title: {article.title}")

if __name__ == '__main__':
    asyncio.run(test())
