import asyncio
import os
import sys
from sqlalchemy import select, func, and_, or_

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def diag():
    from backend.database import async_session_maker
    from backend.database.models.system import SupportKnowledge
    from backend.database import current_tenant_id
    from backend.schemas.support import SupportRequest
    from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
    from backend.services.commerce.operatives.handlers.base import SupportContext
    
    query = "địa chỉ ở đâu"
    print(f"Hỏi: {query}")
    
    async with async_session_maker() as db:
        # Check tenant smartshop
        print("\n--- Context: smartshop ---")
        current_tenant_id.set("smartshop")
        ctx = SupportContext(
            db=db,
            request=SupportRequest(message=query, session_id="test-p3"),
            session_id="test-p3"
        )
        handler = ConsultantHandler()
        success = await handler._handle_internal(ctx)
        
        reply = "".join(ctx.replies)
        print(f"Kết quả cho ra: \"{reply}\"")
        if success:
            print("Status: SUCCESS (Consumed)")
        else:
            print("Status: FAILED (Fall-through)")

if __name__ == "__main__":
    asyncio.run(diag())
