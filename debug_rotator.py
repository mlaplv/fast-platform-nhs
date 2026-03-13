import asyncio
import os
import sys

# Add backend to path
sys.path.append("/app")

async def test_rotator():
    from backend.services.ai_engine.core.key_rotator import key_rotator
    await key_rotator.load_keys()
    
    print(f"--- KeyRotator Diagnostic ---")
    print(f"Keys in pool: {len(key_rotator.keys)}")
    for i, k in enumerate(key_rotator.keys):
        print(f"  [{i}] {k[:8]}...")
    
    print(f"Redis connected: {key_rotator._use_redis}")
    if key_rotator.client:
        try:
            ping = await key_rotator.client.ping()
            print(f"Redis Ping: {ping}")
        except Exception as e:
            print(f"Redis Ping Failed: {e}")

    print("\nAttempting to get keys:")
    for i in range(5):
        try:
            key = await key_rotator.get_key(session_id="test_diag")
            print(f"  Attempt {i+1}: SUCCESS -> {key[:8]}...")
        except Exception as e:
            print(f"  Attempt {i+1}: FAILED -> {e}")

if __name__ == "__main__":
    asyncio.run(test_rotator())
