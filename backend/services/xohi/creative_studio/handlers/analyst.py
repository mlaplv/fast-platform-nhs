import asyncio
import logging
import hashlib
import copy
from datetime import datetime, timezone
from typing import Dict, Optional, List, Union
from sqlalchemy.orm.attributes import flag_modified

from backend.database.repositories import ContentCampaignRepository
from backend.models.schemas import GenericResponse
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

# ──────────────────────────────────────────────────────────────────────────────
# SCOUT CONFIG — Elite V2.2 Timeout Constants
# ──────────────────────────────────────────────────────────────────────────────
_SCOUT_SEARCH_TIMEOUT = 8.0   # Google Search must return within 8s
_SCOUT_AI_TIMEOUT     = 80.0  # AI synthesis hard ceiling (below Stall Detector 100s)
_SCOUT_AGENT = None           # Lazy singleton — avoid recreating Agent on every call

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

    async def auto_fix_adhoc(self, content: str, target_snippet: str, annotation_type: str, error_message: str, topic: Optional[str] = None) -> GenericResponse:
        """CNS V86.5: Ad-hoc surgical fix — không cần campaign. Dùng cho ProductForm/NewsForm."""
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector, AutoFixRequest
        if not content or not target_snippet:
            return GenericResponse(status="error", message="Thiếu content hoặc target_snippet.")
        campaign = AdHocContent(content=content, topic=topic or "")
        try:
            req = AutoFixRequest(text=target_snippet, message=error_message)
            result = await AiInspector().auto_fix(campaign, req)
            new_text = result.new_text if result.new_text and result.new_text != target_snippet else None
            return GenericResponse(status="success", data={"new_text": new_text})
        except Exception as e:
            logger.error(f"[AnalystHandler] ad-hoc auto_fix failed: {e}", exc_info=True)
            return GenericResponse(status="error", message=str(e))

    async def stream_auto_fix(
        self, content: str, target_snippet: str, error_message: str, topic: str = ""
    ):
        """
        CNS V87.0: SSE streaming auto-fix — dùng text-streaming Agent để typewriter effect.
        Yields SSE lines: data: {"chunk": "..."} hoặc data: {"done": true, "full": "..."}
        CLAUDE.md: Dispose resources sau khi xong, cấm block async.
        """
        import json
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        stream_prompt = (
            f"[BÀI VIẾT - CHỦ ĐỀ: {topic}]\n{content[:5000]}\n\n"
            f"[ĐOẠN CẦN SỬA]\n\"{target_snippet}\"\n\n"
            f"[LỖI CẦN KHẮC PHỤC]\n{error_message}\n\n"
            "Hãy viết lại đoạn văn trên. Chỉ trả về đoạn văn đã sửa, không giải thích."
        )
        stream_agent: Agent[None, str] = Agent(
            output_type=str,
            system_prompt=(
                "Bạn là Neural Surgeon. Viết lại đoạn văn theo yêu cầu. "
                "Sắc bén, thêm số liệu thực, giữ nguyên HTML tag. Chỉ trả về đoạn văn đã sửa."
            ),
            retries=1
        )

        full_text = ""
        try:
            word_count = len(content.split())
            yield f"data: {json.dumps({'chunk': f'[NFC] Normalizing {word_count} words for surgical alignment...\\n'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'chunk': '[JUDGE] Decoding error context & initiating Neural Surgeon...\\n'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'chunk': '--- [REASONING START] ---\\n'}, ensure_ascii=False)}\n\n"
            async with trinity_bridge.run_stream(stream_agent, stream_prompt, role="fast") as stream:
                async for chunk in stream.stream_text(delta=True):
                    full_text += chunk
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'full': full_text}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            logger.error(f"[AnalystHandler] stream_auto_fix error: {exc}", exc_info=True)
            yield f"data: {json.dumps({'error': str(exc)[:100]})}\n\n"

    async def surgeon_boost(
        self, content: str, topic: str = "", campaign_id: Optional[str] = None,
        campaign_repo: Optional[ContentCampaignRepository] = None
    ) -> GenericResponse:
        """
        CNS V87.0: Surgeon Boost — phẫu thuật content, trả về ContentPatch list.
        Hỗ trợ cả ad-hoc (content trực tiếp) và campaign mode.
        """
        from backend.services.xohi.creative_studio.operatives.surgeon_booster import run_surgeon_boost

        raw_content = content
        if campaign_id and campaign_repo and not raw_content:
            campaign = await campaign_repo.get(campaign_id)
            if not campaign:
                return GenericResponse(status="error", message="Campaign not found")
            raw_content = campaign.draft_content or ""

        if not raw_content:
            return GenericResponse(status="error", message="Chưa có nội dung để phẫu thuật.")

        try:
            result = await run_surgeon_boost(raw_content, topic)
            return GenericResponse(status="success", data=result.model_dump())
        except Exception as exc:
            logger.error(f"[AnalystHandler] surgeon_boost failed: {exc}", exc_info=True)
            return GenericResponse(status="error", message=str(exc))

    async def save_analysis_report(
        self, campaign_id: str, campaign_repo: ContentCampaignRepository,
        report_type: str, data: Dict[str, object]
    ) -> GenericResponse:
        """
        CNS V87.0: Lưu kết quả phân tích vào JSONB column analysis_report.
        Hỗ trợ dọn dẹp và gom nhóm dữ liệu để Dashboard load nhanh.
        """
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        # Khởi tạo report nếu chưa có
        report = dict(campaign.analysis_report or {})
        
        # Cập nhật slot dữ liệu tương ứng (copyright, seo, ai_inspect, surgeon)
        report[report_type] = {
            "data": data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "version": "V87.0"
        }

        try:
            await campaign_repo.update(campaign_id, {"analysis_report": report})
            logger.info(f"[AnalystHandler] Saved {report_type} report for campaign {campaign_id}")
            return GenericResponse(status="success", message=f"Đã lưu báo cáo {report_type}")
        except Exception as exc:
            logger.error(f"[AnalystHandler] Failed to save report: {exc}", exc_info=True)
            return GenericResponse(status="error", message=str(exc))

    async def bulk_fix(self, campaign_id: Optional[str], data: Dict[str, object], campaign_repo: Optional[ContentCampaignRepository], raw_content: Optional[str] = None) -> GenericResponse:
        from backend.services.xohi.creative_studio.models.schemas import BulkFixRequest
        from backend.services.xohi.creative_studio.operatives.ai_inspector import AiInspector
        from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
        from backend.services.xohi.creative_studio.operatives.seo_analyzer import SeoAnalyzer
        
        if campaign_id and campaign_repo:
            campaign = await campaign_repo.get(campaign_id)
            if not campaign: return GenericResponse(status="error", message="Campaign not found")
        else:
            campaign = AdHocContent(content=raw_content or data.get("content", ""), topic=data.get("topic"))

        if not campaign.draft_content: return GenericResponse(status="error", message="Chưa có nội dung để biên tập.")
        
        try:
            fix_req = BulkFixRequest(**data)
            if fix_req.category == "copyright":
                op = PlagiarismCop()
            elif fix_req.category == "seo":
                op = SeoAnalyzer()
            else:
                op = AiInspector()
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
        [CNS V62.3 — ROOT CAUSE FIX] High-IQ Neural Scout with Smart Caching.
        Performs Google Search recon + AI Strategic Synthesis.
        Persists results for 24h to optimize API costs and latency.

        FIX HISTORY:
        - [R.C.1] Bọc discovery.search() với asyncio.wait_for(8s) để tránh treo event loop.
        - [R.C.2] Bọc trinity_bridge.run() với asyncio.wait_for(80s) + bắt AIConfigurationError.
        - [R.C.3] Dùng lazy singleton Agent thay vì tạo mới mỗi lần gọi.
        - [R.C.4] Graceful degraded ScoutReport khi AI fail — không crash API.
        """
        global _SCOUT_AGENT
        logger.info(f"🕵️ [AnalystHandler] Neural Scout initiating for topic: {topic}")
        from backend.services.xohi.creative_studio.models.schemas import ScoutReport, ScoutHeadline
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge, AIConfigurationError
        from backend.database.alchemy_config import alchemy_config
        from backend.database.repositories import ContentScoutRepository
        from backend.database.models import ContentScout, ContentCampaign
        from pydantic_ai import Agent
        from datetime import datetime, timedelta, timezone
        import uuid

        logs: List[str] = [f"🚀 Khởi động Neural Scout Engine cho tiêu điểm: '{topic}'..."]
        session_maker = alchemy_config.create_session_maker()

        async with session_maker() as session:
            scout_repo = ContentScoutRepository(session=session)

            # ── 1. SMART CACHE CHECK ──────────────────────────────────────────
            existing = None
            try:
                logs.append("🔍 Đang kiểm tra Neural Vault cho 24h qua...")
                existing = await scout_repo.get_one_or_none(topic=topic)

                if existing:
                    now = datetime.now(timezone.utc)
                    exp = existing.expires_at
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=timezone.utc)

                    if exp > now:
                        logs.append("💡 [CACHE HIT] Tìm thấy báo cáo trinh sát còn hiệu lực. Đang truy xuất...")
                        report_data = existing.report_data

                        if campaign_id:
                            campaign_repo = ContentCampaignRepository(session=session)
                            campaign = await campaign_repo.get(campaign_id)
                            if campaign:
                                topic_data = dict(campaign.topic_data or {})
                                topic_data["scout_report"] = report_data
                                campaign.topic_data = topic_data
                                flag_modified(campaign, "topic_data")
                                gold = dict(campaign.gold_metadata or {})
                                if "creation_config" not in gold:
                                    gold["creation_config"] = {}
                                gold["creation_config"]["scouting_active"] = True
                                campaign.gold_metadata = gold
                                flag_modified(campaign, "gold_metadata")
                                await campaign_repo.update(campaign)
                                await session.commit()
                                logs.append(f"🔗 [SYNC] Đã cập nhật báo cáo vào chiến dịch {campaign_id}.")

                        report = ScoutReport(**report_data)
                        report.logs = logs + ["✅ Truy xuất từ Neural Cache thành công."]
                        return GenericResponse(status="success", data=report.model_dump())
                    else:
                        logs.append("⚠️ Cache quá hạn (TTL > 24h). Tiến hành trinh sát mới...")
                else:
                    logs.append("📡 Cache miss. Tiến hành thực địa...")
            except Exception as cache_err:
                logger.warning(f"[Scout] Cache check failed: {cache_err}")
                logs.append("⚠️ Lỗi Cache. Tiếp tục trinh sát trực tiếp...")

            # ── 2. GOOGLE SEARCH RECON (R.C.1: Timeout Guard) ───────────────
            search_context = ""
            try:
                msg = f"📡 Đang thực địa Top 10 Google cho chủ đề: '{topic}'..."
                logs.append(msg)
                if campaign_id:
                    await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 1, "message": msg, "status": "PROCESSING"})

                # R.C.1 FIX: Strict 8s timeout — Google không trả lời thì bỏ qua, không treo event loop
                search_context = await asyncio.wait_for(
                    self.orchestrator.discovery.search(topic),
                    timeout=_SCOUT_SEARCH_TIMEOUT
                )
                logs.append(f"✅ Trinh sát Google hoàn tất. Đã lấy được context ngữ cảnh.")
            except asyncio.TimeoutError:
                logger.warning(f"[Scout] Google Search timed out after {_SCOUT_SEARCH_TIMEOUT}s. Proceeding with empty context.")
                logs.append(f"⚠️ Google Search timeout ({_SCOUT_SEARCH_TIMEOUT}s). AI sẽ tổng hợp từ dữ liệu nội bộ.")
                search_context = "(Google Search timed out — AI will rely on training knowledge)"
            except Exception as search_err:
                logger.warning(f"[Scout] Google Search error: {search_err}")
                logs.append(f"⚠️ Lỗi Google Search: {str(search_err)[:80]}. Tiếp tục với AI...")
                search_context = f"(Search error: {str(search_err)[:200]})"

            # ── 3. AI STRATEGIC SYNTHESIS (R.C.2: Timeout + Error Guard) ────
            msg = "🧠 Đang giải mã chiến lược đối thủ bằng Neural Engine..."
            logs.append(msg)
            if campaign_id:
                await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 1, "message": msg, "status": "PROCESSING"})

            report: Optional[ScoutReport] = None
            try:
                scout_prompt = (
                    "[ROLE] SENIOR CONTENT STRATEGIST — XoHi Intelligence 2026\n"
                    "Nhiệm vụ: Phân tích dữ liệu trinh sát và lập bản trình báo chiến thuật nội dung.\n\n"
                    "[DỮ LIỆU TRINH SÁT TỪ GOOGLE]\n"
                    f"{search_context}\n\n"
                    "[YÊU CẦU ĐẦU RA — JSON]\n"
                    "Trả về ScoutReport với: topic, headlines (List[ScoutHeadline]), "
                    "semantic_keywords (List[str]), strategic_analysis (str), ground_truth_summary (str)."
                )

                # R.C.3 FIX: Lazy singleton Agent — tránh khởi tạo nặng mỗi lần gọi
                if _SCOUT_AGENT is None:
                    _SCOUT_AGENT = Agent(output_type=ScoutReport, system_prompt=scout_prompt)
                else:
                    # Override system_prompt với topic mới (immutable override via agent.override)
                    pass

                # R.C.2 FIX: Hard timeout 80s, giải phóng concurrency guard đúng thứ tự
                response = await asyncio.wait_for(
                    trinity_bridge.run(
                        agent=_SCOUT_AGENT,
                        prompt=f"Tiến hành trình báo chiến lược cho chủ đề: {topic}\n\n[CONTEXT]\n{search_context[:3000]}",
                        role="brain",
                        system_prompt=scout_prompt,
                    ),
                    timeout=_SCOUT_AI_TIMEOUT
                )
                report = response if isinstance(response, ScoutReport) else ScoutReport(**response) if isinstance(response, dict) else None
                if report is None:
                    raise ValueError(f"Unexpected AI response type: {type(response)}")
                logs.append("✅ Neural Engine phân tích xong.")

            except asyncio.TimeoutError:
                logger.error(f"[Scout] AI synthesis timed out after {_SCOUT_AI_TIMEOUT}s for topic: '{topic}'")
                logs.append(f"⚠️ AI timeout ({_SCOUT_AI_TIMEOUT}s). Kích hoạt chế độ Degraded Scout...")

            except AIConfigurationError as ai_err:
                logger.error(f"[Scout] AIConfigurationError: {ai_err}")
                logs.append(f"⚠️ AI không khả dụng ({str(ai_err)[:80]}). Kích hoạt Degraded Scout...")

            except Exception as ai_err:
                logger.error(f"[Scout] AI synthesis error: {ai_err}", exc_info=True)
                logs.append(f"⚠️ Lỗi AI: {str(ai_err)[:80]}. Kích hoạt Degraded Scout...")

            # R.C.4 FIX: Graceful degraded report khi AI fail — không để API crash
            if report is None:
                report = ScoutReport(
                    topic=topic,
                    headlines=[ScoutHeadline(title=f"Nội dung về: {topic}", type="AI_AUGMENTED")],
                    semantic_keywords=[topic],
                    strategic_analysis=(
                        f"## ⚠️ Degraded Mode\n\nAI Engine tạm thời không khả dụng. "
                        f"Dữ liệu Google đã được trinh sát:\n\n{search_context[:500]}"
                    ),
                    ground_truth_summary=search_context[:200] if search_context else "Không có dữ liệu.",
                    logs=logs,
                )
                logs.append("🛡️ Đã xuất báo cáo ở chế độ Degraded (Không có AI). Thử lại sau để có full report.")

            # ── 4. PERSIST TO CACHE ───────────────────────────────────────────
            msg = "💾 Đang lưu trữ kết quả vào Neural Vault..."
            logs.append(msg)
            if campaign_id:
                await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 1, "message": msg, "status": "PROCESSING"})

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

                if campaign_id:
                    campaign_repo = ContentCampaignRepository(session=session)
                    campaign = await campaign_repo.get(campaign_id)
                    if campaign:
                        topic_data = dict(campaign.topic_data or {})
                        topic_data["scout_report"] = report.model_dump()
                        campaign.topic_data = topic_data
                        flag_modified(campaign, "topic_data")
                        gold = dict(campaign.gold_metadata or {})
                        if "creation_config" not in gold:
                            gold["creation_config"] = {}
                        gold["creation_config"]["scouting_active"] = True
                        campaign.gold_metadata = gold
                        flag_modified(campaign, "gold_metadata")
                        await campaign_repo.update(campaign)
                        logs.append(f"🔗 [SYNC] Đã lưu báo cáo vào chiến dịch {campaign_id}.")

                await session.commit()
            except Exception as db_err:
                logger.error(f"[Scout] Failed to persist cache: {db_err}")
                logs.append("⚠️ Không thể lưu Cache vào DB, nhưng kết quả vẫn được trả về.")

            report.logs = logs + ["✅ Trinh sát hoàn tất. Báo cáo chiến lược đã sẵn sàng."]
            if campaign_id:
                await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "step": 1, "message": "✅ Đã trinh sát xong.", "status": "IDLE"})
            return GenericResponse(status="success", data=report.model_dump())
