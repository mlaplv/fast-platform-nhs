import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.services.commerce.logic.lead_extractor import lead_extractor, validate_vietnam_phone

# Elite V2.2: Lead Conversion Test Suite (Unit)

def test_phone_validation():
    """Verify Elite V2.2 VN Phone standards."""
    assert validate_vietnam_phone("0987654321") == "0987654321"
    assert validate_vietnam_phone("84987654321") == "0987654321"
    assert validate_vietnam_phone("+84 987 654 321") == "0987654321"
    assert validate_vietnam_phone("12345") is None
    assert validate_vietnam_phone("012345678") is None # 9 digits

@pytest.mark.asyncio
async def test_extraction_logic_purchase():
    """Verify AI extraction for definite purchase intent."""
    # Mock DB
    db = AsyncMock()
    
    # We can't easily mock the AI Agent's .run without a lot of setup,
    # but we can test the helper logic or use a local mock for the agent itself
    # for now, let's verify the logic flow if AI returns valid data.
    
    # Testing the 'is_definite_purchase' mapping
    message = "Chốt cho mình 2 lọ serum này tới số 0912345678, mình ở Hà Nội."
    
    # Actually running against REAL AI if KEY is present, otherwise mock
    # For safety in CI, we should mock.
    
    from backend.services.commerce.logic.lead_extractor import _lead_extraction_agent, ExtractedLead
    
    # Mocking the AI response
    mock_res = MagicMock()
    mock_res.data = ExtractedLead(
        customer_name="Khách test",
        customer_phone="0912345678",
        customer_address="Hà Nội",
        items=[{"name": "serum", "quantity": 2, "price": 250000}],
        is_definite_purchase=True
    )
    
    # Patch the agent run
    async def mock_run(*args, **kwargs):
        return mock_res
        
    _lead_extraction_agent.run = mock_run
    
    lead = await lead_extractor.extract_and_convert(db, message, "session_123")
    
    assert lead is not None
    assert lead.customer_phone == "0912345678"
    assert lead.is_definite_purchase is True
    assert len(lead.items) == 1
    
@pytest.mark.asyncio
async def test_extraction_logic_inquiry():
    """Verify AI ignores casual inquiries (No draft created)."""
    db = AsyncMock()
    
    from backend.services.commerce.logic.lead_extractor import _lead_extraction_agent, ExtractedLead
    
    mock_res = MagicMock()
    mock_res.data = ExtractedLead(
        customer_name=None,
        customer_phone=None,
        customer_address=None,
        items=[],
        is_definite_purchase=False
    )
    
    async def mock_run(*args, **kwargs):
        return mock_res
        
    _lead_extraction_agent.run = mock_run
    
    lead = await lead_extractor.extract_and_convert(db, "Cái này giá bao nhiêu bạn?", "session_456")
    assert lead.is_definite_purchase is False
    # Draft order should not be created (verify db.add was not called)
    db.add.assert_not_called()
