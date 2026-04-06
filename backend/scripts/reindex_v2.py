import asyncio
import os
import sys
from sqlalchemy import select

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def reindex():
    from backend.database import async_session_maker
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    from backend.database.repositories import SupportKnowledgeRepository
    from backend.database import current_tenant_id
    
    tenants = ["smartshop", "default"]
    
    async with async_session_maker() as db:
        print("Starting Support Knowledge Re-indexing for all tenants...")
        for tenant in tenants:
            print(f"Indexing tenant: {tenant}...")
            # Set context for the service if it uses it
            token = current_tenant_id.set(tenant)
            try:
                repo = SupportKnowledgeRepository(session=db)
                service = SupportKnowledgeService(repo=repo)
                await service.reindex_all_knowledge(db)
                await db.commit()
            finally:
                current_tenant_id.reset(token)
        print("✅ All tenants re-indexed successfully.")

if __name__ == "__main__":
    asyncio.run(reindex())
