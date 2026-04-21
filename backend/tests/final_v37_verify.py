import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.commerce.logic.lead_extractor import LeadExtractor, ExtractedLead

async def final_cto_verification():
    print("--- 🔬 FINAL CTO VERIFICATION: HELEN ELITE V3.7 ---")
    
    # Properly mock a SQLAlchemy result
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []
    
    db = AsyncMock()
    db.execute.return_value = mock_res
    
    session_id = "cto_test_session_v37"

    # CASE 1: Ghost Address Blocking (Virgin White Serum)
    print("\nCase 1: Blocking Ghost Address 'Virgin White Serum'...")
    msg1 = "cho 1 Beppin Body Virgin White Serum"
    ai_res1 = {
        "items": [{"name": "Beppin Body Virgin White Serum", "quantity": 1}],
        "customer_phone": None,
        "customer_address": "Virgin White Serum",
        "is_definite_purchase": True
    }
    
    # Mock resolve_product to return a dummy product
    mock_p = MagicMock()
    mock_p.id = "p1"
    mock_p.price = 100
    mock_p.discount_price = None
    mock_p.slug = "beppin-body-virgin-white-serum"

    # Mock user_service
    mock_user = MagicMock()
    mock_user.id = "u1"
    mock_user.email = "test@guest.com"
    mock_user_res = (mock_user, True, None, "NEW")

    with patch("backend.services.commerce.logic.lead_extractor.trinity_bridge.run", new_callable=AsyncMock) as mock_run:
        with patch("backend.services.commerce.logic.lead_extractor.xohi_memory.get_order_draft", new_callable=AsyncMock) as mock_redis:
            with patch("backend.services.commerce.logic.lead_extractor.LeadExtractor._resolve_product", new_callable=AsyncMock) as mock_res_prod:
                with patch("backend.services.commerce.logic.lead_extractor.user_service.get_or_resolve_customer", new_callable=AsyncMock) as mock_res_user:
                    mock_run.return_value = ai_res1
                    mock_redis.return_value = None
                    mock_res_prod.return_value = mock_p
                    mock_res_user.return_value = mock_user_res
                    
                    lead = await LeadExtractor.extract_and_convert(db, msg1, session_id)
                    if lead is None:
                        print("❌ FAILED: extract_and_convert returned None (Crashed)")
                        return
                        
                    print(f"  - Extracted Address: '{lead.customer_address}'")
                    if lead.customer_address is None:
                        print("  ✅ SUCCESS: Semantic Guard blocked the ghost address.")
                    else:
                        print("  ❌ FAILED: Ghost address was NOT blocked.")

    # CASE 2: Deterministic SĐT Recovery
    print("\nCase 2: Deterministic SĐT Recovery (0949901122)...")
    msg2 = "0949901122"
    ai_res2 = {
        "items": [], "customer_phone": None, "customer_address": None, "is_definite_purchase": False
    }
    
    with patch("backend.services.commerce.logic.lead_extractor.trinity_bridge.run", new_callable=AsyncMock) as mock_run:
        with patch("backend.services.commerce.logic.lead_extractor.xohi_memory.get_order_draft", new_callable=AsyncMock) as mock_redis:
            with patch("backend.services.commerce.logic.lead_extractor.user_service.get_or_resolve_customer", new_callable=AsyncMock) as mock_res_user:
                mock_run.return_value = ai_res2
                mock_redis.return_value = None
                mock_res_user.return_value = mock_user_res
                
                lead = await LeadExtractor.extract_and_convert(db, msg2, session_id)
                print(f"  - Extracted Phone: '{lead.customer_phone}'")
                if lead.customer_phone == "0949901122":
                    print("  ✅ SUCCESS: Deterministic Scanner rescued the phone number.")
                else:
                    print("  ❌ FAILED: Phone number was NOT recovered.")

if __name__ == "__main__":
    asyncio.run(final_cto_verification())
