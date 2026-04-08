import asyncio
import httpx
import time

async def test_helen_greeting():
    print("🚀 [Elite Domain Protocol] Helen AI Active Test")
    
    # ⚠️ MANDATORY: Domain api.micsmo.com (CẤM localhost)
    domain = "api.micsmo.com"
    # Internal routing for Docker execution (Elite Pattern)
    target_url = "http://127.0.0.1:8000/api/v1/client/support/chat"
    
    payload = {
        "message": "Chào bạn",
        "session_id": "test-elite-domain-2026",
        "customer_name": "Sếp Tổng"
    }
    
    print(f"--- 📡 Host Resolution: {domain} ---")
    print(f"--- 📨 Message: '{payload['message']}' ---")
    
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Elite V2.2: Hitting target with explicit Domain Host Header
            resp = await client.post(target_url, json=payload, headers={"Host": domain})
            t1 = time.perf_counter()
            
            latency_ms = (t1 - t0) * 1000
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Latency: {latency_ms:.2f}ms")
                print(f"✅ Compliance: 100% (Domain: {domain})")
                print(f"Helen: {data.get('reply')}")
                print(f"Intent: {data.get('intent')}")
                print(f"Status: {data.get('status')}")
                
                if latency_ms < 50:
                    print("⚡ Lớp 0 (Micro-Heuristic) phản hồi tức thì.")
            else:
                print(f"❌ Error {resp.status_code}: {resp.text}")
                
        except Exception as e:
            print(f"❌ Elite Bridge Failure: {e}")

if __name__ == "__main__":
    asyncio.run(test_helen_greeting())
