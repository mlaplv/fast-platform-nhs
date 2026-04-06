import asyncio
import os
import sys

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def reindex():
    from backend.database import async_session_maker
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    from backend.database.repositories import SupportKnowledgeRepository
    
    async with async_session_maker() as db:
        print("Starting Support Knowledge Re-indexing...")
        repo = SupportKnowledgeRepository(session=db)
        service = SupportKnowledgeService(repo=repo)
        await service.reindex_all_knowledge(db)
        await db.commit()
        print("✅ Support Knowledge Re-indexed successfully.")

if __name__ == "__main__":
    asyncio.run(reindex())
