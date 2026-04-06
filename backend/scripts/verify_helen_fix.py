import asyncio
import os
import sys
import uuid

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.getcwd())

async def verify():
    from backend.database import async_session_maker
    from backend.services.commerce.operatives.support_agent import support_agent
    from backend.schemas.support import SupportRequest
    
    req = SupportRequest(
        message="Địa chỉ ở đâu vậy?",
        session_id=str(uuid.uuid4())
    )
    
    async with async_session_maker() as db:
        print("Testing Helen with query: 'Địa chỉ ở đâu vậy?'")
        # Direct call to process_brain_logic to avoid Arq queue for test
        res = await support_agent.process_brain_logic(req, db)
        print(f"Reply: {res.reply}")
        print(f"Intent: {res.intent}")
        
        if "33 Ngô Thị Nhậm" in res.reply:
            print("✅ VERIFICATION SUCCESS: Helen correctly identified the address.")
        else:
            print("❌ VERIFICATION FAILURE: Helen missing address info.")

if __name__ == "__main__":
    asyncio.run(verify())
