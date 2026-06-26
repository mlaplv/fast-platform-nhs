import logging
from typing import Dict, AsyncGenerator, Optional, List
from uuid import UUID
from litestar import Controller, get, post, put, patch, delete, Request, Response
from litestar.response import Stream
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from litestar.enums import MediaType

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
    AdhocAnalysisRequest, BulkFixRequest, ScoutTopicRequest,
    AdhocAutoFixRequest, SurgeonBoostRequest, NeuralRewriteRequest
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
        stmt = select(CampaignModel).where(
            CampaignModel.id == str(campaign_id),
            CampaignModel.deleted_at == None
        ).options(undefer(CampaignModel.final_html))
        campaign = (await campaign_repo.session.execute(stmt)).scalar_one_or_none()
        if not campaign:
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
            opts = data.options.model_dump() if data.options else None
            cleaned = await noise_cleaner.clean(data.content, mode="aggressive", options=opts)
            return GenericResponse(status="success", data={"content": cleaned})
        except Exception as e:
            logger.error(f"[ContentController] Viral Clean Error: {e}")
            return GenericResponse(status="error", message=str(e))

    @post("/analyze/copyright")
    async def analyze_copyright_adhoc(self, data: AdhocAnalysisRequest, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_copyright(None, None, force=force or data.force, raw_content=data.content, raw_topic=data.topic, content_type=data.content_type)

    @post("/analyze/seo")
    async def analyze_seo_adhoc(self, data: AdhocAnalysisRequest, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_seo(
            None, None,
            force=force or data.force,
            raw_content=data.content,
            raw_topic=data.topic,
            content_type=data.content_type,
            analysis_cache=data.analysis_cache
        )

    @post("/analyze/ai-inspect")
    async def analyze_ai_inspect_adhoc(self, data: AdhocAnalysisRequest, force: bool = False) -> GenericResponse:
        return await content_factory.analyst.analyze_ai_inspect(None, None, force=force or data.force, raw_content=data.content, raw_topic=data.topic, content_type=data.content_type)

    @post("/analyze/bulk-fix")
    async def analyze_bulk_fix_adhoc(self, data: BulkFixRequest) -> GenericResponse:
        fix_payload = {"category": data.category, "annotations": data.annotations}
        return await content_factory.analyst.bulk_fix(None, fix_payload, None, raw_content=data.content)

    @post("/scout")
    async def scout_topic(self, data: ScoutTopicRequest) -> GenericResponse:
        """[CNS V62.2] Perform high-IQ content scouting and strategic analysis."""
        return await content_factory.analyst.scout(data.topic, campaign_id=data.campaign_id)

    @post("/analyze/auto-fix", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_auto_fix_adhoc(self, data: AdhocAutoFixRequest) -> GenericResponse:
        """CNS V86.5: Ad-hoc auto-fix — sửa từng annotation không cần campaign_id."""
        return await content_factory.analyst.auto_fix_adhoc(
            content=data.content,
            target_snippet=data.target_snippet,
            annotation_type=data.annotation_type,
            error_message=data.error_message,
            topic=data.topic,
        )
    @post("/analyze/auto-fix-stream", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_auto_fix_stream(
        self,
        request: Request,
    ) -> Stream:
        """CNS V87.0: SSE streaming auto-fix — typewriter effect từng chunk text."""
        data = await request.json()
        content = data.get("content", "")
        target_snippet = data.get("target_snippet", "")
        error_message = data.get("error_message", "")
        topic = data.get("topic", "")

        async def _gen() -> AsyncGenerator[str, None]:
            async for line in content_factory.analyst.stream_auto_fix(
                content=content,
                target_snippet=target_snippet,
                error_message=error_message,
                topic=topic,
            ):
                yield line

        return Stream(
            content=_gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @post("/analyze/neural-boost", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_neural_boost(self, data: SurgeonBoostRequest, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """CNS V87.0: Neural Boost (Refinement)"""
        return await content_factory.analyst.neural_boost(
            content=data.content,
            topic=data.topic,
            campaign_id=data.campaign_id,
            campaign_repo=campaign_repo,
            content_type=data.content_type or "article",  # CNS V92.1
        )

    @post("/analyze/neural-rewrite", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_neural_rewrite(self, data: NeuralRewriteRequest, campaign_id: Optional[UUID] = None) -> GenericResponse:
        """CNS V88.5: Neural Rewrite — viết lại toàn bộ bài viết dựa trên phản biện."""
        return await content_factory.analyst.neural_rewrite(
            content=data.content,
            topic=data.topic,
            feedback=data.feedback,
            campaign_id=str(campaign_id) if campaign_id else None,
            content_type=data.content_type or "article",
            metadata=data.metadata,
            user_note=data.user_note
        )

    @post("/campaigns/{campaign_id:uuid}/analyze/save-report", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_save_report(
        self, campaign_id: UUID, report_type: str, data: Dict[str, object]
    ) -> GenericResponse:
        """CNS V87.0: Lưu báo cáo phân tích cho campaign."""
        return await content_factory.analyst.save_analysis_report(
            campaign_id=str(campaign_id),
            campaign_repo=content_factory.campaigns,
            report_type=report_type,
            data=data,
        )

    @post("/campaigns/{campaign_id:uuid}/analyze/batch-save", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def analyze_batch_save(
        self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository
    ) -> GenericResponse:
        """
        [CNS V90.0] Batch Save — Gộp save-report + metadata thành 1 HTTP call.
        Giảm từ 2 POST → 1 POST per analysis. Tiết kiệm ~1 RTT mỗi phiên.
        """
        from datetime import datetime, timezone
        data = await request.json()
        reports: Dict[str, object] = data.get("reports", {})
        evidence: Dict[str, object] = data.get("evidence", {})

        try:
            campaign = await campaign_repo.get(str(campaign_id))
            if not campaign:
                return GenericResponse(status="error", message="Campaign not found")

            from sqlalchemy.orm.attributes import flag_modified

            # 1. Cập nhật analysis_report (gộp tất cả report types)
            if reports:
                report = dict(campaign.analysis_report or {})
                now_iso = datetime.now(timezone.utc).isoformat()
                for report_type, report_data in reports.items():
                    if report_type in ("copyright", "seo", "ai_inspect", "surgeon", "enrich", "rewrite"):
                        report[report_type] = {
                            "data": report_data,
                            "updated_at": now_iso,
                            "version": "V90.0"
                        }
                campaign.analysis_report = report
                flag_modified(campaign, "analysis_report")

            # 2. Cập nhật analysis_evidence vào gold_metadata
            if evidence:
                gold = dict(campaign.gold_metadata or {})
                existing_evidence = dict(gold.get("analysis_evidence", {}))
                existing_evidence.update(evidence)
                gold["analysis_evidence"] = existing_evidence
                campaign.gold_metadata = gold
                flag_modified(campaign, "gold_metadata")

            await campaign_repo.update(campaign)
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()

            logger.info(f"[ContentController] Batch saved {list(reports.keys())} for campaign {campaign_id}")
            return GenericResponse(status="success", message=f"Đã lưu batch: {', '.join(reports.keys())}")
        except Exception as e:
            logger.error(f"[ContentController] Batch save error: {e}", exc_info=True)
            return GenericResponse(status="error", message=str(e))
