import asyncio
import sys
import uuid
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import Order
from backend.database.models.affiliate import AffiliateProfile, CommissionLedger
from backend.services.commerce.checkout import CheckoutService
from backend.services.ctv_service import ctv_service
from backend.schemas.client.checkout import StealthCheckoutSchema, CheckoutItemSchema

async def main():
    async with async_session_maker() as session:
        # 1. Let's find affiliate profile for MLAP
        stmt = select(AffiliateProfile).where(AffiliateProfile.ctv_code == 'MLAP')
        aff = (await session.execute(stmt)).scalar_one_or_none()
        if not aff:
            print("Affiliate profile MLAP not found!")
            return
        
        print(f"MLAP Affiliate stats BEFORE test:")
        print(f"  Revenue: {aff.total_revenue:,.0f}đ")
        print(f"  Commission: {aff.total_commission:,.0f}đ")
        print(f"  Orders count: {aff.total_orders}")
        
        # 2. Build mockup stealth checkout payload
        payload = StealthCheckoutSchema(
            items=[
                CheckoutItemSchema(
                    product_id="27ae52bd-5ae2-44b8-b30c-ece1fe926a18",
                    variant_id="v_1588afc185a3",
                    quantity=5,
                    price=100000.0
                )
            ],
            customer_name="Lê Anh Test",
            customer_phone="0949901122",
            customer_address="123 Duong, Phuong, Tỉnh",
            total_amount=500000.0,
            shipping_fee=0.0,
            payment_method="cod"
        )
        
        # 3. Create stealth order
        print("\nCreating stealth order with CTV token...")
        res = await CheckoutService.create_stealth_order(
            db_session=session,
            payload=payload,
            customer_ip="127.0.0.1",
            user_agent="Test UA",
            user_id=None,
            ctv_code="KsLxXzZ5JRPXKOnCJaVSJa4kg_XNFd5j1B9caffYL5E0XQ==",
            attribution_source="cookie"
        )
        
        order_id = res.get("id")
        print(f"Order created! ID: {order_id}, ok: {res.get('ok')}")
        
        # Fetch order from DB
        order = (await session.execute(select(Order).where(Order.id == order_id))).scalar_one()
        print(f"Attributed Order CTV Code in DB: {order.ctv_code}")
        print(f"Attributed Order CTV Affiliate ID in DB: {order.ctv_affiliate_id}")
        
        # 4. Confirm the order to trigger commission credit
        print("\nConfirming order...")
        order.status = "CONFIRMED"
        session.add(order)
        await session.commit()
        
        # 5. Credit commission
        print("Crediting commission...")
        credited = await ctv_service.credit_commission(session, order_id)
        print(f"Commission credit returned: {credited}")
        
        # Reload affiliate stats
        await session.refresh(aff)
        print(f"\nMLAP Affiliate stats AFTER test:")
        print(f"  Revenue: {aff.total_revenue:,.0f}đ")
        print(f"  Commission: {aff.total_commission:,.0f}đ")
        print(f"  Orders count: {aff.total_orders}")
        
        # Fetch pending ledger
        ledger_stmt = select(CommissionLedger).where(CommissionLedger.order_id == order_id)
        ledger = (await session.execute(ledger_stmt)).scalar_one_or_none()
        if ledger:
            print(f"  Ledger entry: ID {ledger.id} | Amount {ledger.commission_amount:,.0f}đ | Status {ledger.status}")
            
            # For testing, let's confirm the ledger entry to move it to available balance
            print("\nConfirming ledger entry to add to available balance...")
            await ctv_service.confirm_pending_commissions(session, order_id)
            await session.refresh(aff)
            print(f"MLAP Affiliate stats AFTER confirmation:")
            print(f"  Revenue: {aff.total_revenue:,.0f}đ")
            print(f"  Commission: {aff.total_commission:,.0f}đ")
            print(f"  Orders count: {aff.total_orders}")

if __name__ == "__main__":
    asyncio.run(main())
