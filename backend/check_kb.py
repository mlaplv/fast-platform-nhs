import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import SupportKnowledgeRepository
from backend.services.commerce.support_knowledge import SupportKnowledgeService

async def main():
    async_session = alchemy_config.create_session_maker()
    async with async_session() as db:
        repo = SupportKnowledgeRepository(session=db)
        svc = SupportKnowledgeService(repo=repo)
        
        msg = "Sản phẩm này có chính hãng không? Nguồn gốc ở đâu?"
        matches = await svc.search_relevant_knowledge_raw(db, msg, limit=3)
        for i, m in enumerate(matches):
            print(f"Match {i+1}: Score: {m.get('match_score')}")
            print(f"Q: {m.get('question')}")
            print(f"A: {m.get('answer')}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
