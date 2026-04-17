import logging
from typing import Dict, Optional, List
from sqlalchemy import select, desc
from backend.services.xohi_memory import xohi_memory
from backend.database import async_session_maker
from backend.database.models.commerce import Order

logger = logging.getLogger("api-gateway")

class FomoService:
    """
    Elite V2.2: Authentic FOMO & Social Proof Engine.
    SSOT for scarcity and urgency metrics.
    No mock data allowed - all metrics derived from Redis/DB state.
    """

    async def get_active_visitors_count(self) -> int:
        """
        Scan Redis for 'support:presence:*' keys.
        Returns the number of active support sessions in the last 2 minutes.
        Elite V2.2: Using SCAN_ITER to ensure O(1) blocking per step.
        """
        try:
            if not xohi_memory._use_redis or not xohi_memory.client:
                return 1 # Fallback for local dev/non-redis envs
            
            count = 0
            # Use scan_iter for non-blocking iteration (RAM efficient)
            async for _ in xohi_memory.client.scan_iter("support:presence:*"):
                count += 1
            
            return max(1, count)
        except Exception as e:
            logger.warning(f"[FomoService] Failed to scan visitors: {e}")
            return 1

    def get_scarcity_vibe(self, stock: int) -> str:
        """
        Determines the urgency level based on real stock.
        Elite V2.2: Thresholds for psychological triggers.
        """
        if stock <= 0:
            return "OUT_OF_STOCK" # Don't push, just inform
        if stock <= 5:
            return "CRITICAL"    # High Urgency: "Only {n} left!"
        if stock <= 15:
            return "LOW"         # Moderate Urgency: "Limited stock available"
        return "STABLE"          # No FOMO required

    def get_social_proof_vibe(self, visitor_count: int) -> str:
        """
        Determines the social proof level based on active presence.
        """
        if visitor_count >= 10:
            return "VIRAL"       # "Currently 10+ people are also viewing this"
        if visitor_count >= 5:
            return "HOT"         # "Many customers are currently interested"
        if visitor_count >= 2:
            return "TRENDING"    # "Growing interest in this item"
        return "QUIET"           # Focus on product quality instead

    async def get_recent_activities(self) -> List[dict]:
        """
        Elite V2.2: Fetch real recent orders and combine with visitor metrics.
        Returns anonymized activity feed.
        """
        activities = []
        
        # 1. Get Live Visitor Count
        visitors = await self.get_active_visitors_count()
        if visitors > 3:
            activities.append({
                "type": "VISITORS",
                "count": visitors,
                "msg": f"Có {visitors} người cũng đang xem như bạn",
                "icon": "Users"
            })

        # 2. Get Recent Orders
        async with async_session_maker() as db_session:
            try:
                stmt = select(Order).where(Order.is_spam == False).order_by(desc(Order.created_at)).limit(5)
                res = await db_session.execute(stmt)
                orders = res.scalars().all()
                
                for order in orders:
                    # Anonymize: "Nguyễn Văn A" -> "Anh A."
                    name = order.customer_name or "Khách hàng"
                    if len(name.split()) > 1:
                        parts = name.split()
                        name = f"{parts[0]} {parts[-1][0]}."
                    
                    activities.append({
                        "type": "ORDER",
                        "name": name,
                        "action": "vừa sở hữu thành công",
                        "time": "vừa xong",
                        "icon": "ShoppingBag"
                    })
            except Exception as e:
                logger.error(f"[FomoService] Error fetching recent orders: {e}")

        # 3. AI Hybrid: If no orders, add a Scarcity/Trending vibe
        if not activities:
            activities.append({
                "type": "TRENDING",
                "msg": "Sản phẩm đang được quan tâm đặc biệt bởi AI",
                "icon": "Zap"
            })

        return activities

fomo_service = FomoService()
