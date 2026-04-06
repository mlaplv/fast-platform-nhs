import asyncio
import sys
import os

# TRỰC TIẾP: Cài đặt path để Python thấy 'backend'
sys.path.append('/app')

async def standalone_test():
    print("\n--- 🛡️ BÁO CÁO CHIẾN DỊCH: HELEN DISCIPLINE (STANDALONE REPORT) ---")
    
    # Lazy Import bên trong hàm để đảm bảo path đã được nhận diện
    try:
        from backend.database.session import AsyncSessionLocal
        from backend.schemas.support import SupportRequest
        from backend.services.commerce.operatives.support_agent import support_agent
        from sqlalchemy import text
    except ImportError as e:
        print(f"❌ LỖI IMPORT: {e}")
        print("Đang thử đường dẫn thay thế...")
        sys.path.append(os.path.join('/app', 'backend'))
        # Thử lại lần nữa với path sâu hơn
        from backend.database.session import AsyncSessionLocal
        from backend.schemas.support import SupportRequest
        from backend.services.commerce.operatives.support_agent import support_agent

    tests = [
        {"msg": "địa chỉ ở đâu?", "label": "KNOWLEDGE (Address)"},
        {"msg": "thành phần là gì?", "label": "KNOWLEDGE (Ingredients)"},
        {"msg": "chào bạn", "label": "GREETING (Heuristic)"}
    ]
    
    async with AsyncSessionLocal() as db:
        # Check DB connection
        await db.execute(text("SELECT 1"))
        
        for t in tests:
            print(f"\n[HỎI]: \"{t['msg']}\"")
            req = SupportRequest(message=t['msg'], session_id="boss_test_standalone")
            res = await support_agent.process_brain_logic(req, db)
            print(f"[HELEN ĐÁP]:\n{res.reply}\n" + "-"*30)

if __name__ == "__main__":
    asyncio.run(standalone_test())
