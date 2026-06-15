import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Generator, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.services.commerce.operatives.handlers.greeting import GreetingHandler
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.support_agent import SupportAgentOperative
from backend.schemas.support import SupportRequest, SupportIntent, SupportResponse
from backend.schemas.order import OrderCreateRequest

@pytest.fixture
def mock_db() -> AsyncMock:
    m: AsyncMock = AsyncMock(spec=AsyncSession)
    # Ensure scalar is also an AsyncMock
    m.scalar = AsyncMock()
    return m

@pytest.fixture
def base_ctx(mock_db: AsyncMock) -> SupportContext:
    return SupportContext(
        db=mock_db,
        request=SupportRequest(message="test", session_id="sid_123"),
        session_id="sid_123",
        dna=NeuralDNA(segment="NEW", available_points=500, point_value_vnd=1000)
    )

@pytest.fixture(autouse=True)
def mock_xohi() -> Generator[MagicMock, None, None]:
    with patch("backend.services.commerce.operatives.support_agent.xohi_memory") as m1:
        with patch("backend.services.commerce.operatives.context_helper.xohi_memory") as m2:
            with patch("backend.services.xohi_memory.xohi_memory") as m3:
                for m in [m1, m2, m3]:
                    m._use_redis = True
                    m.client = AsyncMock()
                    m.client.get = AsyncMock(return_value=None)
                    m.client.exists = AsyncMock(return_value=0)
                    m.client.incr = AsyncMock(return_value=1)
                    m.client.sadd = AsyncMock()
                    m.client.set = AsyncMock()
                    m.client.delete = AsyncMock()
                    m.get_order_draft = AsyncMock(return_value=None)
                    m.set_order_draft = AsyncMock()
                    m.get_user_context = AsyncMock(return_value=None)
                    m.set_user_context = AsyncMock()
                yield m1

@pytest.mark.asyncio
async def test_loyalty_dna_hydration() -> None:
    """Unit 1: Test that Neural DNA hydrates points and name correctly."""
    operative: SupportAgentOperative = SupportAgentOperative()
    mock_db: AsyncMock = AsyncMock()
    mock_db.scalar = AsyncMock(return_value="Lê Anh") # Mock User.name query
    
    # Mock Loyalty
    mock_loyalty: MagicMock = MagicMock()
    mock_loyalty.available_points = 1250
    mock_loyalty.balance_seal = "valid_seal"
    
    mock_result: MagicMock = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_loyalty
    
    mock_db.execute.side_effect = [
        mock_result, # select(UserLoyalty)
        MagicMock(scalar_one_or_none=lambda: MagicMock(value={"value":1000})), # select(SystemSetting)
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # select(Order) - history
    ]
    
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        
        dna: NeuralDNA = await operative._fetch_neural_dna(mock_db, "sid_123", user_id="user_abc")
        
        assert dna.available_points == 1250
        assert dna.customer_name == "Lê Anh"
        assert mock_verify.called is True

@pytest.mark.asyncio
async def test_military_security_tamper_detection() -> None:
    """Unit 2: Test that tampered loyalty data blocks Helen."""
    operative: SupportAgentOperative = SupportAgentOperative()
    mock_db: AsyncMock = AsyncMock()
    mock_db.scalar = AsyncMock(return_value="Any Name")
    
    # Mock LoyaltyService.verify_loyalty_integrity to return False (Tamper detected)
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = False
        
        dna: NeuralDNA = await operative._fetch_neural_dna(mock_db, "sid_123", user_id="hacker_123")
        
        # Balance should default to 0 for security
        assert dna.available_points == 0

@pytest.mark.asyncio
async def test_greeting_hook_with_points(base_ctx: SupportContext) -> None:
    """Unit 3: Test that greeting includes points hook."""
    handler: GreetingHandler = GreetingHandler()
    base_ctx.dna.available_points = 888
    base_ctx.dna.customer_name = "Sếp Tổng"
    base_ctx.dna.segment = "VIP"
    
    res: bool = await handler.handle(base_ctx)
    assert res is True # TERMINATE: Pure greeting consumed.
    assert any("Sếp Tổng" in r for r in base_ctx.replies)
    assert any("888 điểm" in r for r in base_ctx.replies)

@pytest.mark.asyncio
async def test_order_redemption_with_cap() -> None:
    """Unit 4: Test order creation with 1% points cap enforcement."""
    from backend.services.commerce.order import OrderService
    service: OrderService = OrderService()
    mock_db: AsyncMock = AsyncMock()
    
    # Mock Loyalty & Setting lookups
    mock_loyalty: MagicMock = MagicMock()
    mock_loyalty.available_points = 100000 
    mock_loyalty.total_spent = 0
    mock_loyalty.user_id = "user_123"
    
    mock_setting: MagicMock = MagicMock()
    mock_setting.value = {"value": 1000} # 1pt = 1000đ
    
    def mock_execute(stmt) -> MagicMock:
        stmt_str = str(stmt).lower()
        if "user_loyalty" in stmt_str or "userloyalty" in stmt_str:
            return MagicMock(scalar_one_or_none=lambda: mock_loyalty)
        elif "system_setting" in stmt_str or "systemsetting" in stmt_str or "loyalty_point_value_vnd" in stmt_str:
            return MagicMock(scalar_one_or_none=lambda: mock_setting)
        elif "product_variant" in stmt_str or "productvariant" in stmt_str:
            mock_var = MagicMock()
            mock_var.id = "prod_1"
            mock_var.stock = 10
            return MagicMock(all=lambda: [(mock_var.id, mock_var.stock)])
        else:
            return MagicMock(scalar_one_or_none=lambda: None, scalars=lambda: MagicMock(all=lambda: []))
            
    mock_db.execute.side_effect = mock_execute
    
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        
        data: OrderCreateRequest = OrderCreateRequest(
            customer_name="Test User",
            customer_email="test@osmo",
            customer_phone="0912345678",
            total_amount=1000000, 
            items=[{"product_id": "prod_1", "name": "Item 1", "unit_price": 1000000.0, "qty": 1}],
            points_to_redeem=5000 
        )
        
        # Patching internal models and utils
        with patch("backend.services.commerce.loyalty.LoyaltyService._create_balance_seal", return_value="new_seal"):
            with patch("backend.services.commerce.loyalty.LoyaltyService._create_transaction_token", return_value="token"):
                with patch("backend.services.commerce.order.event_bus.emit", new_callable=AsyncMock):
                    with patch("backend.services.commerce.order.Order") as mock_order_model:
                        with patch("backend.services.commerce.order.new_id", return_value="test-id"):
                             await service.create_order(mock_db, data, ip="127.0.0.1", ua="Test", user_id="user_123")
                             
                             # 1% of 1,000,000 is 10,000đ
                             # 10,000đ = 1 pt (since POINT_VALUE = 10000)
                             call_args: Dict[str, object] = mock_order_model.call_args[1]
                             assert call_args["points_redeemed"] == 1
                             assert call_args["point_discount_amount"] == 10000.0
                             assert call_args["total_amount"] == 990000.0

@pytest.mark.asyncio
async def test_fast_path_personalized_greeting() -> None:
    """Unit 5: Test that the Fast-Path classification personalizes the quick_reply."""
    operative: SupportAgentOperative = SupportAgentOperative()
    mock_db: AsyncMock = AsyncMock()
    # Mock User.name query
    mock_db.scalar = AsyncMock(return_value="Lê Anh")
    
    # Mock Loyalty and other DB calls for DNA
    mock_loyalty: MagicMock = MagicMock(available_points=125, balance_seal="seal")
    mock_res: MagicMock = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_loyalty
    
    # Fetch DNA internal calls: Loyalty Integrity, User Loyalty, System Setting, Order History
    mock_db.execute.side_effect = [
        mock_res, # Loyalty Integrity check
        mock_res, # User Loyalty fetch
        MagicMock(scalar_one_or_none=lambda: MagicMock(value={"value":1000})), # System Setting
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # Order History
    ]
    
    from backend.services.commerce.operatives.utils import FastIntentResponse
    mock_fast_res: FastIntentResponse = FastIntentResponse(intent="GREETING", quick_reply="Chào sếp Lê Anh, Helen có thể giúp gì cho sếp ạ?")
    
    with patch("backend.services.commerce.loyalty.LoyaltyService.verify_loyalty_integrity", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        with patch("backend.services.ai_engine.core.trinity_bridge.trinity_bridge.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_fast_res
            
            req: SupportRequest = SupportRequest(message="Helen ơi chào bạn", session_id="sid_123", user_id="user_abc")
            res: SupportResponse = await operative.chat(req, db=mock_db)
            
            assert "Lê Anh" in res.reply
            assert res.status == "DONE"
            # Verify that trinity_bridge was called with the correct deps
            args, kwargs = mock_run.call_args
            assert kwargs["deps"].customer_name == "Lê Anh"


@pytest.mark.asyncio
async def test_order_fallback_during_api_timeout() -> None:
    """Unit 6: Test that API timeout during checkout/order triggers the correct fallback asking for SĐT/Địa chỉ."""
    from backend.services.commerce.operatives.handlers.consultant_helpers import _generate_db_fallback
    from backend.schemas.support import SupportRequest
    from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
    
    from sqlalchemy.ext.asyncio import AsyncSession
    mock_db: AsyncMock = AsyncMock(spec=AsyncSession)
    ctx = SupportContext(
        db=mock_db,
        request=SupportRequest(
            message="tính tiền",
            session_id="sid_checkout_timeout",
            cart_items=[{"product_id": "prod_1", "quantity": 2, "price": 100000}]
        ),
        session_id="sid_checkout_timeout",
        dna=NeuralDNA(segment="NEW", available_points=0, point_value_vnd=1000)
    )
    
    reply = _generate_db_fallback(ctx)
    
    assert "[z2]" in reply
    assert "Số điện thoại" in reply
    assert "Địa chỉ cụ thể" in reply
    assert "Beppin Body" not in reply

