import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.services.commerce.operatives.handlers.greeting import GreetingHandler
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.support_agent import SupportAgentOperative
from backend.schemas.support import SupportRequest, SupportIntent
from backend.schemas.order import OrderCreateRequest

@pytest.fixture
def mock_db():
    from sqlalchemy.ext.asyncio import AsyncSession
    m = AsyncMock(spec=AsyncSession)
    # Ensure scalar is also an AsyncMock
    m.scalar = AsyncMock()
    return m

@pytest.fixture
def base_ctx(mock_db):
    return SupportContext(
        db=mock_db,
        request=SupportRequest(message="test", session_id="sid_123"),
        session_id="sid_123",
        dna=NeuralDNA(segment="NEW", available_points=500, point_value_vnd=1000)
    )

@pytest.fixture(autouse=True)
def mock_xohi():
    with patch("backend.services.commerce.operatives.support_agent.xohi_memory") as m:
        m.client.get = AsyncMock(return_value=None)
        m.get_user_context = AsyncMock(return_value=None)
        m.set_user_context = AsyncMock()
        yield m

@pytest.mark.asyncio
async def test_loyalty_dna_hydration():
    """Unit 1: Test that Neural DNA hydrates points and name correctly."""
    operative = SupportAgentOperative()
    mock_db = AsyncMock()
    mock_db.scalar = AsyncMock(return_value="Lê Anh") # Mock User.name query
    
    # Mock Loyalty
    mock_loyalty = MagicMock()
    mock_loyalty.available_points = 1250
    mock_loyalty.balance_seal = "valid_seal"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_loyalty
    
    mock_db.execute.side_effect = [
        mock_result, # select(UserLoyalty)
        MagicMock(scalar_one_or_none=lambda: MagicMock(value={"value":1000})), # select(SystemSetting)
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # select(Order) - history
    ]
    
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        
        dna = await operative._fetch_neural_dna(mock_db, "sid_123", user_id="user_abc")
        
        assert dna.available_points == 1250
        assert dna.customer_name == "Lê Anh"
        assert mock_verify.called is True

@pytest.mark.asyncio
async def test_military_security_tamper_detection():
    """Unit 2: Test that tampered loyalty data blocks Helen."""
    operative = SupportAgentOperative()
    mock_db = AsyncMock()
    mock_db.scalar = AsyncMock(return_value="Any Name")
    
    # Mock LoyaltyService.verify_loyalty_integrity to return False (Tamper detected)
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = False
        
        dna = await operative._fetch_neural_dna(mock_db, "sid_123", user_id="hacker_123")
        
        # Balance should default to 0 for security
        assert dna.available_points == 0

@pytest.mark.asyncio
async def test_greeting_hook_with_points(base_ctx):
    """Unit 3: Test that greeting includes points hook."""
    handler = GreetingHandler()
    base_ctx.dna.available_points = 888
    base_ctx.dna.customer_name = "Sếp Tổng"
    base_ctx.dna.segment = "VIP"
    
    res = await handler.handle(base_ctx)
    assert res is True # TERMINATE: Pure greeting consumed.
    assert any("Sếp Tổng" in r for r in base_ctx.replies)
    assert any("888 điểm" in r for r in base_ctx.replies)

@pytest.mark.asyncio
async def test_order_redemption_with_cap():
    """Unit 4: Test order creation with 1% points cap enforcement."""
    from backend.services.commerce.order import OrderService
    service = OrderService()
    mock_db = AsyncMock()
    
    # Mock Loyalty & Setting lookups
    mock_loyalty = MagicMock()
    mock_loyalty.available_points = 100000 
    mock_loyalty.total_spent = 0
    mock_loyalty.user_id = "user_123"
    
    mock_setting = MagicMock()
    mock_setting.value = {"value": 1000} # 1pt = 1000đ
    
    # Mock the sequence of DB calls
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: mock_loyalty), # select(UserLoyalty)
        MagicMock(scalar_one_or_none=lambda: mock_setting), # select(SystemSetting)
    ]
    
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        
        data = OrderCreateRequest(
            customer_name="Test User",
            customer_email="test@micsmo.com",
            total_amount=1000000, 
            items=[],
            points_to_redeem=5000 
        )
        
        # Patching internal models and utils
        with patch("backend.services.commerce.loyalty.LoyaltyService._create_balance_seal", return_value="new_seal"):
            with patch("backend.services.commerce.loyalty.LoyaltyService._create_transaction_token", return_value="token"):
                with patch("backend.services.commerce.order.event_bus.emit", new_callable=AsyncMock):
                    with patch("backend.services.commerce.order.Order") as mock_order_model:
                        with patch("backend.services.commerce.order.uuid.uuid4", return_value=MagicMock(hex="test-id")):
                             await service.create_order(mock_db, data, ip="127.0.0.1", ua="Test", user_id="user_123")
                             
                             # 1% of 1,000,000 is 10,000đ
                             # 10,000đ = 10 pts
                             call_args = mock_order_model.call_args[1]
                             assert call_args["points_redeemed"] == 10
                             assert call_args["point_discount_amount"] == 10000.0
                             assert call_args["total_amount"] == 990000.0

@pytest.mark.asyncio
async def test_fast_path_personalized_greeting():
    """Unit 5: Test that the Fast-Path classification personalizes the quick_reply."""
    operative = SupportAgentOperative()
    mock_db = AsyncMock()
    # Mock User.name query
    mock_db.scalar = AsyncMock(return_value="Lê Anh")
    
    # Mock Loyalty and other DB calls for DNA
    mock_loyalty = MagicMock(available_points=125, balance_seal="seal")
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_loyalty
    
    # Fetch DNA internal calls: Loyalty Integrity, User Loyalty, System Setting, Order History
    mock_db.execute.side_effect = [
        mock_res, # Loyalty Integrity check
        mock_res, # User Loyalty fetch
        MagicMock(scalar_one_or_none=lambda: MagicMock(value={"value":1000})), # System Setting
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # Order History
    ]
    
    from backend.services.commerce.operatives.support_agent import FastIntentResponse
    mock_fast_res = FastIntentResponse(intent="GREETING", quick_reply="Chào sếp Lê Anh, Helen có thể giúp gì cho sếp ạ?")
    
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        with patch("backend.services.ai_engine.core.trinity_bridge.trinity_bridge.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_fast_res
            
            req = SupportRequest(message="Chào Helen", session_id="sid_123", user_id="user_abc")
            res = await operative.chat(req, db=mock_db)
            
            assert "Lê Anh" in res.reply
            assert res.status == "DONE"
            # Verify that trinity_bridge was called with the correct deps
            args, kwargs = mock_run.call_args
            assert kwargs["deps"].customer_name == "Lê Anh"
