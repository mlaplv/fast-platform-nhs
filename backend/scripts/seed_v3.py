import asyncio
import os
import sys
import uuid
from sqlalchemy import select, delete

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def seed():
    from backend.database import async_session_maker
    from backend.database.models.system import SupportKnowledge, SupportKnowledgeCategory, SupportKnowledgeEmbedding
    from backend.scripts.seed_data import SUPPORT_KNOWLEDGE_DEFS
    
    tenants = ["smartshop", "default"]
    
    async with async_session_maker() as session:
        try:
            print(f"Cleaning SupportKnowledge & Embeddings for {tenants}...")
            # 1. Delete Embeddings first (FK constraint)
            await session.execute(delete(SupportKnowledgeEmbedding).where(SupportKnowledgeEmbedding.tenant_id.in_(tenants)))
            # 2. Delete Knowledge
            await session.execute(delete(SupportKnowledge).where(SupportKnowledge.tenant_id.in_(tenants)))
            
            for tenant in tenants:
                print(f"Seeding {len(SUPPORT_KNOWLEDGE_DEFS)} items for tenant: {tenant}...")
                for d in SUPPORT_KNOWLEDGE_DEFS:
                    session.add(SupportKnowledge(
                        id=str(uuid.uuid4()),
                        category=SupportKnowledgeCategory[d["category"]],
                        question=d["question"],
                        answer=d["answer"],
                        priority=d.get("priority", 0),
                        is_active=True,
                        tenant_id=tenant
                    ))
            await session.commit()
            print("Seed V3 complete!")
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(seed())
