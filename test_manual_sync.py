import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append("/app")

# Elite V2.2: Context
os.environ["FAST_PLATFORM_TEST"] = "true"

from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory

async def run_manual_test():
    session_id = "manual_sync_888"
    print(f"[*] Starting Manual Neural Sync Test for session: {session_id}")
    
    # 1. Start Event Bus
    await event_bus.start()
    
    # 2. Check Redis
    if not xohi_memory._use_redis:
        print("[!] Redis offline. Aborting.")
        return

    # 3. Subscribe to the channel manually to verify emission
    pubsub = xohi_memory.client.pubsub()
    await pubsub.subscribe(f"pulse:{session_id}")
    print(f"[*] Subscribed to pulse:{session_id}")

    # 4. Emit in background
    async def emit_task():
        await asyncio.sleep(1)
        print("[*] Emitting event...")
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "message_id": "test_msg_123",
            "is_revoked": True
        })
        print("[*] Event emitted.")

    task = asyncio.create_task(emit_task())

    # 5. Listen
    print("[*] Waiting for message from Redis...")
    try:
        async with asyncio.timeout(5.0):
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'message':
                    print(f"[+] RECEIVED: {message['data']}")
                    break
    except asyncio.TimeoutError:
        print("[!] TIMEOUT: No message received in 5s.")
    
    await task
    await event_bus.stop()
    print("[*] Done.")

if __name__ == "__main__":
    asyncio.run(run_manual_test())
