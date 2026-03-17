# backend/api/v1/controllers/content/analysis.py
import logging
import hashlib
import copy
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID
from sqlalchemy.orm.attributes import flag_modified
from litestar import Controller, post, Request
from litestar.di import Provide

from backend.api.v1.schemas.schemas import GenericResponse
from backend.database.repositories import ContentCampaignRepository, MediaRegistryRepository, provide_campaign_repo, provide_media_repo

logger = logging.getLogger("api-gateway")

class ContentAnalysisController(Controller):
    path = "/api/v1/content"
    dependencies = {
        "campaign_repo": Provide(provide_campaign_repo),
        "media_repo": Provide(provide_media_repo)
    }

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

        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = campaign.gold_metadata or {}
        cache = gold.get("analysis_cache", {})

        if not force and cache.get("copyright", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["copyright"]["data"])

        try:
            result = await cop.analyze(campaign)
            result_data = result.model_dump()

            cache["copyright"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
            metrics = gold.get("analysis_metrics", {})
            metrics["unique_score"] = result.uniqueness_score
            metrics["copyright_risk"] = result.risk_level
            metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()

            new_gold = copy.deepcopy(campaign.gold_metadata or {})
            new_gold["analysis_cache"] = cache
            new_gold["analysis_metrics"] = metrics
            campaign.gold_metadata = new_gold
            campaign.unique_score = result.uniqueness_score
            flag_modified(campaign, "gold_metadata")

            await campaign_repo.update(campaign)
            await campaign_repo.session.commit()

            return GenericResponse(status="success", data=result_data)
        except Exception as e:
            logger.error(f"[ContentController] Copyright analysis failed: {str(e)}", exc_info=True)
            return GenericResponse(status="error", message=str(e))

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

        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = campaign.gold_metadata or {}
        cache = gold.get("analysis_cache", {})

        if not force and cache.get("seo", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["seo"]["data"])

        try:
            result = await analyzer.analyze(campaign)
            result_data = result.model_dump()

            cache["seo"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
            metrics = gold.get("analysis_metrics", {})
            metrics["seo_score"] = result.total_score
            metrics["seo_grade"] = result.grade
            metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()

            new_gold = copy.deepcopy(campaign.gold_metadata or {})
            new_gold["analysis_cache"] = cache
            new_gold["analysis_metrics"] = metrics
            campaign.gold_metadata = new_gold
            flag_modified(campaign, "gold_metadata")
            await campaign_repo.update(campaign)
            await campaign_repo.session.commit()

            return GenericResponse(status="success", data=result_data)
        except Exception as e:
            logger.error(f"[ContentController] SEO analysis failed: {str(e)}")
            return GenericResponse(status="error", message=str(e))

    @post("/campaigns/{campaign_id:uuid}/analyze/ai-inspect")
    async def analyze_ai_readiness(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, force: bool = False) -> GenericResponse:
        """
        On-demand: AI READINESS INSPECTOR — GEO 2026.
        """
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")
        if not campaign.draft_content:
            return GenericResponse(status="error", message="Chưa có nội dung để phân tích AI Readiness.")

        inspector = AiInspector()
        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        gold = campaign.gold_metadata or {}
        cache = gold.get("analysis_cache", {})

        if not force and cache.get("ai_inspect", {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache["ai_inspect"]["data"])

        try:
            result = await inspector.analyze(campaign)
            result_data = result.model_dump()

            cache["ai_inspect"] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
            metrics = gold.get("analysis_metrics", {})
            metrics["ai_ready_score"] = result.geo_score
            metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()

            new_gold = copy.deepcopy(campaign.gold_metadata or {})
            new_gold["analysis_cache"] = cache
            new_gold["analysis_metrics"] = metrics
            campaign.gold_metadata = new_gold
            flag_modified(campaign, "gold_metadata")
            await campaign_repo.update(campaign)
            await campaign_repo.session.commit()

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
            from backend.services.xohi.creative_studio.models.schemas import BulkFixRequest
            from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
            from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop

            campaign = await campaign_repo.get(str(campaign_id))
            if not campaign:
                return GenericResponse(status="error", message="Campaign not found")
            if not campaign.draft_content:
                return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")

            data = await request.json()
            fix_req = BulkFixRequest(**data)

            operative = PlagiarismCop() if fix_req.category == "copyright" else AiInspector()
            result = await operative.bulk_fix(campaign, fix_req)

            if result.new_content and result.new_content != campaign.draft_content:
                campaign.draft_content = result.new_content
                flag_modified(campaign, "draft_content")
                await campaign_repo.update(campaign)
                await campaign_repo.session.commit()

            return GenericResponse(status="success", data=result.model_dump())
        except Exception as e:
            logger.error(f"Bulk-Fix error: {e}")
            return GenericResponse(status="error", message=str(e))

    @post("/clean")
    async def clean_content(self, request: Request) -> GenericResponse:
        """
        Phase 76.9: Viral 2026 Semantic Polishing.
        """
        try:
            from backend.core.utils.noise_cleaner import noise_cleaner
            data = await request.json()
            content = data.get("content", "")
            if not content:
                return GenericResponse(status="error", message="Không có nội dung để làm sạch")

            cleaned = await noise_cleaner.clean(content, mode="aggressive")
            return GenericResponse(status="success", data={"content": cleaned})
        except Exception as e:
            logger.error(f"[ContentController] Viral Clean Error: {e}")
            return GenericResponse(status="error", message=str(e))
