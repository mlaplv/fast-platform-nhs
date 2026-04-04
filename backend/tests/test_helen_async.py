import asyncio
import httpx
import sys

# CTO V2.2: Async Verification Script
# This mocks a client calling the Support API to verify Triage logic.

API_URL = "http://localhost:8000/api/v1/client/support/chat"

async def test_helen_async_flow():
    async with httpx.AsyncClient(timeout=20.0) as client:
        # TEST 1: Sync Triage (The Butler)
        # Expected: 200 OK, Status: DONE
        print("--- TEST 1: SYNC TRIAGE (GREETING) ---")
        try:
            r1 = await client.post(API_URL, json={
                "message": "Chào bạn",
                "session_id": "test_sync_123",
                "product_slug": "chamsoc-da"
            })
            print(f"Status: {r1.status_code}")
            data1 = r1.json()
            print(f"Response: {data1.get('reply')}")
            print(f"Task Status: {data1.get('status')}")
            assert r1.status_code == 200
            assert data1.get("status") == "DONE"
        except Exception as e:
            print(f"Test 1 Failed: {e}")

        print("\n" + "="*40 + "\n")

        # TEST 2: Async Brain (LLM/RAG)
        # Expected: 202 Accepted, Status: PROCESSING, Task ID present
        print("--- TEST 2: ASYNC BRAIN (DEEP QUERY) ---")
        try:
            r2 = await client.post(API_URL, json={
                "message": "Thành phần của thuốc hôi nách này là gì vậy em?",
                "session_id": "test_async_456",
                "product_slug": "hoi-nach-helen" # Ensure this slug exists or is handled
            })
            print(f"Status: {r2.status_code}")
            data2 = r2.json()
            print(f"Response: {data2.get('reply')}")
            print(f"Task Status: {data2.get('status')}")
            print(f"Task ID: {data2.get('task_id')}")
            
            assert r2.status_code == 202
            assert data2.get("status") == "PROCESSING"
            assert data2.get("task_id") is not None
        except Exception as e:
            print(f"Test 2 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_helen_async_flow())
