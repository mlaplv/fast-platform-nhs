import uuid
import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import ContentCampaign, CampaignEvent
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
from backend.services.xohi.creative_studio.registry import registry
from backend.services.event_bus import event_bus
from backend.constants.agentic import STEP_ARTIFICIAL_LATENCY_SECONDS

logger = logging.getLogger("api-gateway")

class ExecutionEngine:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def trigger_step(self, campaign_id: str, force_step: int = None):
        await asyncio.sleep(0.05)
        async with self.orchestrator.semaphore:
            from backend.database.alchemy_config import alchemy_config
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as session:
                repo = ContentCampaignRepository(session=session)
                await self._execute_step(campaign_id, repo, force_step=force_step)
                await session.commit()

    async def _execute_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository, force_step: int = None):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        
        step = force_step if force_step is not None else campaign.current_step
        start_time = time.time()
        logger.info(f"[Content Factory] Executing Step {step} for {campaign_id}")
        
        await asyncio.sleep(STEP_ARTIFICIAL_LATENCY_SECONDS)
        if campaign.current_step != step:
            campaign.current_step = step

        try:
            messages = {1: "✍️ Đang phân tích chủ đề...", 2: "🔍 Đang tìm ảnh...", 3: "📝 Lập dàn ý...", 4: "🖋️ AI đang viết...", 5: "🛡️ Đang kiểm tra đạo văn...", 6: "📦 Đang hoàn thiện..."}
            await self._emit_progress(campaign_id, step, messages.get(step, "Đang xử lý..."), user_id=campaign.user_id)

            # Phase 73: Retrieve operative from registry
            operative = registry.get_operative(step)
            response_task = asyncio.create_task(operative.execute(campaign_id, campaign_repo, step=step))

            # Phase 70: Heartbeat Mechanism to prevent "Freezing" during long AI tasks (Step 4)
            pulse_count = 0
            while not response_task.done():
                await asyncio.sleep(10) # Pulse every 10s
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
                elif step == 2: campaign.assets_data = response.data.get("assets", response.data) if isinstance(response.data, dict) else response.data
                elif step == 3: campaign.outline_data = response.data.get("outline", response.data) if isinstance(response.data, dict) else response.data
                elif step == 4: campaign.draft_content = response.data.get("content", campaign.draft_content)
                elif step == 5:
                    if "score" in response.data:
                        campaign.unique_score = response.data["score"]
                elif step == 6:
                    # Step 6 might update final_html and assets
                    if "final_html" in response.data:
                        campaign.final_html = response.data["final_html"]
                    if "assets" in response.data:
                        campaign.assets_data = response.data["assets"]

            # Phase 73: Always set to WAITING_FOR_REVIEW after an automated step completes
            # This allows the user to review Step 5 (Plagiarism) and Step 6 (Final Package)
            campaign.status = "WAITING_FOR_REVIEW"
            if step == 2: campaign.search_count = (campaign.search_count or 0) + 1

            await campaign_repo.update(campaign)

            payload = {
                "campaign_id": campaign_id,
                "step": step,
                "status": campaign.status,
                "data": {}
            }
            # Explicit field mapping to match frontend pulse.ts expectations
            # Frontend reads: topic_data/keywords, assets (NOT assets_data), outline, draft_content, gold_metadata
            if step == 1:
                payload["data"]["topic_data"] = getattr(campaign, "topic_data", None)
                payload["data"]["keywords"] = getattr(campaign, "topic_data", None)
            elif step == 2:
                payload["data"]["assets"] = getattr(campaign, "assets_data", None) or []
            elif step == 3:
                payload["data"]["outline"] = getattr(campaign, "outline_data", None)
            elif step == 4:
                payload["data"]["draft_content"] = getattr(campaign, "draft_content", None)
            elif step == 5:
                payload["data"]["unique_score"] = getattr(campaign, "unique_score", None)
            elif step == 6:
                # IMPORTANT: Ensure deferred column is refreshed before payload construction
                try:
                    await campaign_repo.session.refresh(campaign, ["final_html"])
                except Exception as refresh_err:
                    logger.warning(f"[Content Factory] Refresh failed for final_html: {refresh_err}")

                payload["data"]["assets"] = getattr(campaign, "assets_data", None) or []
                payload["data"]["final_html"] = getattr(campaign, "final_html", None)

            # Always include gold_metadata for avatar/config sync
            payload["data"]["gold_metadata"] = getattr(campaign, "gold_metadata", None) or {}

            await event_bus.emit("CONTENT_STEP_COMPLETED", payload)
            logger.info(f"[Content Factory] Step {step} SUCCESS in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            import traceback
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

    async def _emit_progress(self, campaign_id: str, step: int, message: str, user_id: str = None):
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
