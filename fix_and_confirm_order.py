import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import Order
from backend.database.models.affiliate import AffiliateProfile
from backend.services.ctv_service import ctv_service

async def main():
    async with async_session_maker() as session:
        # Load order
        order_id = "538a9608-f70d-4454-ae96-1829699888ef"
        order = (await session.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
        if not order:
            print("Order not found!")
            return
            
        # Load MLAP affiliate profile
        aff = (await session.execute(select(AffiliateProfile).where(AffiliateProfile.ctv_code == 'MLAP'))).scalar_one()
        
        # Update order attribution
        order.ctv_code = "MLAP"
        order.ctv_affiliate_id = aff.id
        order.attribution_source = "cookie"
        order.status = "CONFIRMED"
        session.add(order)
        await session.commit()
        print(f"Updated order {order_id} to MLAP and CONFIRMED.")
        
        # Credit commission
        credited = await ctv_service.credit_commission(session, order_id)
        print(f"Commission credited: {credited}")
        
        # Confirm commission immediately for demo/validation purposes
        await ctv_service.confirm_pending_commissions(session, order_id)
        print("Commission confirmed immediately.")
        
        # Refresh affiliate to display stats
        await session.refresh(aff)
        print(f"\nMLAP Affiliate Stats:")
        print(f"  Revenue: {aff.total_revenue:,.0f}đ")
        print(f"  Commission: {aff.total_commission:,.0f}đ")
        print(f"  Orders count: {aff.total_orders}")

if __name__ == "__main__":
    asyncio.run(main())
