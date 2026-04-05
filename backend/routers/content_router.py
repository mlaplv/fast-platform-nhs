import logging
from typing import Dict
from uuid import UUID
from litestar import Controller, get, post, put, patch, delete, Request
from litestar.di import Provide
from litestar.exceptions import NotFoundException

from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.services.xohi.creative_studio.orchestrator import content_factory

# Repository & Provider Imports
from backend.database.repositories import (
    ContentCampaignRepository, provide_campaign_repo,
    MediaRegistryRepository, provide_media_repo
)

# Schema Imports
from backend.schemas.content import (
    CampaignSchema, CampaignListResponse, ContentCleanRequest,
    AdhocAnalysisRequest, BulkFixRequest, ScoutTopicRequest
)
from backend.schemas.common import SuccessResponse as GenericResponse

logger = logging.getLogger("api-gateway")

class ContentController(Controller):
    path = "/api/v1/content"
    guards = [PermissionGuard(PermissionEnum.CONTENT_READ)]
    """R4: Unified Content Management Controller."""
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

    @post("/campaigns/{campaign_id:uuid}/approve", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def approve_step(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.approve_step(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/retry", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def retry_step(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await content_factory.retry_step(str(campaign_id), campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/cancel", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def cancel_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await content_factory.management.cancel_campaign(str(campaign_id), campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/publish", guards=[PermissionGuard(PermissionEnum.CONTENT_PUBLISH)])
    async def publish_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        return await content_factory.management.publish_campaign(str(campaign_id), campaign_repo, media_repo)

    @put("/campaigns/{campaign_id:uuid}/metadata", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def update_metadata(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @patch("/campaigns/{campaign_id:uuid}", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def patch_campaign(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @delete("/campaigns/{campaign_id:uuid}", status_code=200, guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def delete_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        return await content_factory.management.delete_campaign(str(campaign_id), campaign_repo, media_repo)

    @post("/campaigns/{campaign_id:uuid}/analyze/copyright")
    async def analyze_copyright(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_copyright(str(campaign_id), campaign_repo, force=force)

    @post("/campaigns/{campaign_id:uuid}/analyze/seo")
    async def analyze_seo(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_seo(str(campaign_id), campaign_repo, force=force)

    @post("/campaigns/{campaign_id:uuid}/analyze/ai-inspect")
    async def analyze_ai_readiness(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_ai_inspect(str(campaign_id), campaign_repo, force=force)

    @post("/campaigns/{campaign_id:uuid}/analyze/auto-fix", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_auto_fix(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.analyst.auto_fix(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/analyze/bulk-fix", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_bulk_fix(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        data = await request.json()
        return await content_factory.analyst.bulk_fix(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/analyze/enrich")
    async def analyze_enrich(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await content_factory.analyst.enrich(str(campaign_id), campaign_repo)

    @post("/clean", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def clean_content(self, data: ContentCleanRequest) -> GenericResponse:
        try:
            from backend.utils.noise_cleaner import noise_cleaner
            cleaned = await noise_cleaner.clean(data.content, mode="aggressive")
            return GenericResponse(status="success", data={"content": cleaned})
        except Exception as e:
            logger.error(f"[ContentController] Viral Clean Error: {e}")
            return GenericResponse(status="error", message=str(e))

    @post("/analyze/copyright")
    async def analyze_copyright_adhoc(self, data: AdhocAnalysisRequest) -> GenericResponse:
        return await content_factory.analyst.analyze_copyright(None, None, force=data.force, raw_content=data.content, raw_topic=data.topic)

    @post("/analyze/seo")
    async def analyze_seo_adhoc(self, data: AdhocAnalysisRequest) -> GenericResponse:
        return await content_factory.analyst.analyze_seo(None, None, force=data.force, raw_content=data.content, raw_topic=data.topic)

    @post("/analyze/ai-inspect")
    async def analyze_ai_inspect_adhoc(self, data: AdhocAnalysisRequest) -> GenericResponse:
        return await content_factory.analyst.analyze_ai_inspect(None, None, force=data.force, raw_content=data.content, raw_topic=data.topic)

    @post("/analyze/bulk-fix")
    async def analyze_bulk_fix_adhoc(self, data: BulkFixRequest) -> GenericResponse:
        fix_payload = {"category": data.category, "annotations": data.annotations}
        return await content_factory.analyst.bulk_fix(None, fix_payload, None, raw_content=data.content)

    @post("/scout")
    async def scout_topic(self, data: ScoutTopicRequest) -> GenericResponse:
        """[CNS V62.2] Perform high-IQ content scouting and strategic analysis."""
        return await content_factory.analyst.scout(data.topic, campaign_id=data.campaign_id)

