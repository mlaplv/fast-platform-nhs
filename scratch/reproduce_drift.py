
import asyncio
import uuid
import logging
import sys
import os
from datetime import datetime, timedelta, timezone

# Ensure backend is in path
sys.path.append("/app")

from backend.services.commerce.operatives.support_agent import support_agent, SupportContext
from backend.schemas.support import SupportRequest, SupportPricingContext
from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.database.models.promotion import ComboDeal

# Disable logging noise
logging.getLogger("api-gateway").setLevel(logging.ERROR)

async def test():
    await trinity_bridge.initialize()
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # 1. CLEANUP & INSERT MOCK COMBO
        from sqlalchemy import delete
        await db.execute(delete(ComboDeal).where(ComboDeal.id == "test-serum-bundle"))
        
        bundle = ComboDeal(
            id="test-serum-bundle",
            name="Combo 3 Serum",
            type="BUNDLE_PRICE",
            condition_payload={"product_ids": ["p3"], "qty": 3},
            reward_payload={"price": 1590000.0},
            is_active=True,
            tenant_id="default",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(bundle)
        await db.flush()

        # 2. Mocking the request WITHOUT pricing_context
        req = SupportRequest(
            message="tính tiền giùm tôi",
            session_id=str(uuid.uuid4()),
            cart_items=[
                {"product": {"id": "p1", "name": "Kem cổ", "price": 650000}, "quantity": 1},
                {"product": {"id": "p2", "name": "Kem mắt", "price": 600000}, "quantity": 1},
                {"product": {"id": "p3", "name": "Serum", "price": 600000}, "quantity": 3},
            ],
            pricing_context=None # FALLBACK TEST
        )
        
        print(f"🚀 [TEST] Message: '{req.message}' | Cart Items: {len(req.cart_items)} | CONTEXT: FALLBACK")
        
        # Test: Full Deep-Brain Logic
        print("🚀 [TEST] Running process_brain_logic...")
        res = await support_agent.process_brain_logic(req, db)
        
        print(f"\n✅ [HELEN REPLY]:\n{res.reply}")
        
        # Cleanup
        await db.execute(delete(ComboDeal).where(ComboDeal.id == "test-serum-bundle"))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(test())
