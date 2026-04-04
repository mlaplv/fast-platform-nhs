"""
Manual Verification: Helen Lead Extraction & Auto-Draft (Elite V2.2)
===================================================================
Standard Architecture: Bridge-Oriented | Full Async I/O | Static Typing
"""
import os
import sys
import asyncio
import logging
import json
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# Load environment before any imports from backend
from dotenv import load_dotenv
load_dotenv()

# Override REDIS_URL and DATABASE_URL for host execution
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("helen-test")

# Import target components
from backend.services.commerce.logic.lead_extractor import lead_extractor
from backend.services.commerce.operatives.support_agent import support_agent, SupportRequest, SupportProductInfo
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi_memory import xohi_memory

async def run_manal_test():
    print("\n" + "="*80)
    print("🚀 HELEN ELITE V2.2 ARCHITECTURAL VERIFICATION")
    print("="*80 + "\n")

    # 1. Infrastructure Setup (Standard Elite V2.2)
    # Point Redis to localhost for host execution
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    # Ensure TrinityBridge is initialized (loads keys + models dynamically)
    await trinity_bridge.initialize()

    # Mock Database Session (Minimal for Order creation detection)
    mock_db = MagicMock(spec=AsyncSession)
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()

    # 2. Preparation
    test_message = "xíp 1 lọ hôi nách về 336/44 Nguyễn Văn Luông, Phú Lâm, HCM), 0949901122, lập"
    session_id = "manual-test-helen-2026"
    product_slug = "hoi-nach-helen"

    print(f"[INPUT] Message: {test_message}")
    print(f"[INPUT] Product Context: {product_slug}")
    print("-" * 40)

    # 3. Execution Phase A: Lead Extraction (Using the new Bridge logic)
    print("\n[STEP 1] Running Extraction Engine (TrinityBridge + LeadExtractor)...")
    
    try:
        lead_result = await lead_extractor.extract_and_convert(
            db=mock_db,
            message=test_message,
            session_id=session_id,
            current_product_slug=product_slug
        )

        if lead_result:
            print("\n✅ EXTRACTION SUCCESSFUL")
            print(f"   - Name:    {lead_result.customer_name}")
            print(f"   - Phone:   {lead_result.customer_phone}")
            print(f"   - Address: {lead_result.customer_address}")
            print(f"   - Intent:  {'🔥 HIGH (Purchase)' if lead_result.is_definite_purchase else 'ℹ️ Inquiry'}")
            print(f"   - Items:   {json.dumps([i.model_dump() for i in lead_result.items], ensure_ascii=False)}")
        else:
            print("\n❌ EXTRACTION FAILED (Check Logs for Quota/Error)")

    except Exception as e:
        print(f"\n💥 CRITICAL FAILURE in Extraction: {e}")

    # 4. Execution Phase B: AI Support Response
    print("\n" + "-"*40)
    print("[STEP 2] Running Helen Brain Logic (Response Generation)...")

    # Mock context fetching for test
    support_agent._fetch_chat_context = AsyncMock(return_value="")
    
    import backend.services.commerce.operatives.support_agent as sa_module
    sa_module._fetch_product_context = AsyncMock(return_value=(
        "Sản phẩm Hôi Nách Helen - Chuyên trị hôi nách, mồ hôi tay chân. Giá 150k/lọ. Hiệu quả ngay lần đầu.",
        SupportProductInfo(
            id="1", 
            name="Hôi Nách Helen", 
            price=150000, 
            price_display="150,000 VND", 
            slug="hoi-nach-helen"
        )
    ))

    request = SupportRequest(
        message=test_message,
        session_id=session_id,
        product_slug=product_slug
    )

    try:
        ai_response = await support_agent.process_brain_logic(request, mock_db)
        
        print("\n✅ AI RESPONSE GENERATED")
        print(f"   - Intent: {ai_response.intent}")
        print(f"   - Reply:  {ai_response.reply}")
        print(f"   - Status: {ai_response.status}")

    except Exception as e:
        print(f"\n💥 CRITICAL FAILURE in Brain Logic: {e}")

    print("\n" + "="*80)
    print("🏁 VERIFICATION COMPLETED")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_manal_test())
