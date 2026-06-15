import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.commerce.logic.lead_extractor import LeadExtractor, ExtractedLead, LeadOrderItem
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest, SupportProductInfo
from backend.database.models.system import SupportChatHistory

@pytest.fixture
def mock_db():
    from sqlalchemy.ext.asyncio import AsyncSession
    db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_result
    return db

@pytest.mark.asyncio
async def test_v37_ghost_address_blocking(mock_db):
    """
    Simulate: "cho 1 Beppin Body Virgin White Serum"
    V3.7 Semantic Guard should block 'Virgin White Serum' as an address.
    """
    msg = "cho 1 Beppin Body Virgin White Serum"
    
    # Mock AI to return a hallucination (mimicking the failure case)
    mock_ai_result = {
        "items": [{"name": "Beppin Body Virgin White Serum", "quantity": 1}],
        "customer_phone": None,
        "customer_address": "Virgin White Serum",
        "is_definite_purchase": True
    }
    
    # Mock resolve_product to prevent it from returning None/erroring
    mock_p = MagicMock()
    mock_p.id = "p1"
    mock_p.price = 100
    
    # Mock user_service.get_or_resolve_customer
    mock_user_res = (MagicMock(), True, None, "NEW")
    
    with patch("backend.services.commerce.logic.lead_extractor.trinity_bridge.run", new_callable=AsyncMock) as mock_run:
        with patch("backend.services.commerce.logic.lead_extractor.xohi_memory.get_order_draft", new_callable=AsyncMock) as mock_redis:
            with patch("backend.services.commerce.logic.lead_extractor.LeadExtractor._resolve_product", new_callable=AsyncMock) as mock_res_prod:
                with patch("backend.services.commerce.logic.lead_extractor.user_service.get_or_resolve_customer", new_callable=AsyncMock) as mock_res_user:
                    mock_run.return_value = mock_ai_result
                    mock_redis.return_value = None
                    mock_res_prod.return_value = mock_p
                    mock_res_user.return_value = mock_user_res
                    
                    lead = await LeadExtractor.extract_and_convert(mock_db, msg, "test_session_v37")
                    
                    # PROOF: Address must be NULL because it contains product keywords (Serum, White)
                    assert lead.customer_address is None
                    print("\n✅ V3.7 Ghost Address (Semantic Guard) PASSED.")

@pytest.mark.asyncio
async def test_v37_deterministic_phone_recovery(mock_db):
    """
    Simulate: "0949901122"
    V3.7 Deterministic Scanner should rescue the SĐT even if LLM fails (returns None).
    """
    msg = "0949901122"
    
    # Mock AI failing to extract anything
    mock_ai_result = {
        "items": [],
        "customer_phone": None,
        "customer_address": None,
        "is_definite_purchase": False
    }
    
    # Mock user_service.get_or_resolve_customer
    mock_user_res = (MagicMock(), True, None, "NEW")

    with patch("backend.services.commerce.logic.lead_extractor.trinity_bridge.run", new_callable=AsyncMock) as mock_run:
        with patch("backend.services.commerce.logic.lead_extractor.xohi_memory.get_order_draft", new_callable=AsyncMock) as mock_redis:
            with patch("backend.services.commerce.logic.lead_extractor.user_service.get_or_resolve_customer", new_callable=AsyncMock) as mock_res_user:
                mock_run.return_value = mock_ai_result
                mock_redis.return_value = None
                mock_res_user.return_value = mock_user_res
                
                lead = await LeadExtractor.extract_and_convert(mock_db, msg, "test_session_v37")
                
                # PROOF: Regex scanner rescued the phone
                assert lead.customer_phone == "0949901122"
                print("✅ V3.7 Deterministic Phone Recovery PASSED.")

@pytest.mark.asyncio
async def test_v37_history_role_filtering(mock_db):
    """
    Simulate: History contains Helen's reply with 'Đia chỉ: ...'
    V3.7 Role Filtering must ignore assistant messages.
    """
    from backend.services.commerce.logic.lead_extractor import ExtractedLead
    lead = ExtractedLead(items=[], customer_phone=None, customer_address=None)
    
    with patch("backend.services.commerce.logic.lead_extractor.GeminiSecurity.decrypt") as mock_decrypt:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        await LeadExtractor._hydrate_from_history(mock_db, "test_session_v37", lead)
        
        args, _ = mock_db.execute.call_args
        sql_stmt = args[0]
        
        # Check compiled SQL and parameters
        compiled = sql_stmt.compile()
        sql_str = str(compiled).lower()
        
        assert "role" in sql_str
        # Check that 'user' value is in the parameters
        assert compiled.params["role_1"] == "user"
        
        assert lead.customer_address is None
        print("✅ V3.7 History Role Filtering (Ghost Prevention) PASSED.")

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
