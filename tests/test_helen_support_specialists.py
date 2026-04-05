import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.services.commerce.operatives.handlers.guardrail import GuardrailHandler
from backend.services.commerce.operatives.handlers.greeting import GreetingHandler
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler, ConsultantResponse
from backend.services.commerce.operatives.router import SupportRouter
from backend.schemas.support import SupportRequest, SupportIntent

@pytest.fixture
def mock_db():
    from sqlalchemy.ext.asyncio import AsyncSession
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def base_request():
    return SupportRequest(
        message="Hello",
        session_id="test_session",
        product_slug="hong-son"
    )

@pytest.fixture
def base_ctx(mock_db, base_request):
    return SupportContext(
        db=mock_db,
        request=base_request,
        session_id="test_session",
        dna=NeuralDNA(segment="NEW")
    )

@pytest.mark.asyncio
async def test_guardrail_rejection(base_ctx):
    """ZONE 4: Test that sensitive topics are immediately rejected."""
    handler = GuardrailHandler()
    base_ctx.request.message = "Tôi bị hôi miệng muốn tư vấn"
    res = await handler.handle(base_ctx)
    assert res is True
    assert "Helen rất tiếc" in base_ctx.replies[0]
    assert base_ctx.intent == SupportIntent.UNKNOWN

@pytest.mark.asyncio
async def test_greeting_pass_through(base_ctx):
    """ZONE 1: Test that greeting prepends but does not stop the pipeline."""
    handler = GreetingHandler()
    base_ctx.request.message = "Chào Helen nhé"
    res = await handler.handle(base_ctx)
    assert res is False # False = pipeline continues
    assert "Dạ Helen chào Anh/Chị! 🌸" in base_ctx.replies[0]

@pytest.mark.asyncio
async def test_order_success_stops_pipeline(base_ctx):
    """ZONE 3: Test that a successful purchase stops further experts from running."""
    handler = OrderHandler()
    base_ctx.request.message = "Cho anh 3 lọ về nhà nhé"
    
    mock_lead = MagicMock()
    mock_lead.processed_order_id = "test-order-999"
    mock_lead.customer_phone = "0949901122"
    mock_lead.shipping_days = "2-3 ngày"
    
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        mock_ext.return_value = mock_lead
        
        # Mock DB response for Order lookup
        mock_order = MagicMock()
        mock_order.items = [{"quantity": 3}]
        mock_order.total_amount = 498000
        mock_order.customer_address = "37 Ngô Quyền, Đắk Lắk"
        
        # Result mock for session.execute
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        base_ctx.db.execute.return_value = mock_result
        
        res = await handler.handle(base_ctx)
        assert res is True # STOPS pipeline
        # "test-order-999"[-8:] is "rder-999" -> capitalized "RDER-999"
        assert "RDER-999" in base_ctx.replies[0]
        assert "498.000đ" in base_ctx.replies[0]

@pytest.mark.asyncio
async def test_router_priority_and_concatenation(base_ctx):
    """Integration: Test that router runs Greeting then Order and joins them."""
    router = SupportRouter()
    base_ctx.request.message = "Chào Helen, chốt cho anh 1 lọ nhé"
    
    # Mock Order success
    mock_lead = MagicMock()
    mock_lead.processed_order_id = "ORD-12345678"
    mock_lead.shipping_days = "1 ngày"
    
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        mock_ext.return_value = mock_lead
        
        # Mock Order DB lookup
        mock_order = MagicMock()
        mock_order.items = [{"quantity": 1}]
        mock_order.total_amount = 249000
        mock_order.customer_address = "Sài Gòn"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order
        base_ctx.db.execute.return_value = mock_result
        
        # Patch Consultant to verify it is NOT called
        with patch("backend.services.commerce.operatives.handlers.consultant.trinity_bridge.run", new_callable=AsyncMock) as mock_llm:
            await router.process(base_ctx)
            
            # 1. Greeting should be first
            assert "Dạ Helen chào" in base_ctx.replies[0]
            # 2. Order should be second
            # "ORD-12345678"[-8:] is "12345678"
            assert "12345678" in base_ctx.replies[1]
            
            # 3. Consultant should be skipped because Order returned True
            assert mock_llm.called is False

@pytest.mark.asyncio
async def test_fallback_to_consultant(base_ctx):
    """ZONE 2: Test that if no order is identified, it falls back to Consultant expert."""
    router = SupportRouter()
    base_ctx.request.message = "Chào em, tại sao anh lại bị hôi nách?"
    
    # Mock Order failure (no lead)
    with patch("backend.services.commerce.operatives.handlers.order.lead_extractor.extract_and_convert", new_callable=AsyncMock) as mock_ext:
        mock_ext.return_value = None
        
        # Mock Consultant success
        mock_llm_res = MagicMock()
        mock_llm_res.data = ConsultantResponse(
            reply="Dạ đó là do vi khuẩn phân hủy axit béo ạ...",
            intent="GENERAL_ADVICE"
        )
        
        with patch("backend.services.commerce.operatives.handlers.consultant.Agent") as mock_agent:
            with patch("backend.services.commerce.operatives.handlers.consultant.trinity_bridge.run", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_llm_res
                
                await router.process(base_ctx)
                
                # Ensure Consultant was reached
                assert mock_llm.called is True
                # Greeting + Consultant (because Order failed)
                assert any("Dạ Helen chào" in r for r in base_ctx.replies)
                assert any("axit béo" in r for r in base_ctx.replies)
                assert base_ctx.intent == SupportIntent.GENERAL_ADVICE
