import logging
import hashlib
import copy
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from sqlalchemy.orm.attributes import flag_modified

from backend.database.repositories import ContentCampaignRepository
from backend.models.schemas import GenericResponse

logger = logging.getLogger("api-gateway")

class AdHocContent:
    """Shim to allow AI analyzers to process content without a full DB campaign record."""
    def __init__(self, content: str, topic: str = None, user_id: str = "system", id: str = "adhoc"):
        self.draft_content = content
        self.gold_metadata = {"topic": topic, "primary_keyword": topic}
        self.user_id = user_id
        self.id = id
        self.unique_score = 0.0
    def get_gold_val(self, key): return self.gold_metadata.get(key)

class AnalystHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def _run_analysis(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], analyzer_class, category: str, force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        if campaign_id and campaign_repo:
            campaign = await campaign_repo.get(campaign_id)
            if not campaign: return GenericResponse(status="error", message="Campaign not found")
        else:
            if not raw_content: return GenericResponse(status="error", message="No content provided for ad-hoc analysis")
            campaign = AdHocContent(content=raw_content, topic=raw_topic)

        if not campaign.draft_content: return GenericResponse(status="error", message="Chưa có nội dung để phân tích.")

        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        
        # Caching is only supported for persistent campaigns
        gold = getattr(campaign, "gold_metadata", {}) or {}
        cache = gold.get("analysis_cache", {}) if isinstance(gold, dict) else {}

        if campaign_id and not force and cache.get(category, {}).get("hash") == content_hash:
            return GenericResponse(status="success", data=cache[category]["data"])

        try:
            analyzer = analyzer_class()
            result = await analyzer.analyze(campaign)
            result_data = result.model_dump()

            # If it's a persistent campaign, update metrics and cache
            if campaign_id and campaign_repo and not isinstance(campaign, AdHocContent):
                cache[category] = {"hash": content_hash, "data": result_data, "at": datetime.now(timezone.utc).isoformat()}
                metrics = gold.get("analysis_metrics", {})
                
                if category == "copyright":
                    metrics["unique_score"] = result.uniqueness_score
                    metrics["copyright_risk"] = result.risk_level
                    campaign.unique_score = result.uniqueness_score
                elif category == "seo":
                    metrics["seo_score"] = result.total_score
                    metrics["seo_grade"] = result.grade
                elif category == "ai_inspect":
                    metrics["ai_ready_score"] = result.geo_score
                
                metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()
                
                new_gold = copy.deepcopy(gold)
                new_gold["analysis_cache"] = cache
                new_gold["analysis_metrics"] = metrics
                campaign.gold_metadata = new_gold
                flag_modified(campaign, "gold_metadata")
                
                await campaign_repo.update(campaign)
                if hasattr(campaign_repo, "session"): await campaign_repo.session.commit()
            
            return GenericResponse(status="success", data=result_data)
        except Exception as e:
            logger.error(f"[AnalystHandler] {category} analysis failed: {str(e)}", exc_info=True)
            return GenericResponse(status="error", message=str(e))

    async def analyze_copyright(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None) -> GenericResponse:
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        return await self._run_analysis(campaign_id, campaign_repo, PlagiarismCop, "copyright", force, raw_content=raw_content)

    async def analyze_seo(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer
        return await self._run_analysis(campaign_id, campaign_repo, SeoAnalyzer, "seo", force, raw_content=raw_content, raw_topic=raw_topic)

    async def analyze_ai_inspect(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None) -> GenericResponse:
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        return await self._run_analysis(campaign_id, campaign_repo, AiInspector, "ai_inspect", force, raw_content=raw_content)

    async def auto_fix(self, campaign_id: str, data: Dict[str, Any], campaign_repo: ContentCampaignRepository) -> GenericResponse:
        # Auto-fix still requires a campaign for now due to complexity of snippet replacement
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector, AutoFixRequest
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return GenericResponse(status="error", message="Campaign not found")
        if not campaign.draft_content: return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")
        try:
            result = await AiInspector().auto_fix(campaign, AutoFixRequest(**data))
            return GenericResponse(status="success", data=result.model_dump())
        except Exception as e: return GenericResponse(status="error", message=str(e))

    async def bulk_fix(self, campaign_id: Optional[str], data: Dict[str, Any], campaign_repo: Optional[ContentCampaignRepository], raw_content: Optional[str] = None) -> GenericResponse:
        from backend.services.xohi.creative_studio.models.schemas import BulkFixRequest
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        
        if campaign_id and campaign_repo:
            campaign = await campaign_repo.get(campaign_id)
            if not campaign: return GenericResponse(status="error", message="Campaign not found")
        else:
            campaign = AdHocContent(content=raw_content or data.get("content", ""), topic=data.get("topic"))

        if not campaign.draft_content: return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")
        
        try:
            fix_req = BulkFixRequest(**data)
            op = PlagiarismCop() if fix_req.category == "copyright" else AiInspector()
            res = await op.bulk_fix(campaign, fix_req)
            
            if res.new_content and res.new_content != campaign.draft_content:
                if campaign_id and campaign_repo and not isinstance(campaign, AdHocContent):
                    campaign.draft_content = res.new_content
                    flag_modified(campaign, "draft_content")
                    await campaign_repo.update(campaign)
                    if hasattr(campaign_repo, "session"): await campaign_repo.session.commit()
            return GenericResponse(status="success", data=res.model_dump())
        except Exception as e: return GenericResponse(status="error", message=str(e))

    async def enrich(self, campaign_id: str, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        from backend.services.xohi.creative_studio.operatives.content_enricher import enricher
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return GenericResponse(status="error", message="Campaign not found")
        if not campaign.draft_content: return GenericResponse(status="error", message="Chưa có nội dung để enrich.")
        try:
            res = await enricher.enrich(campaign)
            if res.new_content and res.new_content != campaign.draft_content:
                campaign.draft_content = res.new_content
                flag_modified(campaign, "draft_content")
                await campaign_repo.update(campaign)
                if hasattr(campaign_repo, "session"): await campaign_repo.session.commit()
            return GenericResponse(status="success", data=res.model_dump())
        except Exception as e: return GenericResponse(status="error", message=str(e))
