import asyncio
import os
import sys
import time

# Add root directory to python path
sys.path.append(os.getcwd())

from backend.services.ai_engine.core.encoder_singleton import (
    warmup_encoder,
    get_shared_encoder,
    release_shared_encoder,
)
import backend.services.ai_engine.core.encoder_singleton as es

async def test_fastembed_unload():
    print("=" * 60)
    print("🧪 FASTEMBED UNLOAD AND WATCHDOG TEST")
    print("=" * 60)

    # 1. Initially, model should be None
    print(f"1. Initial status: {es._shared_encoder}")
    assert es._shared_encoder is None, "Model should be None initially"

    # 2. Warm up model
    print("2. Warming up model...")
    await warmup_encoder()
    model = es._shared_encoder
    print(f"   Model loaded: {model}")
    assert model is not None, "Model should not be None after warmup"
    
    # Verify last used time is updated
    print(f"   Last used time: {es._last_used_time}")
    assert es._last_used_time > 0, "Last used time should be set"
    assert es._unload_task is not None, "Watchdog task should be running"

    # 3. Perform semantic search test to verify watchdog resets time
    old_time = es._last_used_time
    await asyncio.sleep(0.5)
    model2 = get_shared_encoder()
    print(f"3. Accessed model again, new last used time: {es._last_used_time}")
    assert es._last_used_time > old_time, "Last used time should update on access"

    # 4. Mock idle time by setting last_used_time to 150 seconds ago
    print("4. Mocking idle time to 150 seconds ago (limit is 120s)...")
    es._last_used_time = time.time() - 150.0

    # Let the loop run to trigger the watchdog check (which checks every 30s)
    print("   Waiting for watchdog tick...")
    for i in range(35):
        await asyncio.sleep(1)
        if es._shared_encoder is None:
            print(f"   [Tick {i+1}] Watchdog detected idle state and unloaded model successfully!")
            break

    print(f"5. Final model status: {es._shared_encoder}")
    assert es._shared_encoder is None, "Model should be automatically unloaded"
    assert es._unload_task is None, "Watchdog task should have exited"
    print("🎉 SUCCESS: Model was automatically unloaded and memory was reclaimed!")

if __name__ == "__main__":
    asyncio.run(test_fastembed_unload())
