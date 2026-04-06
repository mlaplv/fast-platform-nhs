import asyncio
import os
import sys
from sqlalchemy import select, func, and_, or_

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def run_test():
    from backend.database import async_session_maker
    from backend.database.models.system import SupportKnowledge
    from backend.database import current_tenant_id
    from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
    from backend.services.commerce.operatives.handlers.base import SupportContext
    from backend.schemas.support import SupportRequest
    
    query = "địa chỉ ở đâu"
    print(f"Hỏi: {query}")
    
    async with async_session_maker() as db:
        for tid in ["default", "smartshop"]:
            print(f"\n[Tenant: {tid}]")
            current_tenant_id.set(tid)
            
            # Heuristic Check Logic
            msg_norm = query.lower().strip()
            if any(kw in msg_norm for kw in ["địa chỉ", "ở đâu"]):
                stmt = select(SupportKnowledge).where(
                    and_(
                        SupportKnowledge.deleted_at == None,
                        SupportKnowledge.is_active == True,
                        or_(SupportKnowledge.tenant_id == tid, SupportKnowledge.tenant_id == "default"),
                        func.lower(SupportKnowledge.question).ilike("%địa chỉ%")
                    )
                ).limit(1)
                res = await db.execute(stmt)
                item = res.scalar_one_or_none()
                if item:
                    print(f"  Heuristic Query: SUCCESS (Found ID: {item.id})")
                    print(f"  Answer: {item.answer[:50]}...")
                else:
                    print("  Heuristic Query: FAILED (Scalar return None)")

            # Full Handler Check
            ctx = SupportContext(
                db=db,
                request=SupportRequest(message=query, session_id="test-repro"),
                session_id="test-repro"
            )
            handler = ConsultantHandler()
            success = await handler.handle(ctx)
            reply = "".join(ctx.replies)
            print(f"Kết quả cuối cùng: \"{reply}\"")

if __name__ == "__main__":
    asyncio.run(run_test())
