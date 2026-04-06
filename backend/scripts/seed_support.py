import asyncio
import os
import sys
import uuid
from sqlalchemy import select, delete

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def seed():
    from backend.database import async_session_maker
    from backend.database.models.system import SupportKnowledge, SupportKnowledgeCategory
    from backend.scripts.seed_data import SUPPORT_KNOWLEDGE_DEFS
    
    TENANT_ID = "smartshop"
    
    async with async_session_maker() as session:
        try:
            print("Cleaning SupportKnowledge...")
            await session.execute(delete(SupportKnowledge).where(SupportKnowledge.tenant_id == TENANT_ID))
            
            print(f"Seeding {len(SUPPORT_KNOWLEDGE_DEFS)} items...")
            for d in SUPPORT_KNOWLEDGE_DEFS:
                session.add(SupportKnowledge(
                    id=str(uuid.uuid4()),
                    category=SupportKnowledgeCategory[d["category"]],
                    question=d["question"],
                    answer=d["answer"],
                    priority=d.get("priority", 0),
                    is_active=True,
                    tenant_id=TENANT_ID
                ))
            await session.commit()
            print("Seed complete!")
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(seed())
