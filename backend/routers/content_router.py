import logging
from typing import Dict
from uuid import UUID
from litestar import Controller, get, post, put, patch, delete, Request
from litestar.di import Provide

from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.models.schemas import (
    ContentCampaign as CampaignSchema, 
    CampaignListResponse,
    GenericResponse
)
from backend.database.repositories import ContentCampaignRepository, MediaRegistryRepository, provide_campaign_repo, provide_media_repo

logger = logging.getLogger("api-gateway")

class ContentController(Controller):
    path = "/api/v1/content"
    dependencies = {
        "campaign_repo": Provide(provide_campaign_repo),
        "media_repo": Provide(provide_media_repo)
    }

    @get("/campaigns")
    async def list_campaigns(self, campaign_repo: ContentCampaignRepository, limit: int = 20, offset: int = 0) -> CampaignListResponse:
        return await content_factory.management.list_campaigns(campaign_repo, limit, offset)

    @get("/campaigns/{campaign_id:uuid}")
    async def get_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> CampaignSchema:
        from sqlalchemy.orm import undefer
        from sqlalchemy import select
        from backend.database.models import ContentCampaign as CampaignModel
        stmt = select(CampaignModel).where(CampaignModel.id == str(campaign_id)).options(undefer(CampaignModel.final_html))
        campaign = (await campaign_repo.session.execute(stmt)).scalar_one_or_none()
        if not campaign:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Campaign {campaign_id} not found")
        return CampaignSchema.model_validate(campaign)

    @post("/campaigns/{campaign_id:uuid}/approve")
    async def approve_step(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.approve_step(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/retry")
    async def retry_step(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await content_factory.retry_step(str(campaign_id), campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/cancel")
    async def cancel_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        from backend.database.models import ContentCampaign as CampaignModel
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign: return GenericResponse(status="error", message="Campaign not found")
        campaign.status = "REJECTED"; await campaign_repo.update(campaign)
        from backend.services.event_bus import event_bus
        await event_bus.emit("CAMPAIGN_PURGED", {"campaign_id": str(campaign_id), "type": "TERMINATE", "action": "CANCEL"})
        await campaign_repo.session.commit()
        return GenericResponse(status="success", message="Hệ thống đã ngắt và hủy tiến trình theo lệnh sếp.")

    @post("/campaigns/{campaign_id:uuid}/publish")
    async def publish_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        from backend.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign: return GenericResponse(status="error", message="Campaign not found")
        await MediaCompressor().execute(str(campaign_id), campaign_repo, media_repo=media_repo)
        campaign.status = "COMPLETED"; await campaign_repo.update(campaign)
        await campaign_repo.session.commit()
        return GenericResponse(status="success", message="Campaign published and registered.")

    @put("/campaigns/{campaign_id:uuid}/metadata")
    async def update_metadata(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @patch("/campaigns/{campaign_id:uuid}")
    async def patch_campaign(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @delete("/campaigns/{campaign_id:uuid}", status_code=200)
    async def delete_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        return await content_factory.management.delete_campaign(str(campaign_id), campaign_repo, media_repo)

    @post("/campaigns/{campaign_id:uuid}/analyze/copyright")
    async def analyze_copyright(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_copyright(str(campaign_id), campaign_repo, force)

    @post("/campaigns/{campaign_id:uuid}/analyze/seo")
    async def analyze_seo(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_seo(str(campaign_id), campaign_repo, force)

    @post("/campaigns/{campaign_id:uuid}/analyze/ai-inspect")
    async def analyze_ai_readiness(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_ai_inspect(str(campaign_id), campaign_repo, force)

    @post("/campaigns/{campaign_id:uuid}/analyze/auto-fix")
    async def analyze_auto_fix(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.analyst.auto_fix(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/analyze/bulk-fix")
    async def analyze_bulk_fix(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.analyst.bulk_fix(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/analyze/enrich")
    async def analyze_enrich(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await content_factory.analyst.enrich(str(campaign_id), campaign_repo)

    @post("/clean")
    async def clean_content(self, request: Request) -> GenericResponse:
        try:
            from backend.utils.noise_cleaner import noise_cleaner
            data = await request.json(); content = data.get("content", "")
            if not content: return GenericResponse(status="error", message="Không có nội dung để làm sạch")
            cleaned = await noise_cleaner.clean(content, mode="aggressive")
            return GenericResponse(status="success", data={"content": cleaned})
        except Exception as e:
            logger.error(f"[ContentController] Viral Clean Error: {e}")
            return GenericResponse(status="error", message=str(e))

    @post("/analyze/copyright")
    async def analyze_copyright_adhoc(self, request: Request) -> GenericResponse:
        data = await request.json()
        return await content_factory.analyst.analyze_copyright(None, None, force=data.get("force", False), raw_content=data.get("content"))

    @post("/analyze/seo")
    async def analyze_seo_adhoc(self, request: Request) -> GenericResponse:
        data = await request.json()
        return await content_factory.analyst.analyze_seo(None, None, force=data.get("force", False), raw_content=data.get("content"), raw_topic=data.get("topic"))

    @post("/analyze/ai-inspect")
    async def analyze_ai_inspect_adhoc(self, request: Request) -> GenericResponse:
        data = await request.json()
        return await content_factory.analyst.analyze_ai_inspect(None, None, force=data.get("force", False), raw_content=data.get("content"))

    @post("/analyze/bulk-fix")
    async def analyze_bulk_fix_adhoc(self, request: Request) -> GenericResponse:
        data = await request.json()
        # Extract only the fields BulkFixRequest accepts (strict mode: category + annotations)
        fix_payload = {"category": data.get("category", ""), "annotations": data.get("annotations", [])}
        return await content_factory.analyst.bulk_fix(None, fix_payload, None, raw_content=data.get("content"))

