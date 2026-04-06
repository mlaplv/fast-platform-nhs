import asyncio
import os
import sys
from sqlalchemy import select, func, and_, or_

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def run_e2e_test():
    from backend.database import async_session_maker
    from backend.database.models.system import SupportKnowledge
    from backend.database import current_tenant_id
    from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
    from backend.services.commerce.operatives.handlers.base import SupportContext
    from backend.schemas.support import SupportRequest
    
    queries = [
        "địa chỉ ở đâu vậy?",
        "Thành phần thuốc là gì?",
        "Số điện thoại hotline để liên hệ",
        "Website nhà thuốc là gì?"
    ]
    
    async with async_session_maker() as db:
        # Check both potential tenants
        for tid in ["default", "smartshop"]:
            print(f"\n[Tenant: {tid}]")
            for query in queries:
                print(f"Hỏi: {query}")
                current_tenant_id.set(tid)
                
                # Diagnostic Context with Product Slug (The 'Hong Son' Case)
                ctx = SupportContext(
                    db=db,
                    request=SupportRequest(
                        message=query, 
                        session_id="cto-soi-ky-p5",
                        product_slug="thuoc-dac-tri-hoi-nach-hong-son"
                    ),
                    session_id="cto-soi-ky-p5"
                )
                handler = ConsultantHandler()
                
                # Verify DB item exists for this keyword category
                pattern = None
                if "địa chỉ" in query or "ở đâu" in query: pattern = "%địa chỉ%"
                elif "thành phần" in query: pattern = "%thành phần%"
                elif "hotline" in query or "điện thoại" in query or "website" in query: pattern = "%điện thoại%"
                
                if pattern:
                    stmt = select(SupportKnowledge).where(
                        and_(
                            SupportKnowledge.deleted_at == None,
                            SupportKnowledge.is_active == True,
                            or_(SupportKnowledge.tenant_id == tid, SupportKnowledge.tenant_id == "default", SupportKnowledge.tenant_id == "smartshop"),
                            func.lower(SupportKnowledge.question).ilike(pattern)
                        )
                    ).order_by(SupportKnowledge.priority.desc()).limit(1)
                    
                    row = (await db.execute(stmt)).scalar_one_or_none()
                    if row:
                        print(f"  DB CHECK: Found matching row. (Match: {row.question[:30]}...)")
                    else:
                        print(f"  DB CHECK: ❌ FAILED (No row found for pattern: {pattern})")

                # Step 2: Check Handler logic
                success = await handler.handle(ctx)
                reply = "".join(ctx.replies)
                
                if success and reply:
                    print(f"  HANDLER CHECK: SUCCESS | Kết quả cho ra: \"{reply[:50]}...\"")
                else:
                    print(f"  HANDLER CHECK: FAILED | Kết quả cho ra: \"{reply}\"")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
