import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, UserLoyalty, PointTransaction
from backend.database.models.system import SystemSetting
from backend.constants.commerce import LoyaltyConfig
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
            "s": int(loyalty.total_spent)
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
            
            import os
            if os.getenv("ENV") != "production":
                logger.warning(f"[SECURITY-RESCUE] Re-sealing corrupted loyalty for user {user_id} in {os.getenv('ENV')} environment.")
                loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)
                await db_session.commit()
                return True
            return False

        # Detect manual DB intervention
        pts_match = int(seal_data.get("p", 0)) == loyalty.available_points
        pending_match = int(seal_data.get("pp", 0)) == loyalty.pending_points
        spent_match = int(seal_data.get("s", 0)) == loyalty.total_spent
        
        if not pts_match or not pending_match or not spent_match:
            logger.error(f"[SECURITY-ALERT] Tamper Detected for user {user_id}! DB: {loyalty.available_points} pts (pp:{loyalty.pending_points}), Seal: {seal_data.get('p')} pts (pp:{seal_data.get('pp')}).")
            return False
            
        return True

    @staticmethod
    async def register_pending_points(db_session: AsyncSession, user_id: str, amount: int) -> bool:
        """Called during checkout to show points 'waiting' to the user."""
        if amount <= 0: return False
        
        # SECURITY R00: Verify integrity before updating points balance
        is_intact = await LoyaltyService.verify_loyalty_integrity(db_session, user_id)
        if not is_intact:
            logger.error(f"[SECURITY-FATAL] Loyalty balance tampering detected for user {user_id} before registering pending points. Aborting transaction.")
            return False

        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id).with_for_update()
        res = await db_session.execute(stmt)
        loyalty = res.scalar_one_or_none()
        
        if not loyalty:
            loyalty = UserLoyalty(user_id=user_id, available_points=0, pending_points=0, total_spent=0)
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

        # SECURITY R00: Verify integrity before updating points balance
        is_intact = await LoyaltyService.verify_loyalty_integrity(db_session, order.user_id)
        if not is_intact:
            logger.error(f"[SECURITY-FATAL] Loyalty balance tampering detected for user {order.user_id} before earning points. Aborting.")
            return False

        # Formula: Use centralized earning rate [ELITE V2.2]
        points_to_earn = math.floor(order.total_amount / LoyaltyConfig.EARNING_RATE_VND)
        
        if points_to_earn <= 0:
            return False

        # Get or create UserLoyalty with Pessimistic Locking
        loyalty_stmt = select(UserLoyalty).where(UserLoyalty.user_id == order.user_id).with_for_update()
        l_res = await db_session.execute(loyalty_stmt)
        loyalty = l_res.scalar_one_or_none()

        if not loyalty:
            loyalty = UserLoyalty(user_id=order.user_id, available_points=0, total_spent=0)
            db_session.add(loyalty)

        # Update points and spent amount
        # R2026: Convert from pending to available if applicable
        if loyalty.pending_points >= points_to_earn:
            loyalty.pending_points -= points_to_earn
            
        loyalty.available_points += points_to_earn
        loyalty.total_spent += order.total_amount
        
        # Check Tiers: STANDARD, SILVER, GOLD, PLATINUM (R2026) [ELITE STANDARDIZED]
        new_tier = "STANDARD"
        if loyalty.total_spent >= LoyaltyConfig.TIER_PLATINUM_THRESHOLD:
            new_tier = "PLATINUM"
        elif loyalty.total_spent >= LoyaltyConfig.TIER_GOLD_THRESHOLD:
            new_tier = "GOLD"
        elif loyalty.total_spent >= LoyaltyConfig.TIER_SILVER_THRESHOLD:
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

    @staticmethod
    async def _get_checkin_config(db_session: AsyncSession) -> dict:
        """Fetch check-in config from SystemSetting or fallback to default."""
        stmt = select(SystemSetting).where(SystemSetting.key == "LOYALTY_CHECKIN_CONFIG")
        res = await db_session.execute(stmt)
        setting = res.scalar_one_or_none()
        default_config = {
            "cycle_days": 7,
            "rewards": [10000, 10000, 10000, 10000, 10000, 10000, 10000]
        }
        if setting and setting.value and isinstance(setting.value, dict):
            return {
                "cycle_days": setting.value.get("cycle_days", 7),
                "rewards": setting.value.get("rewards", default_config["rewards"])
            }
        return default_config

    @staticmethod
    async def get_checkin_status(db_session: AsyncSession, user_id: str) -> dict:
        """Get user's current check-in state."""
        config = await LoyaltyService._get_checkin_config(db_session)
        
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
        res = await db_session.execute(stmt)
        loyalty = res.scalar_one_or_none()
        
        today_checked_in = False
        current_streak = 0
        
        now_hcm = datetime.now(timezone(timedelta(hours=7)))
        today_date = now_hcm.date()
        
        if loyalty and loyalty.last_checkin_date:
            last_date = loyalty.last_checkin_date.astimezone(timezone(timedelta(hours=7))).date()
            if last_date == today_date:
                today_checked_in = True
                current_streak = loyalty.current_checkin_streak
            elif last_date == today_date - timedelta(days=1):
                current_streak = loyalty.current_checkin_streak
            else:
                current_streak = 0
        
        return {
            "today_checked_in": today_checked_in,
            "current_streak": current_streak,
            "rewards": config["rewards"],
            "cycle_days": config["cycle_days"]
        }

    @staticmethod
    async def perform_daily_checkin(db_session: AsyncSession, user_id: str) -> dict:
        """Perform daily check-in with pessimistic locking."""
        # SECURITY R00: Verify integrity before updating points balance
        is_intact = await LoyaltyService.verify_loyalty_integrity(db_session, user_id)
        if not is_intact:
            raise Exception("[SECURITY-FATAL] Dữ liệu điểm thưởng bị sai lệch, không thể tiếp tục.")

        config = await LoyaltyService._get_checkin_config(db_session)
        
        # Lock the row
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id).with_for_update()
        res = await db_session.execute(stmt)
        loyalty = res.scalar_one_or_none()
        
        if not loyalty:
            loyalty = UserLoyalty(user_id=user_id, available_points=0, total_spent=0, current_checkin_streak=0)
            db_session.add(loyalty)
            
        now_hcm = datetime.now(timezone(timedelta(hours=7)))
        today_date = now_hcm.date()
        
        if loyalty.last_checkin_date:
            last_date = loyalty.last_checkin_date.astimezone(timezone(timedelta(hours=7))).date()
            if last_date == today_date:
                raise Exception("Hôm nay bạn đã điểm danh rồi!")
            elif last_date == today_date - timedelta(days=1):
                loyalty.current_checkin_streak += 1
            else:
                loyalty.current_checkin_streak = 1
        else:
            loyalty.current_checkin_streak = 1
            
        # Cycle reset
        cycle_days = config.get("cycle_days", 7)
        if loyalty.current_checkin_streak > cycle_days:
            loyalty.current_checkin_streak = 1
            
        # Determine reward
        rewards = config.get("rewards", [])
        reward_idx = loyalty.current_checkin_streak - 1
        reward_amount = rewards[reward_idx] if reward_idx < len(rewards) else 10000
        
        loyalty.last_checkin_date = now_hcm
        loyalty.available_points += reward_amount
        
        pt = PointTransaction(
            user_id=user_id,
            amount=reward_amount,
            transaction_type="DAILY_CHECKIN",
            notes=f"Điểm danh hằng ngày (Ngày {loyalty.current_checkin_streak})"
        )
        pt.integrity_token = LoyaltyService._create_transaction_token(pt)
        db_session.add(pt)
        
        loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)
        
        return {
            "reward_amount": reward_amount,
            "current_streak": loyalty.current_checkin_streak
        }
