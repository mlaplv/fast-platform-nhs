import asyncio
import os
import sys
from sqlalchemy import select

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def check():
    from backend.database import async_session_maker
    from backend.database.models.system import SupportKnowledge, SupportKnowledgeCategory
    
    async with async_session_maker() as session:
        try:
            print("Querying SupportKnowledge for 'địa chỉ'...")
            stmt = select(SupportKnowledge).where(
                SupportKnowledge.question.ilike('%địa chỉ%')
            )
            res = await session.execute(stmt)
            items = res.scalars().all()
            print(f"MATCH_COUNT:{len(items)}")
            for item in items:
                print(f"ID: {item.id} | Q: {item.question} | A: {item.answer[:50]}...")
                
            print("Querying ALL SupportKnowledge...")
            stmt_all = select(SupportKnowledge)
            res_all = await session.execute(stmt_all)
            all_items = res_all.scalars().all()
            print(f"TOTAL_COUNT:{len(all_items)}")
            for item in all_items[:10]:
                print(f"ID: {item.id} | Q: {item.question}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
