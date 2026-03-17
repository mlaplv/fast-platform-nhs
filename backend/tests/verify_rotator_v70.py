import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.ai_engine.core.key_rotator import key_rotator

async def test_rotation():
    print("--- Testing SmartKeyRotator V70.0 (Mocked Redis) ---")
    
    # 0. Mock Redis Client
    key_rotator._use_redis = True
    mock_client = AsyncMock()
    
    # Mock exists to return False by default (not blacklisted)
    mock_client.exists.return_value = False
    # Mock hgetall to return basic metadata
    mock_client.hgetall.return_value = {"fail_count": "0", "health_score": "100", "last_used": "0"}
    # Mock hincrby to return an integer
    mock_client.hincrby.return_value = 1
    
    key_rotator.client = mock_client
    key_rotator.keys = ["KEY_1_XXXXXXXXX", "KEY_2_XXXXXXXXX", "KEY_3_XXXXXXXXX"]

    # 1. Test get_key
    key = await key_rotator.get_key()
    print(f"Chosen Key: {key}")
    
    # 2. Test Success
    await key_rotator.set_success(key)
    print("Marked success.")
    mock_client.hset.assert_called()
    
    # 3. Test Failure (Transient)
    await key_rotator.mark_unhealthy(key, reason="rate_limit")
    print("Marked rate_limit (Cooldown).")
    mock_client.hincrby.assert_called()
    
    # 4. Test Failure (Permanent)
    # Mock exists to return True for the blacklisted index (index 0)
    mock_client.exists.side_effect = lambda k: "v70:black:0" in k
    
    await key_rotator.mark_unhealthy(key_rotator.keys[0], reason="401 Unauthorized")
    print("Marked 401 for KEY_1 (Blacklisted).")
    
    # 5. Check if blacklisted key is avoided
    for _ in range(20):
        k = await key_rotator.get_key()
        if k == key_rotator.keys[0]:
            print("❌ FAILURE: Blacklisted key was selected!")
            return
    print("✅ SUCCESS: Blacklisted key was avoided.")

if __name__ == "__main__":
    asyncio.run(test_rotation())
