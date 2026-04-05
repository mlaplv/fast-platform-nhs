import asyncio
import logging
from typing import Dict, cast
from pydantic import JsonValue
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel

# ══════════════════════════════════════════════════════════════
# ELITE V2.2: HERITAGE VERIFICATION SUITE
# ══════════════════════════════════════════════════════════════
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, MedicalShieldMixin
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge, _G_SAFETY_NONE
from backend.services.commerce.operatives.support_agent import SupportAgentOperative

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify-v22")

async def test_medical_masking():
    """Verify that MedicalShield correctly rewrites sensitive Vietnamese terms."""
    logger.info("🧪 [Test 1] MedicalShield Masking...")
    # SupportAgentOperative inherits MedicalShieldMixin via BaseAgentOperative
    agent = SupportAgentOperative()
    
    raw_text = "Tôi bị hôi nách và muốn trị dứt điểm bàng thuốc nam."
    masked = await agent._mask_sensitive_medical_terms(raw_text)
    
    logger.info(f"   Original: {raw_text}")
    logger.info(f"   Masked:   {masked}")
    
    assert "tăng tiết mồ hôi vùng dưới cánh tay" in masked
    assert "kiểm soát triệu chứng hiệu quả" in masked
    assert "sản phẩm chuyên dụng" in masked
    logger.info("   ✅ Passed: Semantic rewrite successful.")

async def test_trinity_bridge_structural_fix():
    """Verify that TrinityBridge cleans its kwargs by-reference before AI call."""
    logger.info("🧪 [Test 2] TrinityBridge Structural Integrity (Kwarg Leakage Check)...")
    
    kwargs: Dict[str, JsonValue] = {
        "safety_none": True,
        "model_settings": {"temperature": 0.5},
        "session_id": "test-v22",
        "custom_param": "stay-put"
    }
    
    # We test the internal _provision_model method which now takes params as reference
    m_name, m_key = "gemini-1.5-flash", "test-key"
    model, ms = trinity_bridge._provision_model(m_name, m_key, kwargs)
    
    # Assertions
    assert "safety_none" not in kwargs, "CRITICAL: safety_none MUST be popped from dictionary."
    assert "model_settings" not in kwargs, "CRITICAL: model_settings MUST be popped from dictionary."
    assert "custom_param" in kwargs, "Normal params MUST remain in dictionary."
    assert ms["google_safety_settings"] == _G_SAFETY_NONE
    assert ms["temperature"] == 0.5
    
    logger.info("   ✅ Passed: TrinityBridge correctly cleans its kwargs (No TypeError risk).")

async def test_heritage_inheritance():
    """Verify standard Elite V2.2 inheritance hierarchy."""
    logger.info("🧪 [Test 3] Architectural Heritage Inheritance...")
    
    agent = SupportAgentOperative()
    
    assert isinstance(agent, BaseAgentOperative), "SupportAgentOperative MUST inherit from BaseAgentOperative."
    assert isinstance(agent, MedicalShieldMixin), "SupportAgentOperative MUST possess MedicalShieldMixin heritage."
    assert agent.agent_id == "support_agent"
    
    logger.info("   ✅ Passed: Elite V2.2 Heritage confirmed.")

async def main():
    logger.info("🚀 Starting Elite V2.2 Heritage Verification (Structural Audit)")
    try:
        await test_medical_masking()
        await test_trinity_bridge_structural_fix()
        await test_heritage_inheritance()
        logger.info("\n🏆 ALL TESTS PASSED. SYSTEM IS STRUCTURALLY SOUND (ELITE V2.2 compliant).")
    except AssertionError as ae:
        logger.error(f"❌ TEST FAILED: {ae}")
        exit(1)
    except Exception as e:
        logger.error(f"❌ SYSTEM ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
