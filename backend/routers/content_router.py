from typing import List, Dict, Any, Union, Optional
from uuid import UUID
from litestar import Controller, get, post, put, delete, Request
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.models.schemas import ContentCampaign, CampaignStep, AgentResponse
from backend.services.xohi.creative_studio.orchestrator import AgentSignal

class ContentController(Controller):
    path = "/api/v1/content"

    @get("/campaigns")
    async def list_campaigns(self) -> List[ContentCampaign]:
        """Lấy danh sách tất cả các chiến dịch nội dung đang chạy."""
        return list(content_factory.campaigns.values())

    @get("/campaigns/{campaign_id:uuid}")
    async def get_campaign(self, campaign_id: UUID) -> ContentCampaign:
        """Lấy thông tin chi tiết của một chiến dịch cụ thể."""
        campaign = content_factory.get_campaign(campaign_id)
        if not campaign:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Campaign {campaign_id} not found")
        return campaign

    @put("/campaigns/{campaign_id:uuid}/approve")
    async def approve_step(self, campaign_id: UUID, request: Request) -> Dict[str, Any]:
        """
        User phê duyệt kết quả của Step hiện tại và cho phép đi tiếp.
        R81: gold_metadata is IMMUTABLE.
        """
        success = await content_factory.approve_step(campaign_id)
        if success:
            return {"status": "success", "message": "Step approved. Moving to next stage."}
        return {"status": "error", "message": "Failed to approve step."}

    @post("/campaigns/{campaign_id:uuid}/retry")
    async def retry_step(self, campaign_id: UUID) -> Dict[str, Any]:
        """
        Thực hiện chạy lại Step hiện tại (Retry).
        """
        success = await content_factory.retry_step(campaign_id)
        if success:
            return {"status": "success", "message": "Retry initiated."}
        return {"status": "error", "message": "Failed to initiate retry."}

    @delete("/campaigns/{campaign_id:uuid}", status_code=200)
    async def delete_campaign(self, campaign_id: UUID) -> Dict[str, Any]:
        """
        Xóa chiến dịch.
        Note: We use status_code=200 because we return a JSON body. 
        Litestar's default 204 does not allow bodies.
        """
        if str(campaign_id) in content_factory.campaigns:
            del content_factory.campaigns[str(campaign_id)]
            return {"status": "success", "message": "Campaign deleted."}
        return {"status": "error", "message": "Campaign not found."}
