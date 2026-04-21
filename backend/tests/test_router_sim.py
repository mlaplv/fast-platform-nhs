import sys
import os
import asyncio
from unittest.mock import MagicMock

# Allow imports
sys.path.insert(0, os.path.abspath('.'))

from backend.services.commerce.operatives.handlers.base import SupportContext
from backend.services.commerce.operatives.handlers.order import OrderHandler

class MockRequest:
    message = "cho 1 miccosmo white label premium placenta wash 110g"
    product_slug = "miccosmo-wash"

async def test_order_handler():
    ctx = SupportContext(
        db=MagicMock(),
        request=MockRequest(),
        session_id="test_sim",
        dna=MagicMock(),
        product_ctx="",
        history_text="",
        knowledge_index="",
        p_info=MagicMock()
    )
    ctx.p_info.price = 100000
    
    # Mock lead_extractor
    from backend.services.commerce.logic.lead_extractor import lead_extractor, ExtractedLead, LeadOrderItem
    async def mock_extract(*args, **kwargs):
        print("💡 [Simulation] extract_and_convert called")
        return ExtractedLead(
            customer_phone=None,
            customer_address=None,
            is_definite_purchase=True,
            items=[LeadOrderItem(name="Miccosmo Wash", quantity=1, price=100000, id="miccosmo-wash")]
        )
    lead_extractor.extract_and_convert = mock_extract

    # Run
    handler = OrderHandler()
    result = await handler.handle(ctx)
    print(f"✅ Handler Result: {result}")
    print(f"✅ Replies: {ctx.replies}")

asyncio.run(test_order_handler())
