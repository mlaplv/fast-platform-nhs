import asyncio
import os
import json
from unittest.mock import AsyncMock, MagicMock
from backend.services.commerce.logic.lead_extractor import lead_extractor
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest, SupportProductInfo

async def reproduce():
    print("🚀 [CTO AUDIT] Starting reproduction session...")
    
    # 1. Mock DB
    mock_db = AsyncMock()
    mock_db.execute.return_value = MagicMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = [] # Empty history
    
    # 2. Setup Context
    req = SupportRequest(
        message="cho 1 Beppin Body Virgin White Serum",
        session_id="cto_audit_session",
        product_slug="beppin-body-serum"
    )
    
    p_info = SupportProductInfo(
        id="beppin-001",
        name="Beppin Body Virgin White Serum",
        price=249000,
        price_display="249.000đ",
        slug="beppin-body-serum"
    )
    
    ctx = SupportContext.model_construct(
        db=mock_db,
        request=req,
        session_id="cto_audit_session",
        dna=NeuralDNA(segment="NEW"),
        p_info=p_info
    )
    
    # 3. Trigger Handler
    handler = OrderHandler()
    ctx.replies = [] # Ensure it's a list
    
    os.environ["HELEN_DEBUG"] = "1" # Force debug prefix [z3]
    
    print("\n--- TURN 1 EXECUTING ---")
    await handler.handle(ctx)
    
    if ctx.replies:
        print(f"\nHELEN REPLY: {ctx.replies[0]}")
        if "địa chỉ thì Helen đã thấy rồi" in ctx.replies[0]:
            print("\n❌ BUG CONFIRMED: Helen is hallucinating address!")
            if ctx.lead_data:
                print(f"DEBUG LEAD DATA: phone={ctx.lead_data.customer_phone}, address='{ctx.lead_data.customer_address}'")
        else:
            print("\n✅ LOGIC OK: Helen requested both info correctly (in this mock).")
    else:
        print("\n⚠️ NO REPLY: Handler did not trigger.")

if __name__ == "__main__":
    asyncio.run(reproduce())
