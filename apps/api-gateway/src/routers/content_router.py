from typing import List, Optional, Dict, Any
import logging
from uuid import UUID
from litestar import Controller, get, post, delete, Request
from litestar.params import Body
from litestar.di import Provide
from litestar.repository.filters import LimitOffset
from src.database.repositories import (
    ContentCampaignRepository, provide_campaign_repo
)
from src.database.models import ContentCampaign
from src.services.xohi.creative_studio.orchestrator import content_factory

logger = logging.getLogger("api-gateway")

class ContentRouter(Controller):
    """
    V62.1 Content Factory API — Campaign Management & Review.
    """
    path = "/api/v1/content"
    dependencies = {
        "campaign_repo": Provide(provide_campaign_repo)
    }

    @get("/campaigns")
    async def list_campaigns(
        self, 
        campaign_repo: ContentCampaignRepository,
        limit: int = 20,
        offset: int = 0
    ) -> List[ContentCampaign]:
        """List all content campaigns for current tenant."""
        from litestar.repository.filters import LimitOffset
        return await campaign_repo.list(
            LimitOffset(limit, offset),
            order_by=[("created_at", "desc")],
            deleted_at=None
        )

    @get("/campaigns/{campaign_id:uuid}")
    async def get_campaign(
        self, 
        campaign_id: UUID,
        campaign_repo: ContentCampaignRepository
    ) -> ContentCampaign:
        """Get details for a specific campaign."""
        return await campaign_repo.get(str(campaign_id))

    @post("/campaigns/{campaign_id:uuid}/approve")
    async def approve_step(
        self,
        campaign_id: UUID,
        campaign_repo: ContentCampaignRepository,
        data: Dict[str, Any] = Body(),
    ) -> Dict[str, Any]:
        """
        Approve the current step and proceed to the next one.
        'data' can contain 'feedback_or_edits' to modify the step data before proceeding.
        """
        logger.info(f"[Content API] Approving campaign {campaign_id}")
        # Logic will be implemented in orchestrator
        return await content_factory.approve_step(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/retry")
    async def retry_step(
        self,
        campaign_id: UUID,
        campaign_repo: ContentCampaignRepository
    ) -> Dict[str, Any]:
        """Retry the current step (e.g. if AI failed)."""
        logger.info(f"[Content API] Retrying campaign {campaign_id}")
        return await content_factory.retry_step(str(campaign_id), campaign_repo)

    @delete("/campaigns/{campaign_id:uuid}")
    async def delete_campaign(
        self,
        campaign_id: UUID,
        campaign_repo: ContentCampaignRepository
    ) -> None:
        """Soft delete a campaign."""
        await campaign_repo.delete(str(campaign_id))
        # session.commit is handled by litestar
