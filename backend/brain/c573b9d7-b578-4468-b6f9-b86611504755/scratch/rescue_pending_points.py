import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import Order, UserLoyalty
from backend.services.commerce.loyalty import LoyaltyService
import math

async def rescue():
    async with async_session_maker() as session:
        # 1. Tìm các đơn hàng chưa thành công (để tính điểm chờ)
        stmt = select(Order).where(Order.status.in_(["PENDING", "PROCESSING", "SHIPPING"]))
        res = await session.execute(stmt)
        orders = res.scalars().all()
        
        print(f"[*] Found {len(orders)} pending orders to process.")
        
        for order in orders:
            if not order.user_id: continue
            
            pts_to_earn = math.floor(order.total_amount / 100000)
            if pts_to_earn <= 0: continue
            
            print(f"[*] Processing Order {order.id} for User {order.user_id} -> +{pts_to_earn} PTS pending.")
            
            # Update pending points via LoyaltyService (to ensure sealing)
            await LoyaltyService.register_pending_points(session, order.user_id, pts_to_earn)
            
        await session.commit()
        print("[✓] Rescue complete. Pending points synchronized.")

if __name__ == "__main__":
    asyncio.run(rescue())
