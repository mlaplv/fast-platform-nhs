import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("api-gateway")
logger.setLevel(logging.INFO)

from backend.services.commerce.logic.location_resolver import location_resolver
from backend.services.commerce.logic.lead_extractor import lead_extractor
from backend.schemas.order import OrderDraft
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest
from backend.services.commerce.operatives.handlers.order import OrderHandler
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

class MockSession(AsyncMock, AsyncSession):
    pass

async def test_fix():
    print("🚀 Testing Helen AI Memory Fix...")
    
    # 1. Setup Mock DB and Context
    db = MockSession()
    session_id = "test-session-123"
    
    # Active Draft with Items but missing Phone/Address
    draft = OrderDraft(
        session_id=session_id,
        items=[{"product_id": "beppin-body-virgin-white-serum", "name": "Serum Beppin Body", "price": 290000, "quantity": 1}]
    )
    
    request = SupportRequest(
        message="0949901122, 336/28/19 Nguyễn Văn Luông, Phú Lâm",
        session_id=session_id
    )
    
    ctx = SupportContext(
        db=db,
        request=request,
        session_id=session_id,
        dna=NeuralDNA(),
        order_draft=draft,
        replies=[]
    )
    
    handler = OrderHandler()
    
    # 2. Run Handler
    print(f"Message: {request.message}")
    result = await handler.handle(ctx)
    
    print(f"Handler Result (Handled?): {result}")
    print(f"Final Replies: {ctx.replies}")
    
    # 3. Verify Draft State
    print(f"Updated Phone: {ctx.order_draft.customer_phone}")
    print(f"Updated Address: {ctx.order_draft.customer_address}")
    
    if "Phú Lâm" in str(ctx.replies) and "Tỉnh/Thành phố" in str(ctx.replies):
        print("✅ SUCCESS: Correctly identified ambiguity and asked for Province.")
    elif ctx.order_draft.customer_phone == "0949901122" and ctx.order_draft.customer_address:
        print("✅ SUCCESS: Slots filled.")
    else:
        print("❌ FAILED: Slots not filled correctly or wrong reply.")

if __name__ == "__main__":
    asyncio.run(test_fix())
