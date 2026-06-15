import sys
import os
import asyncio
import logging
from typing import List, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# --- BOOTSTRAP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- MOCKING ---
mock_db: MagicMock = MagicMock(spec=AsyncSession)
mock_db.execute = AsyncMock(return_value=MagicMock())
mock_db.flush = AsyncMock()
mock_db.commit = AsyncMock()
mock_db.rollback = MagicMock()

# --- IMPORT TARGETS ---
from backend.services.commerce.logic.lead_extractor import LeadExtractor, ExtractedLead, LeadOrderItem
from backend.services.commerce.operatives.support_agent import SupportAgentOperative
from backend.services.commerce.operatives.handlers.base import NeuralDNA, SupportContext
from backend.schemas.support import SupportRequest, SupportResponse
from backend.schemas.order import OrderDraft
from backend.database.models.commerce import ProductBase

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger("test-ssot")

async def run_ssot_tests() -> None:
    print("\n" + "="*60)
    print("🚀 HELEN SSOT & BIDIRECTIONAL SYNC - UNIT TESTS")
    print("="*60 + "\n")

    session_id: str = "test_ssot_session_999"

    # --- Scenario 1: Incremental Merge - Hydration from Redis when NO Web Cart exists ---
    print("📝 [Scenario 1] Hydration from Redis (no Web Cart)")
    lead: ExtractedLead = ExtractedLead(
        customer_phone="0949901122",
        customer_address=None,
        items=[] # Empty in current turn
    )
    
    # Mock Redis draft
    mock_draft: OrderDraft = OrderDraft(
        session_id=session_id,
        customer_phone="0949901122",
        items=[{"product_id": "sp1", "name": "Miccosmo Serum", "quantity": 3, "price": 450000}]
    )

    with patch('backend.services.xohi_memory.xohi_memory.get_order_draft', AsyncMock(return_value=mock_draft.model_dump(mode='json'))):
        hydrated_lead: ExtractedLead = await LeadExtractor._hydrate_from_redis(
            session_id=session_id,
            lead=lead,
            message="Số điện thoại của chị nhé",
            has_web_cart=False
        )
        print(f"   -> Hydrated items count: {len(hydrated_lead.items)}")
        assert len(hydrated_lead.items) == 1
        assert hydrated_lead.items[0].quantity == 3
        assert hydrated_lead.items[0].id == "sp1"
        print("   ✅ Scenario 1 Success: Restored items from Redis correctly.\n")

    # --- Scenario 2: Incremental Merge - Hydration from Redis when Web Cart DOES exist ---
    print("📝 [Scenario 2] Bypass Hydration from Redis (Web Cart active)")
    lead2: ExtractedLead = ExtractedLead(
        customer_phone="0949901122",
        customer_address=None,
        items=[]
    )
    with patch('backend.services.xohi_memory.xohi_memory.get_order_draft', AsyncMock(return_value=mock_draft.model_dump(mode='json'))):
        hydrated_lead2: ExtractedLead = await LeadExtractor._hydrate_from_redis(
            session_id=session_id,
            lead=lead2,
            message="Chị vừa sửa giỏ hàng trên web",
            has_web_cart=True
        )
        print(f"   -> Hydrated items count: {len(hydrated_lead2.items)}")
        assert len(hydrated_lead2.items) == 0
        print("   ✅ Scenario 2 Success: Bypassed Redis items hydration to trust Web Cart.\n")

    # --- Scenario 3: Bidirectional Sync Response Generation in SupportAgentOperative ---
    print("📝 [Scenario 3] Bidirectional Sync Response Generation")
    
    agent: SupportAgentOperative = SupportAgentOperative()
    request: SupportRequest = SupportRequest(
        message="cho mình một chai nữa",
        session_id=session_id,
        cart_items=[
            {
                "product": {"id": "sp1", "name": "Miccosmo Serum", "price": 450000, "discountPrice": 450000, "slug": "miccosmo-serum"},
                "quantity": 1,
                "selected": True
            }
        ],
        cart_epoch=5
    )

    # Mock DB return values
    mock_product: ProductBase = ProductBase(id="sp1", name="Miccosmo Serum", price=450000, discount_price=450000, slug="miccosmo-serum")
    
    # We patch context building and routing to mock draft change
    async def mock_process(ctx: SupportContext) -> SupportContext:
        # Update draft to quantity 2 (e.g. backend extraction processed "one more")
        ctx.order_draft = OrderDraft(
            session_id=session_id,
            items=[{"product_id": "sp1", "name": "Miccosmo Serum", "quantity": 2, "price": 450000}]
        )
        ctx.replies.append("Dạ Helen đã thêm 1 chai nữa vào giỏ hàng cho mình rồi ạ! 🌸")
        return ctx

    # Mock the router process call
    with patch.object(agent.router, 'process', side_effect=mock_process):
        with patch('backend.services.commerce.operatives.support_agent._fetch_chat_context', AsyncMock(return_value="")):
            with patch('backend.services.commerce.operatives.support_agent._fetch_neural_dna', AsyncMock(return_value=NeuralDNA())):
                with patch('backend.services.commerce.operatives.support_agent._fetch_product_context', AsyncMock(return_value=("", None))):
                    with patch('backend.services.commerce.operatives.support_agent._prepare_pricing_breakdown', AsyncMock(return_value=MagicMock())):
                        with patch('backend.services.xohi_memory.xohi_memory.get_order_draft', AsyncMock(return_value=None)):
                            with patch('backend.services.commerce.operatives.support_agent.SupportAgentOperative._save_history', AsyncMock()):
                                with patch('backend.services.commerce.operatives.support_agent.SupportAgentOperative._emit_inbox_update', AsyncMock()):
                                    # Patch the DB execution dynamically based on target table string
                                    async def mock_execute(stmt: object, *args: object, **kwargs: object) -> MagicMock:
                                        stmt_str: str = str(stmt)
                                        res: MagicMock = MagicMock()
                                        if "product_bases" in stmt_str:
                                            res.scalars.return_value.all.return_value = [mock_product]
                                            res.scalar_one_or_none.return_value = mock_product
                                        elif "product_variants" in stmt_str:
                                            res.scalars.return_value.all.return_value = []
                                            res.scalar_one_or_none.return_value = None
                                        elif "vouchers" in stmt_str:
                                            res.scalars.return_value.all.return_value = []
                                            res.scalar_one_or_none.return_value = None
                                        else:
                                            res.scalars.return_value.all.return_value = []
                                            res.scalar_one_or_none.return_value = None
                                        return res
                                    
                                    mock_db.execute = mock_execute
                                    
                                    response: SupportResponse = await agent.process_brain_logic(request, mock_db)
                                    
                                    print(f"   -> Response reply: {response.reply}")
                                    print(f"   -> Response ui_metadata: {response.ui_metadata}")
                                    
                                    assert response.ui_metadata is not None
                                    assert "update_cart" in response.ui_metadata
                                    sync_payload: Dict[str, object] = response.ui_metadata["update_cart"]
                                    assert sync_payload["epoch"] == 6
                                    assert len(sync_payload["items"]) == 1
                                    assert sync_payload["items"][0]["quantity"] == 2
                                    print("   ✅ Scenario 3 Success: Bidirectional sync generated correct update payload & incremented epoch.\n")

    print("="*60)
    print("🎉 TẤT CẢ CÁC BÀI THỬ NGHIỆM ĐÃ VƯỢT QUA KIỂM TRA!")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_ssot_tests())
