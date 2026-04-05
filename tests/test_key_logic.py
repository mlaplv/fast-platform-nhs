import asyncio
import os
import time
from typing import List, Dict, Optional, cast

# Setup imports - pointing to backend
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

async def test_key_rotation_logic():
    """
    Test 1: Verify Gemini Key Rotation.
    Ensures that keys are rotated and blacklisted keys are skipped.
    """
    print("\n🚀 Running Test 1: Key Rotation Logic...")
    # 1. Reset Redis for clean state
    await key_rotator.reset_health()
    
    # 2. Setup mock keys (AFTER reset_health to avoid overwrite)
    mock_keys = ["AIza_TEST_KEY_1", "AIza_TEST_KEY_2", "AIza_TEST_KEY_3"]
    key_rotator.keys = mock_keys
    key_rotator.index = 0
    
    # 3. Get first key
    k1 = await key_rotator.get_key()
    assert k1 in mock_keys
    
    # 4. Mock a failure for k1 and verify it gets blacklisted/cooldown
    await key_rotator.mark_unhealthy(k1, reason="auth_soft") 
    
    # 5. Get next key - should NOT be k1
    k2 = await key_rotator.get_key()
    assert k2 != k1
    assert k2 in mock_keys
    
    print(f"✅ Key Rotation Verified: {k1} -> {k2} (Skipped unhealthy)")

async def test_model_selection_and_key_matching():
    """
    Test 2: Verify Model Selection + Key Assignment.
    Ensures TrinityBridge builds the correct model chain and assigns a key.
    """
    print("\n🚀 Running Test 2: Model Selection & Key Matching...")
    # 1. Initialize bridge - This will load real keys/models
    await trinity_bridge.initialize()
    
    # 2. Test 'fast' role (should prioritize flash)
    role = "fast"
    discovered = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
    chain = await trinity_bridge.models_helper.build_chain(role, "", [], discovered)
    
    # Check prioritization logic (Elite V2.2: gemini-2.0-flash should be first)
    assert "gemini-2.0-flash" in chain[0]
    
    # 3. Verify key assignment for the selected model
    key = await key_rotator.get_key(model_name=chain[0])
    assert key is not None
    assert len(key) > 0
    
    print(f"✅ Model Selection Verified: Role '{role}' -> First Model: {chain[0]}")

async def test_soft_auth_cooldown_recovery():
    """
    Test 3: Verify Soft Auth Cooldown (10m) vs Hard Blacklist (30d).
    """
    print("\n🚀 Running Test 3: Soft Auth Cooldown Recovery...")
    test_key = "AIza_RECOVERY_TEST"
    
    # 1. Reset Redis
    await key_rotator.reset_health()
    
    # 2. Mock state
    key_rotator.keys = [test_key]
    
    # 3. Mark as SOFT_AUTH
    await key_rotator.mark_unhealthy(test_key, reason="auth_soft")
    
    # 4. Verify it is blacklisted in Redis
    kid = key_rotator._get_key_id(test_key)
    is_bl = await key_rotator.client.exists(f"{key_rotator.BLACKLIST_PREFIX}{kid}")
    assert is_bl == True
    
    # 5. Verify expected TTL (should be ~600 for SOFT_AUTH)
    ttl = await key_rotator.client.ttl(f"{key_rotator.BLACKLIST_PREFIX}{kid}")
    assert 0 < ttl <= 600
    
    print(f"✅ Soft Auth Cooldown Verified: TTL={ttl}s")

async def run_all():
    print("=== STARTING INTELLIGENT KEY TESTS (ELITE V2.2) ===")
    try:
        await test_key_rotation_logic()
        await test_model_selection_and_key_matching()
        await test_soft_auth_cooldown_recovery()
        print("\n🏆 ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_all())
