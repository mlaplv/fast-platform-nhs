import uuid
import logging
import asyncio
import time
import traceback
from datetime import datetime, timezone
from typing import Dict, Union, Optional
from sqlalchemy import select, func
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import ContentCampaign, CampaignEvent
from backend.database.repositories import ContentCampaignRepository
from backend.utils.text import to_int
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
from backend.services.xohi.creative_studio.registry import registry
from backend.services.event_bus import event_bus
from backend.constants.agentic import STEP_ARTIFICIAL_LATENCY_SECONDS
from backend.database.alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")

class ExecutionEngine:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator
        self._active_tasks: Dict[str, asyncio.Task] = {} # CNS V82.50: Campaign task tracking

    async def trigger_step(self, campaign_id: str, force_step: Optional[int] = None):
        logger.info(f"🔥 [ExecutionEngine] CNS V82.55 Active for campaign {campaign_id}")
        # CNS V82.50: Capture and cancel existing task BEFORE registering the new one
        # This avoids the race where a task might accidentally wait on itself
        old_task = self._active_tasks.get(campaign_id)
        if old_task and not old_task.done():
            logger.warning(f"[ExecutionEngine] Triggering cancellation for campaign {campaign_id}.")
            old_task.cancel()
            # CNS V82.50: REMOVED await wait_for. Let the old task die asynchronously while the new task prepares.
            # This ensures zero-blocking during retries.

        # Register CURRENT task as the active one
        current_task = asyncio.current_task()
        self._active_tasks[campaign_id] = current_task
        logger.info(f"📌 [ExecutionEngine] Registered NEW task {current_task.get_name()} for {campaign_id}")

        try:
            # CNS V82.50: IMMEDIATE HARD WIPE & STATE TRANSITION
            # We do this BEFORE the semaphore to ensure the UI resets instantly
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as session:
                repo = ContentCampaignRepository(session=session)
                stmt = select(ContentCampaign).where(
                    ContentCampaign.id == campaign_id,
                    ContentCampaign.deleted_at == None
                )
                c = (await session.execute(stmt)).scalar_one_or_none()
                if c:
                    # CNS V82.50: Define step if missing
                    step = force_step if force_step is not None else c.current_step

                    # CNS V82.50: CASCADING HARD WIPE
                    # When a step is retried, we MUST clear all data for THAT step AND ALL FUTURE steps
                    # to prevent "ghosting" or "stale data leaks" from previous higher-step runs.
                    logger.info(f"🧹 [ExecutionEngine] CASCADING WIPE from Step {step} onwards.")
                    
                    if step <= 1: 
                        c.topic_data = None
                    if step <= 2:
                        c.assets_data = []
                        if c.gold_metadata:
                            gold = dict(c.gold_metadata)
                            gold["reserve_assets"] = []
                            c.gold_metadata = gold
                            flag_modified(c, "gold_metadata")
                    if step <= 3: 
                        c.outline_data = None
                    if step <= 4: 
                        c.draft_content = ""
                    if step <= 5: 
                        c.unique_score = 1.0
                    if step <= 6: 
                        c.final_html = None
                    
                    await repo.update(c)
                    await session.commit()
                    logger.info(f"✅ [ExecutionEngine] Cascading Wipe Complete for {campaign_id}")
            
            # Signal UI immediately after wipe
            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": campaign_id,
                "step": step, 
                "message": "💥 Đã dọn sạch dữ liệu. Đang khởi động lại...",
                "status": "PROCESSING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            async with self.orchestrator.semaphore:
                async with session_maker() as session:
                    repo = ContentCampaignRepository(session=session)
                    logger.info(f"[ExecutionEngine] Ready to execute Step {step} for {campaign_id}")
                    await self._execute_step(campaign_id, repo, force_step=force_step)
                    await session.commit()
        finally:
            # Only remove if we are still the active task
            if self._active_tasks.get(campaign_id) == current_task:
                del self._active_tasks[campaign_id]

    async def terminate_campaign_tasks(self, campaign_id: str):
        """
        Elite V2.2: Hard Kill Signal.
        Cancels any active asyncio task for a campaign to prevent ghost logs.
        """
        task = self._active_tasks.get(campaign_id)
        if task and not task.done():
            logger.warning(f"🛑 [ExecutionEngine] Terminating active task for purged campaign: {campaign_id}")
            task.cancel()
            # We don't await here to avoid blocking management handlers, 
            # let it finish cancellation in its own thread.
            if self._active_tasks.get(campaign_id) == task:
                del self._active_tasks[campaign_id]

    async def _execute_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository, force_step: Optional[int] = None):
        stmt = select(ContentCampaign).where(
            ContentCampaign.id == campaign_id,
            ContentCampaign.deleted_at == None
        )
        campaign = (await campaign_repo.session.execute(stmt)).scalar_one_or_none()
        if not campaign: return
        
        step = force_step if force_step is not None else campaign.current_step
        start_time = time.time()
        logger.info(f"[Content Factory] Executing Step {step} for {campaign_id}")
        
        await asyncio.sleep(STEP_ARTIFICIAL_LATENCY_SECONDS)
        campaign.status = "PROCESSING" # CNS V82.50: Explicitly set status to PROCESSING
        if campaign.current_step != step:
            campaign.current_step = step
        await campaign_repo.update(campaign)

        try:
            messages = {1: "✍️ Đang phân tích chủ đề...", 2: "🔍 Đang tìm ảnh...", 3: "📝 Lập dàn ý...", 4: "🖋️ AI đang viết...", 5: "🛡️ Đang kiểm tra đạo văn...", 6: "📦 Đang hoàn thiện..."}
            await self._emit_progress(campaign_id, step, messages.get(step, "Đang xử lý..."), user_id=campaign.user_id)

            # Phase 73: Retrieve operative from registry for steps 1-4 and 6
            operative = registry.get_operative(step)

            # Phase 76.5: Neural Streaming Waterfall (Step 4 Special Handling)
            if step == 4 and hasattr(operative, "stream_draft"):
                campaign = await campaign_repo.get(campaign_id)
                campaign.draft_content = "" # Clear stale content to prevent UI showing old article
                full_content = ""
                async for chunk in operative.stream_draft(campaign):
                    if chunk["type"] == "chunk":
                        text = chunk["text"]
                        full_content += text
                        # Emit chunk to event bus for real-time UI updates
                        await event_bus.emit("CONTENT_CHUNK", {
                            "campaign_id": campaign_id,
                            "text": text,
                            "step": 4
                        })
                    elif chunk["type"] == "final":
                        # Step 4 logic completion
                        campaign.draft_content = chunk["content"]
                        response = AgentResponse(
                            signal=AgentSignal.PROCEED_NEXT,
                            message="Draft content generated — Viral 2026 Edition.",
                            data={"content": chunk["content"]}
                        )
                        break
                    elif chunk["type"] == "error":
                        await self._log_error(campaign, campaign_repo, "ERROR", chunk["message"])
                        return

                # Mock a finished task for the existing logic below
                response_task = asyncio.Future()
                response_task.set_result(response)
            else:
                # Phase 76.5: Clean buffers before run (Prevents UI ghosting)
                campaign = await campaign_repo.get(campaign_id)
                if step == 3:
                    campaign.outline_data = None
                elif step == 1:
                    campaign.topic_data = None
                await campaign_repo.update(campaign)

                response_task = asyncio.create_task(operative.execute(campaign_id, campaign_repo, step=step))

            # Phase 76: Zero-Latency Heartbeat (V76)
            # Replaces busy-wait sleep(10) with instant completion detection
            pulse_count = 0
            while not response_task.done():
                # Wait for task completion OR 10s timeout for next pulse
                try:
                    done, pending = await asyncio.wait([response_task], timeout=10.0)
                except Exception:
                    # Defensive: in case of rare cancellation issues
                    if response_task.done(): break
                    raise

                if not response_task.done():
                    pulse_count += 1
                    logger.debug(f"[Content Factory] Pulse {pulse_count}: Step {step} still working for {campaign_id}")

                    msg = messages.get(step, "Đang xử lý...")
                    if step == 4:
                        sub_msgs = [
                            "Đang phân tích và nhào nặn tiêu đề...",
                            "Đang xây dựng nội dung chi tiết theo dàn ý...",
                            "Đang căn chỉnh mật độ từ khóa chuẩn SEO...",
                            "Đang tối ưu hóa hình ảnh và thẻ figure...",
                            "Đang kiểm tra tính nhất quán của văn phong...",
                            "Đang hoàn thiện những bước cuối cùng..."
                        ]
                        idx = min(pulse_count - 1, len(sub_msgs) - 1)
                        msg = sub_msgs[idx]

                    await self._emit_progress(campaign_id, step, msg, user_id=campaign.user_id)

                    # CNS V82.10: Reactive Cancellation Support
                    # Re-fetch campaign to check for user-triggered REJECTED (Hard Kill)
                    from backend.database.alchemy_config import alchemy_config
                    async with alchemy_config.create_session_maker()() as check_session:
                        check_repo = ContentCampaignRepository(session=check_session)
                        check_stmt = select(ContentCampaign).where(
                            ContentCampaign.id == campaign_id,
                            ContentCampaign.deleted_at == None
                        )
                        check_campaign = (await check_session.execute(check_stmt)).scalar_one_or_none()
                        if check_campaign and check_campaign.status == "REJECTED":
                            logger.warning(f"[Content Factory] Task {campaign_id} CANCELLED via Hard Kill. Aborting.")
                            response_task.cancel()
                            return

            response = await response_task
            if not isinstance(response, AgentResponse):
                response = AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Legacy success", data={"raw": response})

            # Phase 73: Sync metadata from response if present (Prevents overwriting agent-side changes)
            if response.data and "gold_metadata" in response.data:
                campaign.gold_metadata = response.data["gold_metadata"]
                flag_modified(campaign, "gold_metadata")

            if response.signal == AgentSignal.REDO_PREVIOUS:
                if await self._handle_backtrack(campaign, campaign_repo, step):
                    return

            if response.signal == AgentSignal.FAIL_GRACEFULLY:
                await self._log_error(campaign, campaign_repo, "ERROR", f"Agent Escalation: {response.message}")
                return

            # Update campaign data from response (Specific step fields)
            if response.data:
                if step == 1:
                    campaign.topic_data = response.data
                    campaign.gold_metadata = response.data # First seal
                elif step == 2:
                    # Phase 15.3: Chuẩn hóa dữ liệu assets (hỗ trợ kéo thả)
                    raw_assets = response.data.get("assets", response.data) if isinstance(response.data, dict) else response.data
                    if isinstance(raw_assets, list):
                        campaign.assets_data = raw_assets
                    else:
                        campaign.assets_data = raw_assets
                elif step == 3:
                    # CNS V86.5: Robust Outline Extraction
                    outline = response.data.get("outline", response.data) if isinstance(response.data, dict) else response.data
                    # If it's a dict and has sections, it's good. If it's legacy raw string, it's good.
                    campaign.outline_data = outline
                elif step == 4:
                    # CNS V86.5: Robust Draft Extraction
                    draft = campaign.draft_content # Default to current
                    if isinstance(response.data, dict):
                        draft = response.data.get("content", response.data.get("raw", campaign.draft_content))
                    elif isinstance(response.data, str):
                        draft = response.data
                    
                    # Ensure draft is eventually a string (handle nested dicts if agent misunderstood)
                    if isinstance(draft, dict) and "content" in draft:
                        draft = draft["content"]
                    
                    campaign.draft_content = draft
                elif step == 5:
                    if isinstance(response.data, dict) and "score" in response.data:
                        campaign.unique_score = response.data["score"]
                elif step == 6:
                    # Step 6 might update final_html and assets
                    if isinstance(response.data, dict):
                        if "final_html" in response.data:
                            campaign.final_html = response.data["final_html"]
                        if "assets" in response.data:
                            campaign.assets_data = response.data["assets"]
                            flag_modified(campaign, "assets_data")

            # Phase 73: Always set to WAITING_FOR_REVIEW after an automated step completes
            # This allows the user to review Step 5 (Plagiarism) and Step 6 (Final Package)
            campaign.status = "WAITING_FOR_REVIEW"
            if step == 2:
                campaign.search_count = (campaign.search_count or 0) + 1
                flag_modified(campaign, "assets_data")

            await campaign_repo.update(campaign)

            payload: Dict[str, object] = {
                "campaign_id": campaign_id,
                "step": step,
                "status": campaign.status,
                "data": {}
            }
            payload_data = payload["data"]
            if not isinstance(payload_data, dict): payload_data = {} # Defensive cast
            # Explicit field mapping to match frontend pulse.ts expectations
            # Frontend reads: topic_data/keywords, assets (NOT assets_data), outline, draft_content, gold_metadata
            if step == 1:
                td = getattr(campaign, "topic_data", None)
                payload_data["topic_data"] = td
                payload_data["keywords"] = td
            elif step == 2:
                payload_data["assets"] = getattr(campaign, "assets_data", None) or []
            elif step == 3:
                payload_data["outline"] = getattr(campaign, "outline_data", None)
            elif step == 4:
                payload_data["draft_content"] = getattr(campaign, "draft_content", None)
            elif step == 5:
                payload_data["unique_score"] = getattr(campaign, "unique_score", None)
            elif step == 6:
                # IMPORTANT: Ensure deferred column is refreshed before payload construction
                try:
                    await campaign_repo.session.refresh(campaign, ["final_html"])
                except Exception as refresh_err:
                    logger.warning(f"[Content Factory] Refresh failed for final_html: {refresh_err}")

                payload_data["assets"] = getattr(campaign, "assets_data", None) or []
                payload_data["final_html"] = getattr(campaign, "final_html", None)

            # Always include gold_metadata for avatar/config sync
            payload_data["gold_metadata"] = getattr(campaign, "gold_metadata", None) or {}
            
            logger.info(f"[ExecutionEngine] Emitting CONTENT_STEP_COMPLETED for Step {step}. Assets in payload: {len(payload_data.get('assets', [])) if isinstance(payload_data.get('assets'), list) else 'N/A'}, Reserves: {len(payload_data.get('gold_metadata', {}).get('reserve_assets', []))}")

            await event_bus.emit("CONTENT_STEP_COMPLETED", payload)
            logger.info(f"[Content Factory] Step {step} SUCCESS in {time.time() - start_time:.2f}s")

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"[Content Factory] Step {step} FAILED for {campaign_id}:\n{error_trace}")
            await self._log_error(campaign, campaign_repo, "ERROR", str(e))

    async def _handle_backtrack(self, campaign, repo, step) -> bool:
        stmt = select(func.count()).select_from(CampaignEvent).where(
            CampaignEvent.campaign_id == campaign.id,
            CampaignEvent.event_type == "BACKTRACK",
            CampaignEvent.payload["step"].as_integer() == step
        )
        result = await repo.session.execute(stmt)
        count = result.scalar() or 0
        
        if count < 2:
            event = CampaignEvent(
                id=str(uuid.uuid4()), campaign_id=campaign.id, event_type="BACKTRACK",
                payload={"step": step, "count": count + 1}, tenant_id=campaign.tenant_id
            )
            repo.session.add(event)
            campaign.current_step = max(1, step - 1)
            campaign.status = "PROCESSING"
            await repo.update(campaign)
            asyncio.create_task(self.trigger_step(campaign.id, force_step=campaign.current_step))
            return True
        return False

    async def _emit_progress(self, campaign_id: str, step: int, message: str, user_id: Optional[str] = None):
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": campaign_id, "user_id": user_id, "step": step,
            "message": message, "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def _log_error(self, campaign, repo, status, error_msg):
        campaign.status = status
        event = CampaignEvent(
            id=str(uuid.uuid4()), campaign_id=campaign.id, event_type="ERROR",
            payload={"step": campaign.current_step, "error": error_msg}, tenant_id=campaign.tenant_id
        )
        repo.session.add(event)
        await repo.update(campaign)
        
        # Phase 82.11: Emit explicit ERROR signal to SSE so the Svelte UI doesn't hang!
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": campaign.id,
            "user_id": campaign.user_id,
            "step": campaign.current_step,
            "message": error_msg,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
