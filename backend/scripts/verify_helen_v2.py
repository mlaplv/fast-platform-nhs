import asyncio
import os
import sys
from sqlalchemy import select

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def verify():
    from backend.database import async_session_maker
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    from backend.database.repositories import SupportKnowledgeRepository
    from backend.database import current_tenant_id
    from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
    from backend.services.commerce.operatives.handlers.base import SupportContext
    from backend.schemas.support import SupportRequest
    
    tenants = ["default", "smartshop"]
    queries = ["Địa chỉ ở đâu vậy?", "địa chỉ ở đâu", "dia chi o dau", "phòng khám ở đâu"]
    
    async with async_session_maker() as db:
        repo = SupportKnowledgeRepository(session=db)
        service = SupportKnowledgeService(repo=repo)
        handler = ConsultantHandler()
        
        for tenant in tenants:
            print(f"\n--- Testing Tenant: {tenant} ---")
            token = current_tenant_id.set(tenant)
            try:
                for q in queries:
                    print(f"Query: '{q}'")
                    # Test 1: Direct Heuristic
                    ctx = SupportContext(
                        db=db,
                        request=SupportRequest(message=q, session_id="test"),
                        session_id="test"
                    )
                    success = await handler._handle_internal(ctx)
                    if success and ctx.replies:
                        print(f"  [HEURISTIC] FOUND: {ctx.replies[0][:50]}...")
                    else:
                        # Test 2: Service Keyword Search
                        res = await service.search_relevant_knowledge_keyword(db, q)
                        if res:
                            print(f"  [KEYWORD] FOUND: {res[0]['question']}")
                        else:
                            print("  [FAIL] No knowledge found.")
            finally:
                current_tenant_id.reset(token)

if __name__ == "__main__":
    asyncio.run(verify())
