import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, UserLoyalty, PointTransaction
from backend.database.models.system import SystemSetting
from backend.utils.security import GeminiSecurity
import math
import json

logger = logging.getLogger("api-gateway")

class LoyaltyService:
    @staticmethod
    def _create_balance_seal(loyalty: UserLoyalty) -> str:
        """Military-Grade Seal for user balance based on current state."""
        payload = {
            "u": loyalty.user_id,
            "p": loyalty.available_points,
            "pp": loyalty.pending_points, # R2026: Seal pending points to prevent manipulation
            "s": float(loyalty.total_spent)
        }
        return GeminiSecurity.encrypt(payload)

    @staticmethod
    def _create_transaction_token(pt: PointTransaction) -> str:
        """Immutable seal for a specific transaction."""
        payload = {
            "u": pt.user_id,
            "a": pt.amount,
            "t": pt.transaction_type,
            "o": pt.order_id
        }
        return GeminiSecurity.encrypt(payload)

    @staticmethod
    async def verify_loyalty_integrity(db_session: AsyncSession, user_id: str) -> bool:
        """
        R00-Protocol: Verify the AES-GCM seal against the raw database values.
        Returns False if tampering is detected.
        """
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
        res = await db_session.execute(stmt)
        loyalty = res.scalar_one_or_none()
        
        if not loyalty:
            return True # New user, no data to tamper with
            
        if not loyalty.balance_seal:
            # R2026: Auto-upgrade legacy data to secure seal on first access
            logger.warning(f"[SECURITY] Legacy Loyalty data detected for user {user_id}. Sealing now.")
            loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)
            await db_session.commit()
            return True

        seal_data = GeminiSecurity.decrypt(loyalty.balance_seal)
        if not seal_data or not isinstance(seal_data, dict):
            logger.error(f"[SECURITY-CRITICAL] Loyalty Seal Corrupted for user {user_id}!")
            return False

        # Detect manual DB intervention
        pts_match = int(seal_data.get("p", 0)) == loyalty.available_points
        pending_match = int(seal_data.get("pp", 0)) == loyalty.pending_points
        spent_match = abs(float(seal_data.get("s", 0)) - loyalty.total_spent) < 0.01
        
        if not pts_match or not pending_match or not spent_match:
            logger.error(f"[SECURITY-ALERT] Tamper Detected for user {user_id}! DB: {loyalty.available_points} pts (pp:{loyalty.pending_points}), Seal: {seal_data.get('p')} pts (pp:{seal_data.get('pp')}).")
            return False
            
        return True

    @staticmethod
    async def register_pending_points(db_session: AsyncSession, user_id: str, amount: int) -> bool:
        """Called during checkout to show points 'waiting' to the user."""
        if amount <= 0: return False
        
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
        res = await db_session.execute(stmt)
        loyalty = res.scalar_one_or_none()
        
        if not loyalty:
            loyalty = UserLoyalty(user_id=user_id, available_points=0, pending_points=0, total_spent=0.0)
            db_session.add(loyalty)
            
        # Add to pending
        loyalty.pending_points += amount
        
        # Reseal
        loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)
        return True

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
        # R2026: Convert from pending to available if applicable
        if loyalty.pending_points >= points_to_earn:
            loyalty.pending_points -= points_to_earn
            
        loyalty.available_points += points_to_earn
        loyalty.total_spent += order.total_amount
        
        # Check Tiers: STANDARD, SILVER, GOLD, PLATINUM (R2026)
        new_tier = "STANDARD"
        if loyalty.total_spent > 20_000_000:
            new_tier = "PLATINUM"
        elif loyalty.total_spent >= 20_000_000:
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
        pt.integrity_token = LoyaltyService._create_transaction_token(pt)
        db_session.add(pt)

        # Seal the final balance
        loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)

        # Update order logic
        order.points_earned = points_to_earn
        
        return True
