import logging
import hashlib
import copy
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional
from uuid import UUID
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger("api-gateway")
from litestar import Controller, get, post, put, patch, delete, Request
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.models.schemas import (
    ContentCampaign as CampaignSchema, 
    CampaignStep, 
    AgentResponse,
    CampaignListResponse,
    GenericResponse
)
from backend.services.xohi.creative_studio.models.schemas import AgentSignal
from backend.database.repositories import ContentCampaignRepository, provide_campaign_repo
from litestar.di import Provide

class ContentController(Controller):
    path = "/api/v1/content"
    dependencies = {"campaign_repo": Provide(provide_campaign_repo)}

    @get("/campaigns")
    async def list_campaigns(
        self, 
        campaign_repo: ContentCampaignRepository,
        limit: int = 20,
        offset: int = 0
    ) -> CampaignListResponse:
        """Lấy danh sách các chiến dịch hỗ trợ phân trang (V72.10: Dynamic Paging)."""
        from sqlalchemy import select, func
        from backend.database.models import ContentCampaign as CampaignModel
        
        # 1. Total Count for frontend progress bar / stats
        count_stmt = select(func.count()).select_from(CampaignModel)
        total_count = await campaign_repo.session.execute(count_stmt)
        total = total_count.scalar_one()

        # 2. Paged results
        stmt = select(
            CampaignModel.id,
            CampaignModel.topic_data,
            CampaignModel.status,
            CampaignModel.current_step,
            CampaignModel.created_at,
            CampaignModel.user_id
        ).order_by(CampaignModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await campaign_repo.session.execute(stmt)
        items = [
            {
                "id": str(row.id),
                "topic_data": row.topic_data,
                "status": row.status,
                "current_step": row.current_step,
                "created_at": row.created_at.isoformat(),
                "user_id": str(row.user_id) if row.user_id else None
            }
            for row in result
        ]

        return CampaignListResponse(
            items=items,
            total=total,
            has_more=(offset + limit) < total,
            limit=limit,
            offset=offset
        )

    @get("/campaigns/{campaign_id:uuid}")
    async def get_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> CampaignSchema:
        """Lấy thông tin chi tiết một chiến dịch (Undefer support)."""
        from sqlalchemy.orm import undefer
        from sqlalchemy import select
        # R106: Force ORM model to avoid collision with Pydantic schema
        from backend.database.models import ContentCampaign as CampaignModel
        try:
            # R102: Explicitly undefer final_html for detail view
            stmt = select(CampaignModel).where(CampaignModel.id == str(campaign_id)).options(undefer(CampaignModel.final_html))
            result = await campaign_repo.session.execute(stmt)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                from litestar.exceptions import NotFoundException
                raise NotFoundException(f"Campaign {campaign_id} not found")
            return CampaignSchema.model_validate(campaign)
        except Exception as e:
            logger.error(f"[ContentController] Error fetching campaign {campaign_id}: {str(e)}")
            raise e

    @post("/campaigns/{campaign_id:uuid}/approve")
    async def approve_step(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """User phê duyệt bước sáng tạo hiện tại."""
        data: Dict[str, object] = await request.json()
        return await content_factory.approve_step(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/retry")
    async def retry_step(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """Chạy lại bước sáng tạo hiện tại."""
        return await content_factory.retry_step(str(campaign_id), campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/publish")
    async def publish_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """Xuất bản và địa phương hóa toàn bộ tài nguyên."""
        from backend.database.models import ContentCampaign as CampaignModel
        campaign: Optional[CampaignModel] = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        from backend.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
        compressor = MediaCompressor()
        await compressor.execute(str(campaign_id), campaign_repo)

        campaign.status = "COMPLETED"
        await campaign_repo.update(campaign)
        await campaign_repo.session.commit()
        return GenericResponse(status="success", message="Campaign published and localized.")

    @put("/campaigns/{campaign_id:uuid}/metadata")
    async def update_metadata(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """Cập nhật dữ liệu chiến dịch (keywords, assets...)."""
        data: Dict[str, object] = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @patch("/campaigns/{campaign_id:uuid}")
    async def patch_campaign(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """RESTful Alias cho update_metadata."""
        data: Dict[str, object] = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @delete("/campaigns/{campaign_id:uuid}", status_code=200)
    async def delete_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """Xóa chiến dịch và toàn bộ log chat liên quan (Hard Memory Purge)."""
        try:
            cid_str = str(campaign_id)
            
            # 1. Clean up associated ChatMessages (Resume Logs)
            from sqlalchemy import delete as sa_delete, func, cast, String
            from backend.database.models import ChatMessage
            
            # Robust JSON filtering (Phase 4): Works across SQLite and Postgres
            # We look for campaign_id in the content JSON
            stmt = sa_delete(ChatMessage).where(
                cast(ChatMessage.content["campaign_id"], String).label("cid") == cid_str
            )
            await campaign_repo.session.execute(stmt)
            
            # 2. Delete the campaign itself
            await campaign_repo.delete(cid_str)
            
            await campaign_repo.session.commit()
            return GenericResponse(status="success", message="Campaign and associated neural logs purged.")
        except Exception as e:
            # R102: Log the exception details for Phase 4 debugging
            logger.error(f"[ContentController] Purge failed for {campaign_id}: {str(e)}")
            # Fallback to simple delete if cleanup fails (Rule: Service continuity over total purge)
            try:
                await campaign_repo.delete(str(campaign_id))
                await campaign_repo.session.commit()
                return GenericResponse(status="partial_success", message="Campaign deleted, but logs may persist.")
            except Exception as e2:
                logger.critical(f"[ContentController] Total delete failure: {e2}")
                return GenericResponse(status="error", message=str(e2))

    @post("/campaigns/{campaign_id:uuid}/analyze/copyright")
    async def analyze_copyright(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        """
        On-demand: ĐẠO VĂN & BẢN QUYỀN — 2026 Edition.
        Dùng Google Search + Gemini AI để kiểm tra ngữ nghĩa (không phải so ký tự).
        """
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")
        if not campaign.draft_content:
            return GenericResponse(status="error", message="Chưa có nội dung để kiểm tra.")
        cop = PlagiarismCop()
        
        # Expert Optimizer (V71.30): Content Fingerprinting
        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = campaign.gold_metadata or {}
        cache = gold.get("analysis_cache", {})
        
        if not force and cache.get("copyright", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["copyright"]["data"])

        if force:
            logger.info(f"Copyright force refresh for campaign {campaign_id}")

        result = await cop.analyze(campaign)
        result_data = result.model_dump()
        
        # Archiving & Metrics
        cache["copyright"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
        metrics = gold.get("analysis_metrics", {})
        metrics["unique_score"] = result.uniqueness_score
        metrics["copyright_risk"] = result.risk_level
        metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()
        
        # ARCHIVING & METRICS (V71.30)
        new_gold = copy.deepcopy(campaign.gold_metadata or {})
        new_gold["analysis_cache"] = cache
        new_gold["analysis_metrics"] = metrics
        campaign.gold_metadata = new_gold
        campaign.unique_score = result.uniqueness_score
        flag_modified(campaign, "gold_metadata")
        
        await campaign_repo.update(campaign)
        await campaign_repo.session.commit()
        
        return {"status": "success", "data": result_data}

    @post("/campaigns/{campaign_id:uuid}/analyze/seo")
    async def analyze_seo(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        """
        On-demand: PHÂN TÍCH SEO 2026 — E-E-A-T, Entity Coverage, AI-Naturalness, Featured Snippet.
        """
        from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")
        if not campaign.draft_content:
            return GenericResponse(status="error", message="Chưa có nội dung để phân tích.")
        analyzer = SeoAnalyzer()
        
        # Expert Optimizer (V71.30): Content Fingerprinting
        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = campaign.gold_metadata or {}
        cache = gold.get("analysis_cache", {})
        
        if not force and cache.get("seo", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["seo"]["data"])

        if force:
            logger.info(f"SEO force refresh for campaign {campaign_id}")

        result = await analyzer.analyze(campaign)
        result_data = result.model_dump()
        
        # Archiving & Metrics
        cache["seo"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
        metrics = gold.get("analysis_metrics", {})
        metrics["seo_score"] = result.total_score
        metrics["seo_grade"] = result.grade
        metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()
        
        # ARCHIVING & METRICS (V71.30)
        new_gold = copy.deepcopy(campaign.gold_metadata or {})
        new_gold["analysis_cache"] = cache
        new_gold["analysis_metrics"] = metrics
        campaign.gold_metadata = new_gold
        flag_modified(campaign, "gold_metadata")
        await campaign_repo.update(campaign)
        await campaign_repo.session.commit()
        
        return {"status": "success", "data": result_data}

    @post("/campaigns/{campaign_id:uuid}/analyze/ai-inspect")
    async def analyze_ai_readiness(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        """
        On-demand: AI READINESS INSPECTOR — GEO 2026.
        Dùng LLM chấm điểm bài viết theo 4 tiêu chí cốt lõi (Princeton Study):
        1. Dữ liệu Thống kê & Tính Cụ thể
        2. Citations & Expert Quotes
        3. Fluency & No Fluff
        4. Quotable Snippet Structure
        """
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")
        if not campaign.draft_content:
            return GenericResponse(status="error", message="Chưa có nội dung để phân tích AI Readiness.")
        
        inspector = AiInspector()
        # Expert Optimizer (V71.30): Content Fingerprinting
        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = campaign.gold_metadata or {}
        cache = gold.get("analysis_cache", {})
        
        if not force and cache.get("ai_inspect", {}).get("hash") == content_hash:
            logger.info(f"AI Inspect cache hit for campaign {campaign_id}")
            return GenericResponse(status="success", data=cache["ai_inspect"]["data"])

        if force:
            logger.info(f"AI Inspect force refresh for campaign {campaign_id}")

        try:
            result = await inspector.analyze(campaign)
            result_data = result.model_dump()
            
            # Archiving & Metrics
            cache["ai_inspect"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
            metrics = gold.get("analysis_metrics", {})
            metrics["ai_ready_score"] = result.geo_score
            metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()
            
            # ARCHIVING & METRICS (V71.30)
            new_gold = copy.deepcopy(campaign.gold_metadata or {})
            new_gold["analysis_cache"] = cache
            new_gold["analysis_metrics"] = metrics
            campaign.gold_metadata = new_gold
            flag_modified(campaign, "gold_metadata")
            await campaign_repo.update(campaign)
            await campaign_repo.session.commit()
            logger.info(f"[EXPERT] COMMIT SUCCESS for campaign {campaign_id}")
            
            return GenericResponse(status="success", data=result_data)
        except Exception as e:
            logger.error(f"AI Inspector error: {e}")
            return GenericResponse(status="error", message=str(e))
    @post("/campaigns/{campaign_id:uuid}/analyze/auto-fix")
    async def analyze_auto_fix(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """
        On-Demand Surgical Auto-Fix (Contextual Local Rewrite)
        """
        try:
            from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector, AutoFixRequest
            campaign = await campaign_repo.get(str(campaign_id))
            if not campaign:
                    return GenericResponse(status="error", message="Campaign not found")
            if not campaign.draft_content:
                return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")
            
            inspector = AiInspector()
            data = await request.json()
            fix_req = AutoFixRequest(**data)
            
            result = await inspector.auto_fix(campaign, fix_req)
            return GenericResponse(status="success", data=result.model_dump())
        except Exception as e:
            logger.error(f"Auto-Fix error: {e}")
            return GenericResponse(status="error", message=str(e))

    @post("/campaigns/{campaign_id:uuid}/analyze/bulk-fix")
    async def analyze_bulk_fix(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """
        On-Demand Bulk Surgical Rewrite: Fixes ALL identified errors for a category.
        """
        try:
            from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
            from backend.services.xohi.creative_studio.models.schemas import BulkFixRequest
            campaign = await campaign_repo.get(str(campaign_id))
            if not campaign:
                    return GenericResponse(status="error", message="Campaign not found")
            if not campaign.draft_content:
                return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")
            
            inspector = AiInspector()
            data = await request.json()
            fix_req = BulkFixRequest(**data)
            
            result = await inspector.bulk_fix(campaign, fix_req)
            return GenericResponse(status="success", data=result.model_dump())
        except Exception as e:
            logger.error(f"Bulk-Fix error: {e}")
            return GenericResponse(status="error", message=str(e))
