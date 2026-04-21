import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest, SupportProductInfo
from backend.services.commerce.logic.lead_extractor import ExtractedLead, LeadOrderItem

@pytest.mark.asyncio
async def test_reproduce_loop_bug():
    """
    Simulate the exact flow from the user's screenshot.
    Turn 1: "cho 1 Beppin Body Virgin White Serum"
    Turn 2: "0949901122"
    """
    handler = OrderHandler()
    mock_db = AsyncMock()
    
    # 1. TURN 1
    req1 = SupportRequest(message="cho 1 Beppin Body Virgin White Serum", session_id="loop_test_id")
    # Use model_construct to bypass strict AsyncSession validation for mock_db
    ctx1 = SupportContext.model_construct(
        db=mock_db, request=req1, session_id="loop_test_id",
        dna=NeuralDNA(segment="NEW"),
        p_info=SupportProductInfo(id="p1", name="Beppin", price=100, price_display="100", slug="beppin")
    )
    ctx1.replies = []
    
    # Mock Lead Extractor for Turn 1: Captured product, but NO phone/address
    lead1 = ExtractedLead(
        items=[LeadOrderItem(name="Beppin", quantity=1)],
        customer_phone=None,
        customer_address=None,
        shipping_days=None,
        is_definite_purchase=True
    )
    
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        with patch("backend.services.commerce.operatives.handlers.order.xohi_memory", new_callable=MagicMock) as mock_redis:
            mock_redis.set_order_draft = AsyncMock()
            mock_redis.get_order_draft = AsyncMock(return_value=None)
            mock_ext.return_value = lead1
            
            await handler.handle(ctx1)
            reply1 = ctx1.replies[0]
            print(f"\nTURN 1 REPLY: {reply1}")
            
    # 2. TURN 2
    req2 = SupportRequest(message="0949901122", session_id="loop_test_id")
    ctx2 = SupportContext.model_construct(
        db=mock_db, request=req2, session_id="loop_test_id",
        dna=NeuralDNA(segment="NEW"),
        p_info=SupportProductInfo(id="p1", name="Beppin", price=100, price_display="100", slug="beppin")
    )
    ctx2.replies = []
    
    # Mock Lead Extractor for Turn 2: Should capture the phone
    lead2 = ExtractedLead(
        items=[LeadOrderItem(name="Beppin", quantity=1)],
        customer_phone="0949901122",
        customer_address=None,
        shipping_days=None,
        is_definite_purchase=True
    )
    
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        with patch("backend.services.commerce.operatives.handlers.order.xohi_memory", new_callable=MagicMock) as mock_redis:
            mock_redis.set_order_draft = AsyncMock()
            # Simulate Redis holding the Turn 1 state
            mock_redis.get_order_draft = AsyncMock(return_value=lead1.model_dump())
            mock_ext.return_value = lead2
            
            await handler.handle(ctx2)
            reply2 = ctx2.replies[0] if ctx2.replies else "NO-REPLY"
            print(f"TURN 2 REPLY: {reply2}")
            # EXPECTED: Should acknowledge phone and ask for address
            # ACTUAL BUG REPORT SAYS: Reprints SĐT request (meaning it didn't see the phone)

if __name__ == "__main__":
    asyncio.run(test_reproduce_loop_bug())
