import asyncio
import os
import sys
from sqlalchemy import select, and_

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def diag():
    from backend.database import async_session_maker
    from backend.database.models.system import SupportKnowledge
    from backend.database import current_tenant_id
    
    async with async_session_maker() as session:
        print(f"Current Context TenantID: {current_tenant_id.get()}")
        
        print("Querying ALL SupportKnowledge (No filters)...")
        stmt = select(SupportKnowledge)
        res = await session.execute(stmt)
        items = res.scalars().all()
        print(f"Grand Total: {len(items)}")
        for i in items:
            print(f"ID:{i.id} | Q:{i.question[:30]} | Tenant:{i.tenant_id} | Active:{i.is_active} | Deleted:{i.deleted_at}")

        print("\nQuerying with 'địa chỉ' ILIKE...")
        stmt_ilike = select(SupportKnowledge).where(
            and_(
                SupportKnowledge.deleted_at == None,
                SupportKnowledge.is_active == True,
                SupportKnowledge.question.ilike("%địa chỉ%")
            )
        )
        res_ilike = await session.execute(stmt_ilike)
        item = res_ilike.scalar_one_or_none()
        if item:
            print(f"FOUND: {item.question}")
        else:
            print("NOT FOUND via ILIKE")

if __name__ == "__main__":
    asyncio.run(diag())
