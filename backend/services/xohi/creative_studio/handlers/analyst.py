import logging
import hashlib
import copy
from datetime import datetime, timezone
from typing import Dict, Optional, List, Union
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
    def get_gold_val(self, key: str, fallback: object = None, *args, **kwargs) -> object:
        # [ELITE BUGFIX] Chấp nhận variadic arguments để tránh lỗi TypeError (takes 2 positional but 3 given)
        return self.gold_metadata.get(key, fallback)

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
        
        cached = cache.get(category)
        if campaign_id and not force and cached and cached.get("hash") == content_hash:
            # [ELITE R2026.9] Auto-upgrade if cache is legacy (missing Neural branding)
            cached_data = cached.get("data", {})
            cached_logs = cached_data.get("logs", [])
            has_neural_vibe = any("NEURAL" in str(l).upper() for l in cached_logs)
            
            if has_neural_vibe:
                logger.info(f"♻️ [AnalystHandler] Using cached {category} for {campaign_id}")
                return GenericResponse(status="success", data=cached_data)
            else:
                logger.info(f"🧬 [AnalystHandler] Detected legacy cache for {category}. Upgrading to Neural Engine...")

        try:
            # TIER 1: THE BUTLER (Sync Cache Retrieval)
            # If we have a valid cache hit, return immediately (<100ms)
            if campaign_id and not force and cached and cached.get("hash") == content_hash:
                return GenericResponse(status="success", data=cached.get("data", {}))

            # TIER 2: THE BRAIN (Async Execution)
            # Rule R2.2: AI-heavy tasks MUST be offloaded to the background worker.
            if campaign_id and campaign_repo and not isinstance(campaign, AdHocContent):
                analyzer = analyzer_class()
                
                # Payload construction for the worker
                # We pass the dynamic request schema if defined
                payload = {"campaign_id": campaign_id, "force": force}
                
                # Use inherited Heritage Backdoor to enqueue task
                task_id = await analyzer.enqueue_chat(
                    request_data=payload,
                    session_id=str(getattr(campaign, "id", "session"))
                )

                # Return 202 Accepted (Standard Elite V2.2 Protocol)
                return GenericResponse(
                    status="accepted", 
                    message="Neural Engine đang xử lý yêu cầu. Kết quả sẽ được cập nhật tự động.",
                    data={"task_id": task_id, "category": category}
                )
            
            # Ad-hoc Fallback (Sync): Only for anonymous content analysis (No DB)
            analyzer = analyzer_class()
            result = await analyzer.analyze(campaign, force=force)
            return GenericResponse(status="success", data=result.model_dump())

        except Exception as e:
            logger.error(f"[AnalystHandler] {category} analysis failed: {str(e)}", exc_info=True)
            return GenericResponse(status="error", message=str(e))

    async def analyze_copyright(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        logger.info(f"🕵️ [AnalystHandler] Neural Copyright Engine initiating for campaign: {campaign_id}")
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        return await self._run_analysis(campaign_id, campaign_repo, PlagiarismCop, "copyright", force, raw_content=raw_content, raw_topic=raw_topic)

    async def analyze_seo(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        logger.info(f"📡 [AnalystHandler] Neural SEO Engine initiating for campaign: {campaign_id}")
        from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer
        return await self._run_analysis(campaign_id, campaign_repo, SeoAnalyzer, "seo", force, raw_content=raw_content, raw_topic=raw_topic)

    async def analyze_ai_inspect(self, campaign_id: Optional[str], campaign_repo: Optional[ContentCampaignRepository], force: bool = False, raw_content: Optional[str] = None, raw_topic: Optional[str] = None) -> GenericResponse:
        logger.info(f"🧠 [AnalystHandler] Neural AI-Ready Inspector initiating for campaign: {campaign_id}")
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        return await self._run_analysis(campaign_id, campaign_repo, AiInspector, "ai_inspect", force, raw_content=raw_content, raw_topic=raw_topic)

    async def auto_fix(self, campaign_id: str, data: Dict[str, object], campaign_repo: ContentCampaignRepository) -> GenericResponse:
        # Auto-fix still requires a campaign for now due to complexity of snippet replacement
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector, AutoFixRequest
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return GenericResponse(status="error", message="Campaign not found")
        if not campaign.draft_content: return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")
        try:
            result = await AiInspector().auto_fix(campaign, AutoFixRequest(**data))
            return GenericResponse(status="success", data=result.model_dump())
        except Exception as e: return GenericResponse(status="error", message=str(e))

    async def bulk_fix(self, campaign_id: Optional[str], data: Dict[str, object], campaign_repo: Optional[ContentCampaignRepository], raw_content: Optional[str] = None) -> GenericResponse:
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
                msg = f"📡 Đang thực địa Top 10 Google cho chủ đề: '{topic}'..."
                logs.append(msg)
                if campaign_id: await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 1, "message": msg, "status": "PROCESSING"})
                
                search_context = await self.orchestrator.discovery.search(topic)
                
                # 3. AI STRATEGIC SYNTHESIS
                msg = "🧠 Đang giải mã chiến lược đối thủ bằng Neural Engine..."
                logs.append(msg)
                if campaign_id: await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 1, "message": msg, "status": "PROCESSING"})
                
                scout_prompt = f"""[ROLE] SENIOR CONTENT STRATEGIST — XoHi Intelligence 2026
Nhiệm vụ: Phân tích sâu 10 đối thủ hàng đầu và lập bản trình báo chiến thuật nội dung.

[DỮ LIỆU TRINH SÁT TỪ GOOGLE]
{search_context}

[YÊU CẦU ĐẦU RA — JSON]
Trả về một `ScoutReport` (Pydantic Model) bao gồm:
1. `headlines`: Danh sách 6-10 tiêu đề gợi ý đa kênh.
2. `semantic_keywords`: 8-12 từ khóa Semantic/LSI quan trọng nhất để "đánh chặn" SEO.
3. `strategic_analysis`: Bản TRÌNH BÁO CHIẾN LƯỢC (Markdown) cực kỳ chuyên sâu.
4. `ground_truth_summary`: Tóm tắt ngắn gọn bối cảnh thực tế trinh sát được.
"""
                agent = Agent(output_type=ScoutReport, system_prompt=scout_prompt)
                response = await trinity_bridge.run(agent=agent, prompt=f"Tiến hành trình báo chiến lược cho chủ đề: {topic}", role="brain")
                
                report = response.data if hasattr(response, 'data') else response.output
                
                # 4. PERSIST TO CACHE
                msg = "💾 Đang lưu trữ kết quả trinh sát vào Neural Vault..."
                logs.append(msg)
                if campaign_id: await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 1, "message": msg, "status": "PROCESSING"})
                
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
