import os
import uuid
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.operatives.vision_insight import VisionInsight
from backend.services.xohi.creative_studio.models.schemas import TopicSeed, ArticleOutline, AgentSignal, AgentResponse
from backend.services.xohi.creative_studio.operatives.asset_hunter import AssetHunter
from backend.services.xohi.creative_studio.operatives.creative_pen import CreativePen
from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
from backend.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.event_bus import event_bus
from litestar.repository.filters import LimitOffset
from backend.database.alchemy_config import alchemy_config
from backend.constants.agentic import ORCHESTRATOR_SEMAPHORE_LIMIT, STEP_ARTIFICIAL_LATENCY_SECONDS
from backend.services.xohi.creative_studio.registry import registry
from backend.services.ai_engine.core.trinity_bridge import AIConfigurationError

logger = logging.getLogger("api-gateway")

class ContentOrchestrator:
    """
    The brain of V62.1 Content Factory. 
    Manages the 6-step state machine with the Hardened "Golden Thread" logic.
    """

    def __init__(self, vision=None, hunter=None, pen=None, cop=None, media=None):
        # R107: Dependency Injection for Agentic Collaboration
        self.vision = vision or VisionInsight()
        self.pen = pen or CreativePen(model_name=os.getenv("TIER3_MODEL", "gemini-3.1-pro-preview-customtools"))
        self.cop = cop or PlagiarismCop()
        self.media = media or MediaCompressor()
        
        if hunter:
            self.hunter = hunter
        else:
            keys = []
            for i in ["", "_1", "_2"]:
                k = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}")
                cx = os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
                if k and cx:
                    keys.append({"key": k, "cx": cx})
            self.hunter = AssetHunter(keys)
            
        self.semaphore = asyncio.Semaphore(ORCHESTRATOR_SEMAPHORE_LIMIT) # R101
        
        # R107: Bootstrap DI Registry
        registry.register(1, self.vision)
        registry.register(2, self.hunter)
        registry.register(3, self.pen)
        registry.register(4, self.pen) # CreativePen handles 3 and 4
        registry.register(5, self.cop)
        registry.register(6, self.media)
        
        logger.info("[Content Factory] V61.0 Orchestrator initialized with DI & Registry.")

    async def resume_all(self):
        """
        R104: Self-Healing Resume logic. 
        Scans DB for PROCESSING campaigns on startup and resumes them.
        """
        logger.info("[Content Factory] SELF-HEALING: Scanning for PROCESSING campaigns to resume...")
        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            repo = ContentCampaignRepository(session=session)
            # Find campaigns stuck in PROCESSING
            from sqlalchemy import select
            stmt = select(ContentCampaign).where(ContentCampaign.status == "PROCESSING")
            result = await session.execute(stmt)
            campaigns = result.scalars().all()
            
            for c in campaigns:
                logger.info(f"[Content Factory] RESUMING stuck campaign: {c.id} (Step {c.current_step})")
                asyncio.create_task(self._trigger_next_step(c.id, force_step=c.current_step))
        logger.info(f"[Content Factory] SELF-HEALING: Resume check complete. {len(campaigns)} restored.")

    async def get_active_campaign(self, campaign_repo: ContentCampaignRepository, user_id: str = None, tenant_id: str = "default") -> Optional[ContentCampaign]:
        """Find the most recent campaign that is either processing or waiting for review."""
        results = await campaign_repo.list(
            LimitOffset(limit=5, offset=0),
            order_by=[("created_at", "desc")],
            deleted_at=None
        )
        for c in results:
            if c.status in ["PROCESSING", "WAITING_FOR_REVIEW"] and c.tenant_id == tenant_id:
                # Rule R86: Stickiness — Only resume campaigns belonging to this user
                if user_id and c.user_id == user_id:
                    return c
                elif not user_id: # Fallback for system-level checks
                    return c
        return None

    def format_resume_greeting(self, campaign: ContentCampaign) -> str:
        """Format a proactive greeting for a resumed session."""
        step = campaign.current_step
        title = campaign.topic_data.get("title", "bài viết mới")
        
        if campaign.status == "PROCESSING":
            return f"Chào sếp, em đang tiếp tục thực hiện Bước {step} cho bài viết '{title}' ạ. Sếp đợi em chút nhé!"
        else:
            return f"Chào sếp, em đã hoàn thành xong Bước {step} cho bài viết '{title}'. Mời sếp xem qua và duyệt để em chạy tiếp ạ!"

    async def handle_voice_request(
        self, transcript: str, context: list = None, 
        campaign_repo: ContentCampaignRepository = None,
        tenant_id: str = "default",
        user_id: str = None
    ) -> IntentResponse:
        """
        Entry point khi sếp nói "viết bài" qua Voice/Text.
        R86: Tạo campaign trong DB TRƯỚC → gọi AI sinh keywords → lưu → trả response.
        """
        if campaign_repo is None:
            logger.error("[Content Factory] campaign_repo is strictly None — cannot persist.")
            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message="Dạ sếp, hệ thống Content Factory đang khởi động. Sếp thử lại sau chút nhé!",
                router_tier=RouterTier.TIER_2_SEMANTIC, data={}, cost_tokens=0.0
            )

        try:
            stale = await self.get_active_campaign(campaign_repo, user_id, tenant_id)
            if stale:
                # 1. Lệnh "tiếp" rõ ràng
                if "tiếp" in transcript.lower():
                    if stale.status == "WAITING_FOR_REVIEW":
                        return await self.approve_step(stale.id, {"approved": True}, campaign_repo)
                    else:
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=self.format_resume_greeting(stale),
                            router_tier=RouterTier.TIER_2_SEMANTIC, data={"campaign_id": stale.id, "step": stale.current_step}, cost_tokens=0.0
                        )
                
                # 2. Idempotency Latch (15s Chốt chặn): Nếu sếp bấm spam hoặc hệ thống auto-retry
                # Kiểm tra timestamp created_at của chiến dịch dở dang gần nhất
                try:
                    now = datetime.now(timezone.utc)
                    stale_time = stale.created_at
                    if stale_time.tzinfo is None:
                        stale_time = stale_time.replace(tzinfo=timezone.utc)
                    time_diff = (now - stale_time).total_seconds()
                    
                    if time_diff < 15.0:
                        logger.warning(f"[Content Factory] Idempotency Latch triggered. Blocking duplicate request. Diff: {time_diff}s, ID: {stale.id}")
                        if stale.status == "WAITING_FOR_REVIEW":
                            return IntentResponse(
                                status="success", action=IntentAction.CONTENT_CREATE,
                                message=f"Dạ sếp, bài viết '{stale.topic_data.get('title', 'này')}' em vừa phân tích xong. Mời sếp duyệt trên màn hình ạ!",
                                router_tier=RouterTier.TIER_2_SEMANTIC, data={"campaign_id": stale.id, "step": stale.current_step, "keywords": stale.topic_data}, cost_tokens=0.0
                            )
                        else:
                            return IntentResponse(
                                status="success", action=IntentAction.CONTENT_CREATE,
                                message=self.format_resume_greeting(stale),
                                router_tier=RouterTier.TIER_2_SEMANTIC, data={"campaign_id": stale.id, "step": stale.current_step}, cost_tokens=0.0
                            )
                except Exception as e:
                    logger.error(f"[Content Factory] Lỗi khi tính Idempotency Latch: {e}")

            campaign = ContentCampaign(
                id=str(uuid.uuid4()),
                user_id=user_id,
                source_input=transcript,
                tenant_id=tenant_id,
                current_step=1,
                status="PROCESSING",
                gold_metadata={},
                search_count=0
            )
            c_id = campaign.id
            u_id_str = str(campaign.user_id) if campaign.user_id else "default"
            raw_input = campaign.source_input

            campaign = await campaign_repo.add(campaign)
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()
                await campaign_repo.session.refresh(campaign) # Ensure object is reloaded and safe
                
            logger.info(f"[Content Factory] Campaign created and committed: {c_id}")

            seed: TopicSeed = await self.vision.analyze_input(raw_input, c_id, u_id_str)
            seed_data = seed.model_dump()

            campaign.topic_data = seed_data
            campaign.status = "WAITING_FOR_REVIEW"
            await campaign_repo.update(campaign)
            
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()
            
            logger.info(f"[Content Factory] Step 1 done: {c_id} → committed WAITING_FOR_REVIEW")

            voice_msg = self._format_keywords_for_voice(seed_data)

            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": c_id,
                "step": 1,
                "status": "WAITING_FOR_REVIEW",
                "user_id": u_id_str,
                "data": {"keywords": seed_data}
            })

            return IntentResponse(
                status="success",
                action=IntentAction.CONTENT_CREATE,
                message=voice_msg,
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={
                    "category": "CONTENT_CREATE",
                    "action": "STEP1_REVIEW",
                    "campaign_id": campaign.id,
                    "status": "WAITING_FOR_REVIEW",
                    "keywords": seed_data,
                    "step": 1
                },
                cost_tokens=0.0
            )

        except AIConfigurationError as ae:
            logger.error(f"[Content Factory] AI Configuration Error: {ae}")
            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message=f"Dạ sếp, lỗi LLM: {str(ae)}. Model: {ae.model}, Key Index: {ae.key_index}. Sếp kiểm tra lại Key hoặc Model trong .env nhé!",
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={"category": "CONTENT_CREATE", "source_input": transcript, "error_type": "AI_CONFIG", "model": ae.model},
                cost_tokens=0.0
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"[Content Factory] handle_voice_request CRASH: {e}\n{error_details}")
            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message=f"Dạ sếp, có lỗi hệ thống: {str(e)}. Sếp thử lại sau chút nhé!",
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={"category": "CONTENT_CREATE", "source_input": transcript, "debug_error": str(e)},
                cost_tokens=0.0
            )

    def _format_keywords_for_voice(self, seed_data: dict) -> str:
        """Format TopicSeed thành câu nói tự nhiên, siêu mỏng cho XoHi voice (V80.1)."""
        title = seed_data.get("title", "mới")
        return (
            f"Dạ sếp, em đã phân tích xong từ khóa cho chủ đề '{title}'. "
            f"Mời sếp duyệt trên màn hình để em chạy tiếp ạ!"
        )

    async def _run_current_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository, force_step: int = None):
        """
        R107: Dynamic Orchestration via DI Registry (V61.0).
        Eliminates 100+ lines of hardcoded if/elif logic.
        """
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        
        step = force_step if force_step is not None else campaign.current_step
        import time, asyncio
        start_time = time.time()
        logger.info(f"[Content Factory] Dynamic Dispatch: Step {step} for {campaign_id}")
        
        await asyncio.sleep(STEP_ARTIFICIAL_LATENCY_SECONDS)

        if campaign.current_step != step:
            logger.warning(f"[Content Factory] STEP DRIFT: Enforcing {step}")
            campaign.current_step = step

        try:
            operative = registry.get_operative(step)
            
            messages = {
                1: "✍️ Đang phân tích chủ đề...",
                2: "🔍 Hệ thống AssetHunt đang tìm ảnh...",
                3: "📝 Lập dàn ý bài viết...",
                4: "🖋️ AI đang chấp bút bản thảo...",
                5: "🛡️ Đang kiểm tra đạo văn...",
                6: "📦 Đóng gói sản phẩm cuối cùng..."
            }
            await self._emit_progress(campaign_id, step, messages.get(step, "Đang xử lý..."), user_id=campaign.user_id)
            
            response = await operative.execute(campaign_id, campaign_repo, step=step)
            
            if not isinstance(response, AgentResponse):
                response = AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Legacy success", data={"raw": response})

            if response.signal == AgentSignal.REDO_PREVIOUS:
                from sqlalchemy import select, func
                from backend.database.models import CampaignEvent
                
                stmt = select(func.count()).select_from(CampaignEvent).where(
                    CampaignEvent.campaign_id == campaign_id,
                    CampaignEvent.event_type == "BACKTRACK",
                    CampaignEvent.payload["step"].as_integer() == step
                )
                if hasattr(campaign_repo, "session"):
                    result = await campaign_repo.session.execute(stmt)
                    backtrack_count = result.scalar() or 0
                else:
                    backtrack_count = 0
                
                if backtrack_count < 2:
                    logger.warning(f"[Content Factory] BACKTRACK TRIGGERED by Step {step}: {response.message}")
                    event = CampaignEvent(
                        id=str(uuid.uuid4()),
                        campaign_id=campaign_id,
                        event_type="BACKTRACK",
                        payload={"step": step, "reason": response.message, "count": backtrack_count + 1},
                        tenant_id=campaign.tenant_id
                    )
                    if hasattr(campaign_repo, "session"):
                        campaign_repo.session.add(event)
                    
                    campaign.current_step = max(1, step - 1)
                    campaign.status = "PROCESSING"
                    curr_step = campaign.current_step
                    await campaign_repo.update(campaign)
                    
                    if hasattr(campaign_repo, "session"):
                        await campaign_repo.session.commit()
                    
                    asyncio.create_task(self._trigger_next_step(campaign_id, force_step=curr_step))
                    return
                else:
                    logger.error(f"[Content Factory] MAX BACKTRACK EXCEEDED at Step {step}.")
                    response.signal = AgentSignal.FAIL_GRACEFULLY

            if response.signal == AgentSignal.FAIL_GRACEFULLY:
                await self._log_error(campaign_id, campaign_repo, "ERROR", f"Agent Escalation: {response.message}")
                if hasattr(campaign_repo, "session"):
                    await campaign_repo.session.commit()
                return

            campaign = await campaign_repo.get(campaign_id)
            
            # Preserve agent data
            if response.data:
                if step == 4:
                    campaign.draft_content = response.data.get("content", campaign.draft_content)
                elif step == 5:
                    campaign.unique_score = response.data.get("score", campaign.unique_score)
                    campaign.plagiarism_data = response.data

            if step < 6:
                campaign.status = "WAITING_FOR_REVIEW"
                if step == 2: campaign.search_count = (campaign.search_count or 0) + 1
            else:
                campaign.status = "COMPLETED"
                
            await campaign_repo.update(campaign)
            
            payload = {"campaign_id": campaign_id, "step": step, "status": campaign.status, "data": {}}
            if step == 1: payload["data"]["keywords"] = campaign.topic_data
            elif step == 2: payload["data"]["assets"] = campaign.assets_data
            elif step == 3: payload["data"]["outline"] = campaign.outline_data
            elif step == 4: payload["data"]["draft_content"] = campaign.draft_content or ""
            elif step == 5: 
                payload["data"]["unique_score"] = campaign.unique_score
                payload["data"]["plagiarism"] = campaign.plagiarism_data

            await event_bus.emit("CONTENT_STEP_COMPLETED", payload)
            
            elapsed = time.time() - start_time
            logger.info(f"[Content Factory] Step {step} SUCCESS in {elapsed:.2f}s")
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[Content Factory] Step {step} FAILED after {elapsed:.2f}s: {e}")
            await self._log_error(campaign_id, campaign_repo, "ERROR", str(e))
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()

    async def approve_step(self, campaign_id: str, data: Dict[str, Any], 
                           campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        step = campaign.current_step
        request_step = data.get("step")
        
        if request_step is not None and int(request_step) != step:
            return {
                "status": "error", 
                "message": f"Dạ sếp, bước {request_step} này đã qua hoặc chưa tới ạ. Em đang ở bước {step}.",
                "current_step": step
            }

        approved = data.get("approved", True)
        edited_data = data.get("edited_data")

        if approved:
            if edited_data:
                if step == 1: 
                    campaign.topic_data = edited_data
                elif step == 3: 
                    # If it's HTML from the editor, store it as the draft_content base for step 4
                    if isinstance(edited_data, dict) and "html" in edited_data:
                        campaign.draft_content = edited_data["html"]
                    else:
                        campaign.outline_data = edited_data
                elif step == 4: 
                    # Support both 'content' and 'html' (from RichTextEditor)
                    new_content = edited_data.get("html") or edited_data.get("content")
                    if new_content:
                        campaign.draft_content = new_content

            if step == 2:
                if "assets" in data and data["assets"] is not None:
                    campaign.assets_data = data["assets"]
                
                # R85.2: Sync curated avatar and selection focus
                avatar = data.get("avatar")
                selected_index = data.get("selected_index")
                if avatar or selected_index is not None:
                    gold = dict(campaign.gold_metadata or {})
                    if avatar:
                        gold["avatar"] = avatar
                    if selected_index is not None:
                        gold["selected_index"] = selected_index
                    campaign.gold_metadata = gold

            if step == 1:
                campaign.gold_metadata = campaign.topic_data

            if campaign.status != "WAITING_FOR_REVIEW":
                return {"status": "error", "message": "Bước này đang được xử lý hoặc đã duyệt rồi ạ."}

            campaign.current_step += 1
            campaign.status = "PROCESSING"
            await campaign_repo.update(campaign)
            
            target_step = campaign.current_step
            
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()

            asyncio.create_task(self._trigger_next_step(campaign_id, force_step=target_step))

            return {
                "status": "success", 
                "message": f"Dạ sếp, em đang bắt đầu thực hiện Bước {target_step} ạ.",
                "campaign_id": campaign_id,
                "next_step": target_step
            }
        else:
            campaign.status = "REJECTED"
            await campaign_repo.update(campaign)
            return {"status": "success", "message": "Đã ghi nhận sếp không duyệt bước này.", "campaign_id": campaign_id}

    async def retry_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        campaign.status = "PROCESSING"
        await campaign_repo.update(campaign)
        
        if hasattr(campaign_repo, "session"):
            current_step_val = campaign.current_step
            await campaign_repo.session.commit()

        asyncio.create_task(self._trigger_next_step(campaign_id, force_step=current_step_val))

        return {"status": "success", "message": f"Em đang chạy lại bước {current_step_val} cho sếp đây!", "campaign_id": campaign_id}

    async def update_metadata(self, campaign_id: str, data: Dict[str, Any], 
                              campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """R85.1: Cập nhật dữ liệu trung gian (Assets/Keywords) mà không chuyển bước."""
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        assets = data.get("assets")
        if assets is not None:
            campaign.assets_data = assets
            
        keywords = data.get("keywords")
        if keywords is not None:
            campaign.topic_data = keywords

        outline = data.get("outline_data")
        if outline is not None:
            campaign.outline_data = outline

        draft = data.get("draft_content")
        if draft is not None:
            campaign.draft_content = draft

        avatar = data.get("avatar")
        selected_index = data.get("selected_index")
        
        if avatar or selected_index is not None:
            # R85.2: Force new dict to ensure SQLAlchemy detects mutation
            gold = dict(campaign.gold_metadata or {})
            if avatar:
                gold["avatar"] = avatar
            if selected_index is not None:
                gold["selected_index"] = selected_index
            campaign.gold_metadata = gold

        await campaign_repo.update(campaign)
        if hasattr(campaign_repo, "session"):
            await campaign_repo.session.commit()

        return {"status": "success", "message": "Neural data synchronized.", "campaign_id": campaign_id}

    async def _trigger_next_step(self, campaign_id: str, force_step: int = None):
        import asyncio
        await asyncio.sleep(0.05)
        
        async with self.semaphore:
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as session:
                repo = ContentCampaignRepository(session=session)
                await self._run_current_step(campaign_id, repo, force_step=force_step)
                await session.commit()

    async def _emit_progress(self, campaign_id: str, step: int, message: str, data: Dict[str, Any] = None, user_id: str = None):
        payload = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "step": step,
            "message": message,
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if data:
            payload["data"] = data
            
        await event_bus.emit("CONTENT_PROGRESS", payload)

    async def _log_error(self, campaign_id: str, campaign_repo: ContentCampaignRepository, 
                         status: str, error_msg: str):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        campaign.status = status
        
        from backend.database.models import CampaignEvent
        event = CampaignEvent(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            event_type="ERROR",
            payload={"step": campaign.current_step, "error": error_msg},
            tenant_id=campaign.tenant_id
        )
        if hasattr(campaign_repo, "session"):
            campaign_repo.session.add(event)
        
        await campaign_repo.update(campaign)

# Singleton — import from anywhere
content_factory = ContentOrchestrator()
