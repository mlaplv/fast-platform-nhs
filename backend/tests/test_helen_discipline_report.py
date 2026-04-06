import asyncio
import time
from backend.schemas.support import SupportRequest
from backend.services.commerce.operatives.support_agent import support_agent
from backend.database.session import AsyncSessionLocal

async def run_discipline_report():
    print("\n--- 🛡️ BÁO CÁO CHIẾN DỊCH: HELEN DISCIPLINE (ELITE V2.2) ---")
    
    tests = [
        {"msg": "địa chỉ ở đâu?", "label": "KNOWLEDGE (Address)", "check": lambda r: "[z1]" not in r and "Hồng Sơn" in r},
        {"msg": "thành phần là gì?", "label": "KNOWLEDGE (Ingredients)", "check": lambda r: "[z1]" not in r and "thành phần" in r.lower()},
        {"msg": "chào bạn", "label": "GREETING (Heuristic)", "check": lambda r: "[z1]" in r and "Mã đơn" not in r},
        {"msg": "mua 3 lọ 0987654321 địa chỉ láng hạ", "label": "ORDER (Lead Extraction)", "check": lambda r: "thành công" in r.lower() or "đơn hàng" in r.lower()}
    ]
    
    async with AsyncSessionLocal() as db:
        for t in tests:
            print(f"\n[TESTING] {t['label']}: \"{t['msg']}\"")
            start = time.time()
            
            # Note: We bypass the background task for instant report results
            req = SupportRequest(message=t['msg'], session_id="test_discipline_session")
            res = await support_agent.process_brain_logic(req, db)
            
            lat = (time.time() - start) * 1000
            reply = res.reply
            status = "✅ PASS" if t['check'](reply) else "❌ FAIL"
            
            print(f"  > Phản hồi: {reply[:100]}...")
            print(f"  > Độ trễ: {lat:.2f}ms")
            print(f"  > Kết quả: {status}")

    print("\n--- KẾT THÚC BÁO CÁO ---")

if __name__ == "__main__":
    asyncio.run(run_discipline_report())
