import asyncio
import json
import os
import sys

# Elite V2.2: Standalone Neural Sync Test (Bypassing pytest)
os.environ["FAST_PLATFORM_TEST"] = "true"

from litestar.testing import AsyncTestClient
from backend.main import app
from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory

# Enable real Redis for debugging
# xohi_memory._use_redis = False
# xohi_memory.client = None

async def run_test():
    print("--- STARTING NEURAL SYNC TEST (STANDALONE) ---")
    session_id = "standalone_sid_999"
    message_id = "msg_revoke_standalone"
    
    async with AsyncTestClient(app=app) as client:
        print(f"1. Establishing stream for {session_id}")
        async with client.stream("GET", f"/api/v1/client/support/pulse/{session_id}") as response:
            print(f"2. Response received: {response.status_code}")
            
            async def trigger_revoke():
                await asyncio.sleep(0.5)
                print("3. Emitting event...")
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {
                    "session_id": session_id,
                    "message_id": message_id,
                    "is_revoked": True
                })
            
            task = asyncio.create_task(trigger_revoke())
            
            print("4. Reading stream...")
            async for line in response.aiter_lines():
                print(f"Line: {line}")
                if line.startswith("data:"):
                    print("5. Success! Received data line.")
                    break
            
            await task
    print("--- TEST COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(run_test())
