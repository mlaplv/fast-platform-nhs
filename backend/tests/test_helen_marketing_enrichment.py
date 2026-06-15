import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest, SupportIntent, SupportProductInfo, SupportResponse
from backend.services.commerce.operatives.handlers.consultant_helpers import build_marketing_benefits_block
from backend.services.commerce.operatives.context_helper import _try_db_first_fast_path
from backend.services.commerce.operatives.support_agent import SupportAgentOperative

@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def base_ctx(mock_db: AsyncMock) -> SupportContext:
    req = SupportRequest(
        message="init",
        session_id="test-marketing-session",
        product_slug="test-product"
    )
    return SupportContext(
        db=mock_db,
        request=req,
        session_id="test-marketing-session",
        dna=NeuralDNA(segment="NEW", available_points=5),
        p_info=SupportProductInfo(
            id="prod-123",
            name="Test Premium Cream",
            price=500000.0,
            price_display="500.000đ",
            slug="test-product"
        )
    )

@pytest.mark.asyncio
async def test_build_marketing_benefits_block_full(mock_db: AsyncMock) -> None:
    # 1. Mock Combo Deals query
    mock_combo = MagicMock()
    mock_combo.name = "Mua 2 Tặng 1 Cream"
    mock_combo.condition_payload = {"product_ids": ["prod-123"], "buy_qty": 2}
    mock_combo.reward_payload = {"get_qty": 1}
    
    mock_combo_res = MagicMock()
    mock_combo_res.scalars.return_value.all.return_value = [mock_combo]
    
    # 2. Mock Vouchers query
    mock_voucher_1 = MagicMock()
    mock_voucher_1.id = "VOUCHER1"
    mock_voucher_1.discount_value = 50000.0
    mock_voucher_1.min_spend = 400000.0
    mock_voucher_1.priority = 10
    
    mock_voucher_2 = MagicMock()
    mock_voucher_2.id = "VOUCHER2"
    mock_voucher_2.discount_value = 20000.0
    mock_voucher_2.min_spend = 0.0
    mock_voucher_2.priority = 5

    mock_vouchers_res = MagicMock()
    mock_vouchers_res.scalars.return_value.all.return_value = [mock_voucher_1, mock_voucher_2]

    # Assign DB execution side effects
    mock_db.execute.side_effect = [mock_combo_res, mock_vouchers_res]

    p_info = SupportProductInfo(
        id="prod-123",
        name="Test Premium Cream",
        price=500000.0,
        price_display="500.000đ",
        slug="test-product"
    )
    dna = NeuralDNA(segment="VIP", available_points=12)

    # 3. Mock LoyaltyService Check-in configuration
    mock_checkin_config = {
        "checkin_bonus": 1.0,
        "streak_bonus_day_7": 5.0
    }
    
    with patch("backend.services.commerce.loyalty.LoyaltyService._get_checkin_config", return_value=mock_checkin_config):
        block = await build_marketing_benefits_block(mock_db, p_info, dna)
        
        print("Generated Marketing Block:\n", block)
        
        # Verify Combo is present
        assert "🎁 **ƯU ĐÃI ĐỘC QUYỀN ĐANG ÁP DỤNG:**" in block
        assert "Mua 2 tặng 1" in block
        
        # Verify Voucher best fit is chosen (VOUCHER1 is 50k off, fits min_spend 400k)
        assert "Voucher áp dụng" in block
        assert "VOUCHER1" in block
        
        # Verify Loyalty Points
        # earned_points = 500000 // 10000 = 50 pts
        assert "Tích lũy & Loyalty" in block or "Tích điểm Osmo" in block
        assert "50 điểm" in block
        assert "12 điểm" in block
        
        # Verify Check-in info
        assert "Điểm danh nhận quà" in block

@pytest.mark.asyncio
async def test_fast_path_consultation_marketing_injection(mock_db: AsyncMock) -> None:
    # Setup mock metadata result for ProductBase
    mock_meta_res = MagicMock()
    mock_meta_res.scalar_one_or_none.return_value = {
        "benefits": ["Mờ thâm sạm và sáng da chuyên sâu", "Cấp ẩm căng bóng tự nhiên"]
    }
    mock_db.execute.return_value = mock_meta_res

    req = SupportRequest(
        message="[system_consult] cho em hỏi về sản phẩm",
        session_id="test-consult-session",
        product_slug="test-product"
    )
    
    p_info = SupportProductInfo(
        id="prod-123",
        name="Test Premium Cream",
        price=500000.0,
        price_display="500.000đ",
        slug="test-product"
    )
    
    dna = NeuralDNA(segment="VIP", available_points=5)

    # Mock build_marketing_benefits_block to return a static block
    mock_marketing_block = "=== MOCK MARKETING BLOCK ==="
    with patch("backend.services.commerce.operatives.handlers.consultant_helpers.build_marketing_benefits_block", return_value=mock_marketing_block):
        res = await _try_db_first_fast_path(
            db=mock_db,
            request=req,
            p_info=p_info,
            c_name="Khách hàng",
            cur_settings={"currency_symbol": "đ", "currency_format": "{value}đ"},
            ctx_text="",
            dna=dna
        )
        
        assert res is not None
        assert res.ok is True
        # Verify the marketing block is injected in the reply
        assert "=== MOCK MARKETING BLOCK ===" in res.reply
        assert "Test Premium Cream" in res.reply

@pytest.mark.asyncio
async def test_support_agent_product_mismatch_draft_clearing() -> None:
    # Mock database session
    db_mock = AsyncMock(spec=AsyncSession)
    
    # Mock product query to return the current product info
    mock_prod = MagicMock()
    mock_prod.id = "prod-abc"
    mock_prod.slug = "current-cream"
    mock_prod_res = MagicMock()
    mock_prod_res.first.return_value = mock_prod
    db_mock.execute.return_value = mock_prod_res

    # Mock xohi_memory calls
    mock_draft = {
        "session_id": "test-mismatch-session",
        "items": [{"product_id": "prod-xyz", "quantity": 1}],
        "is_complete": False
    }
    
    agent = SupportAgentOperative()
    
    # Message is browsing/consultation, not a cart checkout keyword
    req = SupportRequest(
        message="Tư vấn giúp mình nhé",
        session_id="test-mismatch-session",
        product_slug="current-cream"
    )
    
    with patch("backend.services.xohi_memory.xohi_memory.get_order_draft", return_value=mock_draft) as mock_get_draft, \
         patch("backend.services.xohi_memory.xohi_memory.clear_order_draft") as mock_clear_draft, \
         patch("backend.services.commerce.operatives.support_agent._get_currency_settings", return_value={}), \
         patch("backend.services.commerce.operatives.support_agent._fetch_chat_context", side_effect=ValueError("Exit Early")):
        
        try:
            await agent.process_brain_logic(req, db_mock)
        except ValueError as e:
            if str(e) != "Exit Early":
                raise
            
        # Since product_slug current-cream (ID: prod-abc) does not match draft's product_id (prod-xyz)
        # and it's not a cart checkout, clear_order_draft MUST be called!
        mock_clear_draft.assert_called_once_with("test-mismatch-session")
