import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest, SupportIntent, SupportProductInfo

@pytest.fixture
def mock_db():
    from sqlalchemy.ext.asyncio import AsyncSession
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def base_ctx(mock_db):
    req = SupportRequest(
        message="init",
        session_id="test_beppin_session",
        product_slug="beppin-body-serum" # Assume current product context
    )
    return SupportContext(
        db=mock_db,
        request=req,
        session_id="test_beppin_session",
        dna=NeuralDNA(segment="NEW"),
        p_info=SupportProductInfo(
            id="beppin-001",
            name="Beppin Body Virgin White Serum",
            price=249000.0,
            price_display="249.000đ",
            slug="beppin-body-serum"
        )
    )

@pytest.mark.asyncio
async def test_turn_1_beppin_order_no_info(base_ctx):
    """
    TURN 1: "cho 1 Beppin Body Virgin White Serum"
    User is Guest (Khách vãn lai), provided no phone, no address.
    EXPECTED: Helen asks for BOTH Phone and Address (Fix for Ghost Address).
    """
    handler = OrderHandler()
    base_ctx.request.message = "cho 1 Beppin Body Virgin White Serum"
    
    # Mock Lead Extractor: Found items, but no phone/address
    mock_lead = MagicMock()
    mock_lead.items = [{"name": "Beppin Body Virgin White Serum", "quantity": 1}]
    mock_lead.customer_phone = None
    mock_lead.customer_address = None
    mock_lead.is_definite_purchase = False
    mock_lead.possible_provinces = []
    
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        mock_ext.return_value = mock_lead
        
        await handler.handle(base_ctx)
        
        reply = base_ctx.replies[0]
        print(f"Turn 1 Reply: {reply}")
        
        # PROOF: Should NOT claim to have seen the address
        assert "Số điện thoại và Địa chỉ" in reply
        assert "địa chỉ thì Helen đã thấy rồi" not in reply

@pytest.mark.asyncio
async def test_turn_2_standalone_phone(base_ctx):
    """
    TURN 2: "0949901122"
    User provides ONLY phone number.
    EXPECTED: OrderHandler triggers and processes it (Fix for Memory Loop).
    """
    handler = OrderHandler()
    base_ctx.request.message = "0949901122"
    
    # Mock Lead Extractor: Successfully extracted phone and hydrated info from history
    mock_lead = MagicMock()
    mock_lead.items = [{"name": "Beppin Body Virgin White Serum", "quantity": 1}]
    mock_lead.customer_phone = "0949901122"
    mock_lead.customer_address = "123 Đường ABC, HCM" # Hydrated from history (mocked)
    mock_lead.processed_order_id = "ORD-SUCCESS-123"
    mock_lead.is_definite_purchase = True
    
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        mock_ext.return_value = mock_lead
        
        # Mock DB for Order lookup after success
        mock_order = MagicMock()
        mock_order.items = [{"quantity": 1}]
        mock_order.total_amount = 249000
        mock_order.customer_address = "123 Đường ABC, HCM"
        mock_order.status = "SUCCESS"
        mock_order.id = "order-uuid-123"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            mock_order, # First call: Order lookup
            None        # Second call: Voucher lookup (return None to avoid complexity)
        ]
        base_ctx.db.execute.return_value = mock_result
        
        # Check if handler triggers (returns True)
        res = await handler.handle(base_ctx)
        
        assert res is True
        reply = base_ctx.replies[0]
        print(f"Turn 2 Reply: {reply}")
        
        # PROOF: Order success message should appear
        assert "chúc mừng Anh/Chị đã đặt hàng thành công" in reply
        assert "249.000đ" in reply

@pytest.mark.asyncio
async def test_turn_1_hallucinated_address(base_ctx):
    """
    TURN 1 (Hallucination Case): User says "cho 1 Beppin..."
    AI hallucinations "Virgin White Serum" as the address.
    EXPECTED: OrderHandler sees this is NOT a resolved address (shipping_days is None).
    It should ask for BOTH Phone and Address.
    """
    handler = OrderHandler()
    base_ctx.request.message = "cho 1 Beppin Body Virgin White Serum"
    
    # Mock Lead Extractor: Returns a hallucinated address
    mock_lead = MagicMock()
    mock_lead.items = [{"name": "Beppin Body Virgin White Serum", "quantity": 1}]
    mock_lead.customer_phone = None
    mock_lead.customer_address = "Virgin White Serum" # HALLUCINATION
    mock_lead.shipping_days = None # Resolver failed
    mock_lead.is_definite_purchase = False
    mock_lead.possible_provinces = []
    
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        mock_ext.return_value = mock_lead
        
        await handler.handle(base_ctx)
        
        reply = base_ctx.replies[0]
        print(f"Hallucination Reply: {reply}")
        
        # PROOF: Even though customer_address is truthy, it's not resolved.
        # Should ask for BOTH.
        assert "Số điện thoại và Địa chỉ" in reply
        assert "địa chỉ thì Helen đã thấy rồi" not in reply

if __name__ == "__main__":
    # Fallback for manual run if pytest fails
    async def run_manual():
        ctx = base_ctx(AsyncMock(), SupportRequest(message="", session_id="s"))
        await test_turn_1_beppin_order_no_info(ctx)
        await test_turn_2_standalone_phone(ctx)
    asyncio.run(run_manual())
