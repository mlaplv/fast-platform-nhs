from typing import List, Dict, Any, Union, Optional
from uuid import UUID
from litestar import Controller, get, post, put, delete, Request
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.models.schemas import ContentCampaign, CampaignStep, AgentResponse
from backend.services.xohi.creative_studio.orchestrator import AgentSignal
from backend.database.repositories import ContentCampaignRepository, provide_campaign_repo
from litestar.di import Provide

class ContentController(Controller):
    path = "/api/v1/content"
    dependencies = {"campaign_repo": Provide(provide_campaign_repo)}

    @get("/campaigns")
    async def list_campaigns(self, campaign_repo: ContentCampaignRepository) -> List[ContentCampaign]:
        """Lấy danh sách tất cả các chiến dịch nội dung đang chạy."""
        from litestar.repository.filters import LimitOffset
        campaigns = await campaign_repo.list(LimitOffset(limit=100, offset=0), order_by=[("created_at", "desc")])
        return [ContentCampaign.model_validate(c) for c in campaigns]

    @get("/campaigns/{campaign_id:uuid}")
    async def get_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> ContentCampaign:
        """Lấy thông tin chi tiết của một chiến dịch cụ thể."""
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Campaign {campaign_id} not found")
        return ContentCampaign.model_validate(campaign)

    @post("/campaigns/{campaign_id:uuid}/approve")
    async def approve_step(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        User phê duyệt kết quả của Step hiện tại và cho phép đi tiếp.
        R81: gold_metadata is IMMUTABLE.
        """
        data = await request.json()
        return await content_factory.approve_step(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/retry")
    async def retry_step(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        Thực hiện chạy lại Step hiện tại (Retry).
        """
        return await content_factory.retry_step(str(campaign_id), campaign_repo)

    @put("/campaigns/{campaign_id:uuid}/metadata")
    async def update_metadata(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        Cập nhật metadata (assets, keywords, etc.) mà không chuyển bước.
        R85.1: Phục vụ curation thời gian thực (F5 Fix).
        """
        data = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @delete("/campaigns/{campaign_id:uuid}", status_code=200)
    async def delete_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        Xóa chiến dịch (Soft Delete).
        """
        try:
            await campaign_repo.delete(str(campaign_id))
            return {"status": "success", "message": "Campaign deleted."}
        except Exception:
            return {"status": "error", "message": "Campaign not found or could not be deleted."}
