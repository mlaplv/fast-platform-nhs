import logging
from typing import Dict, Optional
from backend.services.xohi_memory import xohi_memory

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

fomo_service = FomoService()
