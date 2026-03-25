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
            # Pass force flag to analyzer if it supports it (to bypass AI exhaustion cache)
            result = await analyzer.analyze(campaign, force=force)
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

    async def analyze_copyright(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        logger.info(f"💓 [AnalystHandler] Hammering copyright check for {campaign_id}")
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        return await self._run_analysis(campaign_id, campaign_repo, PlagiarismCop, "copyright", force, raw_content=raw_content, raw_topic=raw_topic)

    async def analyze_seo(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer
        return await self._run_analysis(campaign_id, campaign_repo, SeoAnalyzer, "seo", force, raw_content=raw_content, raw_topic=raw_topic)

    async def analyze_ai_inspect(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        return await self._run_analysis(campaign_id, campaign_repo, AiInspector, "ai_inspect", force, raw_content=raw_content, raw_topic=raw_topic)

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

    async def scout(self, topic: str, campaign_id: Optional[str] = None) -> GenericResponse:
        """
        [CNS V62.2] High-IQ Neural Scout with Smart Caching.
        Performs Google Search recon + AI Strategic Synthesis (ADS vs TOP 10).
        Persists results for 24h to optimize API costs and latency.
        """
        logger.info(f"🕵️ [AnalystHandler] Neural Scout initiating for topic: {topic}")
        from backend.services.xohi.creative_studio.models.schemas import ScoutReport
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
        from backend.database.alchemy_config import alchemy_config
        from backend.database.repositories import ContentScoutRepository
        from backend.database.models import ContentScout, ContentCampaign
        from pydantic_ai import Agent
        from datetime import datetime, timedelta, timezone
        import uuid

        logs = [f"🚀 Khởi động Neural Scout Engine cho tiêu điểm: '{topic}'..."]
        session_maker = alchemy_config.create_session_maker()
        
        async with session_maker() as session:
            scout_repo = ContentScoutRepository(session=session)
            
            # 1. SMART CACHE CHECK (Elite Standard)
            existing = None
            try:
                logs.append("🔍 Đang kiểm tra Neural Vault cho 24h qua...")
                existing = await scout_repo.get_one_or_none(topic=topic)
                
                if existing:
                    now = datetime.now(timezone.utc)
                    exp = existing.expires_at
                    if exp.tzinfo is None: exp = exp.replace(tzinfo=timezone.utc)
                    
                    if exp > now:
                        logs.append("💡 [CACHE HIT] Tìm thấy báo cáo trinh sát còn hiệu lực. Đang truy xuất...")
                        report_data = existing.report_data
                        
                        # CNS V62.4: Atomic Sync to Campaign if provided
                        if campaign_id:
                            campaign_repo = ContentCampaignRepository(session=session)
                            campaign = await campaign_repo.get(campaign_id)
                            if campaign:
                                topic_data = dict(campaign.topic_data or {})
                                topic_data["scout_report"] = report_data
                                campaign.topic_data = topic_data
                                flag_modified(campaign, "topic_data")
                                
                                # CNS V62.5: UI Persistence - Auto-expand scout section
                                gold = dict(campaign.gold_metadata or {})
                                if "creation_config" not in gold: gold["creation_config"] = {}
                                gold["creation_config"]["scouting_active"] = True
                                campaign.gold_metadata = gold
                                flag_modified(campaign, "gold_metadata")
                                
                                await campaign_repo.update(campaign)
                                await session.commit() # CNS V62.5: Ensure sync is persisted to DB
                                logs.append(f"🔗 [SYNC] Đã tự động cập nhật báo cáo vào chiến dịch {campaign_id} (Auto-expand enabled).")

                        report = ScoutReport(**report_data)
                        report.logs = logs + ["✅ Truy xuất dữ liệu từ Neural Cache thành công."]
                        return GenericResponse(status="success", data=report.model_dump())
                    else:
                        logs.append("⚠️ Dữ liệu trinh sát đã quá hạn (TTL > 24h). Tiến hành trinh sát mới...")
                else:
                    logs.append("📡 Không tìm thấy dữ liệu trong Cache. Tiến hành thực địa...")
            except Exception as e:
                logger.warning(f"Cache check failed: {str(e)}")
                logs.append("⚠️ Lỗi Cache Controller. Tiếp tục trinh sát trực tiếp...")

            try:
                # 2. PROCEED WITH RECON
                logs.append("📡 Đang trinh sát Top 10 Google SERP & ADS fragments...")
                search_context = await self.orchestrator.discovery.search(topic)
                
                # 3. AI STRATEGIC SYNTHESIS
                logs.append("🧠 Đang giải mã chiến lược đối thủ bằng Neural Engine...")
                
                scout_prompt = f"""[ROLE] SENIOR CONTENT STRATEGIST — XoHi Intelligence 2026
Nhiệm vụ: Phân tích sâu 10 đối thủ hàng đầu và lập bản trình báo chiến thuật nội dung.

[DỮ LIỆU TRINH SÁT TỪ GOOGLE]
{search_context}

[YÊU CẦU ĐẦU RA — JSON]
Trả về một `ScoutReport` (Pydantic Model) bao gồm:
1. `headlines`: Danh sách 6-10 tiêu đề gợi ý đa kênh.
   - Phân loại rõ: ADS (Click-bait chất lượng cao), TOP_10 (SEO chuẩn), AI_AUGMENTED (Sáng tạo đột phá).
2. `semantic_keywords`: 8-12 từ khóa Semantic/LSI quan trọng nhất để "đánh chặn" SEO.
3. `strategic_analysis`: Bản TRÌNH BÁO CHIẾN LƯỢC (Markdown) cực kỳ chuyên sâu bao gồm:
   - **Search Intent Decoding**: Giải mã mục đích thực sự và "nỗi đau" của người dùng.
   - **Competitor Gap Analysis**: Chỉ ra những mảng nội dung/insight mà đối thủ đang bỏ trống hoặc làm hời hợt.
   - **Elite Execution Roadmap**: Công thức cụ thể để bài viết đạt Information Gain cao nhất, vượt xa Top 1.
4. `ground_truth_summary`: Tóm tắt ngắn gọn bối cảnh thực tế trinh sát được.

CHÚ Ý: Bản trình báo chiến lược phải mang tính THAM KHẢO CHIẾN THUẬT CAO (Actionable Intelligence), không được viết chung chung.
"""
                agent = Agent(output_type=ScoutReport, system_prompt=scout_prompt)
                response = await trinity_bridge.run(agent=agent, prompt=f"Tiến hành trình báo chiến lược cho chủ đề: {topic}", role="brain")
                
                report = response.data if hasattr(response, 'data') else response.output
                
                # 4. PERSIST TO CACHE
                logs.append("💾 Đang lưu trữ kết quả trinh sát vào Neural Vault (24h)...")
                try:
                    if existing:
                        await scout_repo.delete(existing.id)
                    
                    new_scout = ContentScout(
                        id=str(uuid.uuid4()),
                        topic=topic,
                        report_data=report.model_dump(),
                        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                    )
                    await scout_repo.add(new_scout)
                    
                    # CNS V62.4: Atomic Sync to Campaign for fresh results
                    if campaign_id:
                        campaign_repo = ContentCampaignRepository(session=session)
                        campaign = await campaign_repo.get(campaign_id)
                        if campaign:
                            topic_data = dict(campaign.topic_data or {})
                            topic_data["scout_report"] = report.model_dump()
                            campaign.topic_data = topic_data
                            flag_modified(campaign, "topic_data")
                            
                            # CNS V62.5: UI Persistence - Auto-expand scout section
                            gold = dict(campaign.gold_metadata or {})
                            if "creation_config" not in gold: gold["creation_config"] = {}
                            gold["creation_config"]["scouting_active"] = True
                            campaign.gold_metadata = gold
                            flag_modified(campaign, "gold_metadata")
                            
                            await campaign_repo.update(campaign)
                            logs.append(f"🔗 [SYNC] Đã lưu báo cáo mới vào chiến dịch {campaign_id} (Auto-expand enabled).")
                    
                    await session.commit()
                except Exception as db_e:
                    logger.error(f"Failed to cache scout: {str(db_e)}")
                    logs.append("⚠️ Không thể lưu Cache vào DB, nhưng dữ liệu vẫn ổn.")

                report.logs = logs + ["✅ Trinh sát hoàn tất. Báo cáo chiến lược 'Elite' đã sẵn sàng."]
                return GenericResponse(status="success", data=report.model_dump())
                
            except Exception as e:
                logger.error(f"[AnalystHandler] Scout failed: {str(e)}", exc_info=True)
                return GenericResponse(status="error", message=f"Neural Scout Error: {str(e)}")
