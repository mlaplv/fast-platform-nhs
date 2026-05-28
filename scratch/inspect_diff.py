import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import Order
from backend.database.models.affiliate import AffiliateProfile, CommissionLedger

async def inspect():
    async with async_session_maker() as db_session:
        # Check profiles
        print("--- CTV Profiles ---")
        aff_res = await db_session.execute(select(AffiliateProfile))
        for p in aff_res.scalars().all():
            print(f"ID: {p.id}, Code: {p.ctv_code}, User: {p.user_id}, Total Rev: {p.total_revenue}, Total Comm: {p.total_commission}")

        # Check latest orders
        print("\n--- Orders ---")
        ord_res = await db_session.execute(select(Order).order_by(Order.created_at.desc()).limit(10))
        for o in ord_res.scalars().all():
            print(f"ID: {o.id}, Code: {o.ctv_code}, Total: {o.total_amount}, Status: {o.status}, User ID: {o.user_id}")

        # Check commission ledgers
        print("\n--- Commission Ledgers ---")
        ledg_res = await db_session.execute(select(CommissionLedger))
        for l in ledg_res.scalars().all():
            print(f"Order ID: {l.order_id}, Aff ID: {l.affiliate_id}, Order Amt: {l.order_amount}, Comm Amt: {l.commission_amount}, Status: {l.status}")

if __name__ == "__main__":
    asyncio.run(inspect())
