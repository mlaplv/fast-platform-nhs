import logging
from typing import List, Dict, Any, Union, Optional
from uuid import UUID

logger = logging.getLogger(__name__)
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

    @post("/campaigns/{campaign_id:uuid}/analyze/copyright")
    async def analyze_copyright(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        On-demand: ĐẠO VĂN & BẢN QUYỀN — 2026 Edition.
        Dùng Google Search + Gemini AI để kiểm tra ngữ nghĩa (không phải so ký tự).
        """
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}
        if not campaign.draft_content:
            return {"status": "error", "message": "Chưa có nội dung để kiểm tra."}
        cop = PlagiarismCop()
        result = await cop.analyze(campaign)
        return {"status": "success", "data": result.model_dump()}

    @post("/campaigns/{campaign_id:uuid}/analyze/seo")
    async def analyze_seo(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        On-demand: PHÂN TÍCH SEO 2026 — E-E-A-T, Entity Coverage, AI-Naturalness, Featured Snippet.
        """
        from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer
        campaign = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}
        if not campaign.draft_content:
            return {"status": "error", "message": "Chưa có nội dung để phân tích."}
        analyzer = SeoAnalyzer()
        result = await analyzer.analyze(campaign)
        return {"status": "success", "data": result.model_dump()}

    @post("/campaigns/{campaign_id:uuid}/analyze/ai-inspect")
    async def analyze_ai_readiness(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
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
            return {"status": "error", "message": "Campaign not found"}
        if not campaign.draft_content:
            return {"status": "error", "message": "Chưa có nội dung để phân tích AI Readiness."}
        
        inspector = AiInspector()
        try:
            result = await inspector.analyze(campaign)
            logger.info(f"AI Inspector output: {result.model_dump_json(indent=2)}")
            return {"status": "success", "data": result.model_dump()}
        except Exception as e:
            logger.error(f"AI Inspector error: {e}")
            return {"status": "error", "message": str(e)}
    @post("/campaigns/{campaign_id:uuid}/analyze/auto-fix")
    async def analyze_auto_fix(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        On-Demand Surgical Auto-Fix (Contextual Local Rewrite)
        """
        try:
            from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector, AutoFixRequest
            campaign = await campaign_repo.get(str(campaign_id))
            if not campaign:
                return {"status": "error", "message": "Campaign not found"}
            if not campaign.draft_content:
                return {"status": "error", "message": "Chưa có nội dung để biên tập."}
            
            inspector = AiInspector()
            data = await request.json()
            fix_req = AutoFixRequest(**data)
            
            result = await inspector.auto_fix(campaign, fix_req)
            return {"status": "success", "data": result.model_dump()}
        except Exception as e:
            logger.error(f"Auto-Fix error: {e}")
            return {"status": "error", "message": str(e)}
