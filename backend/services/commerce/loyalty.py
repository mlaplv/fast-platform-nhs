import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, UserLoyalty, PointTransaction
from backend.database.models.system import SystemSetting
import math

logger = logging.getLogger("api-gateway")

class LoyaltyService:
    @staticmethod
    async def earn_order_points(db_session: AsyncSession, order_id: str) -> bool:
        """Triggered when an order is completed to add points to the user."""
        order_stmt = select(Order).where(Order.id == order_id)
        order_res = await db_session.execute(order_stmt)
        order = order_res.scalar_one_or_none()

        if not order or not order.user_id:
            return False

        # Only process delivered orders and ensure points were not already given
        if order.status != "DELIVERED":
            return False

        if order.points_earned > 0: # already earned
            return False

        # Formula: 100k -> 1 point
        points_to_earn = math.floor(order.total_amount / 100000)
        
        if points_to_earn <= 0:
            return False

        # Get or create UserLoyalty
        loyalty_stmt = select(UserLoyalty).where(UserLoyalty.user_id == order.user_id)
        l_res = await db_session.execute(loyalty_stmt)
        loyalty = l_res.scalar_one_or_none()

        if not loyalty:
            loyalty = UserLoyalty(user_id=order.user_id, available_points=0, total_spent=0.0)
            db_session.add(loyalty)

        # Update points and spent amount
        loyalty.available_points += points_to_earn
        loyalty.total_spent += order.total_amount
        
        # Check Tiers: STANDARD, SILVER, GOLD, PLATINUM (R2026)
        new_tier = "STANDARD"
        if loyalty.total_spent > 20_000_000:
            new_tier = "PLATINUM"
        elif loyalty.total_spent == 20_000_000:
            new_tier = "GOLD"
        elif loyalty.total_spent >= 10_000_000:
            new_tier = "SILVER"

        if loyalty.tier != new_tier:
            loyalty.tier = new_tier
            logger.info(f"[LOYALTY] User {order.user_id} upgraded to {new_tier}")
        
        # Add ledger history
        pt = PointTransaction(
            user_id=order.user_id,
            order_id=order.id,
            amount=points_to_earn,
            transaction_type="EARN_ORDER",
            notes=f"Tích điểm từ đơn hàng {order.id}: {order.total_amount}đ"
        )
        db_session.add(pt)

        # Update order logic
        order.points_earned = points_to_earn
        
        return True
