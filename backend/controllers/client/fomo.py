from litestar import Controller, get
from backend.services.commerce.logic.fomo_service import fomo_service
from typing import List

class FomoController(Controller):
    """
    Elite V2.2: Fomo Activity Controller.
    Exposes real-time social proof and recent activities.
    """
    path = "/api/v1/client/fomo"

    @get("/activity")
    async def get_activity(self) -> List[dict]:
        """
        Fetch combined activity feed: Orders + Visitors + AI Trending.
        """
        return await fomo_service.get_recent_activities()

    @get("/metrics/{slug:str}")
    async def get_metrics(self, slug: str) -> dict:
        """
        Elite V2.2: Fetch authentic metrics for a specific product.
        """
        return await fomo_service.get_product_metrics(slug)
