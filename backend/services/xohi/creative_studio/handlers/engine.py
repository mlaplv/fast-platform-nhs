import uuid
import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import select, func
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
            operative = registry.get_operative(step)
            messages = {1: "✍️ Đang phân tích chủ đề...", 2: "🔍 Đang tìm ảnh...", 3: "📝 Lập dàn ý...", 4: "🖋️ AI đang viết...", 5: "📦 Đang hoàn thiện..."}
            await self._emit_progress(campaign_id, step, messages.get(step, "Đang xử lý..."), user_id=campaign.user_id)
            
            response = await operative.execute(campaign_id, campaign_repo, step=step)
            if not isinstance(response, AgentResponse):
                response = AgentResponse(signal=AgentSignal.PROCEED_NEXT, message="Legacy success", data={"raw": response})

            if response.signal == AgentSignal.REDO_PREVIOUS:
                if await self._handle_backtrack(campaign, campaign_repo, step):
                    return

            if response.signal == AgentSignal.FAIL_GRACEFULLY:
                await self._log_error(campaign, campaign_repo, "ERROR", f"Agent Escalation: {response.message}")
                return

            # Update campaign data from response
            if response.data:
                if step == 1: campaign.topic_data = response.data
                elif step == 2: campaign.assets_data = response.data.get("assets", response.data) if isinstance(response.data, dict) else response.data
                elif step == 3: campaign.outline_data = response.data
                elif step == 4: campaign.draft_content = response.data.get("content", campaign.draft_content)
                elif step == 5:
                    campaign.final_html = response.data.get("final_html", campaign.final_html)
                    campaign.assets_data = response.data.get("assets", campaign.assets_data)

            campaign.status = "WAITING_FOR_REVIEW" if step < 5 else "COMPLETED"
            if step == 2: campaign.search_count = (campaign.search_count or 0) + 1
            await campaign_repo.update(campaign)
            
            payload = {"campaign_id": campaign_id, "step": step, "status": campaign.status, "data": {}}
            mapping = {1: "topic_data", 2: "assets_data", 3: "outline_data", 4: "draft_content", 5: ["assets_data", "final_html"]}
            fields = mapping.get(step)
            if isinstance(fields, list):
                for f in fields: payload["data"][f] = getattr(campaign, f)
            else:
                payload["data"][fields.split('_')[0]] = getattr(campaign, fields)

            await event_bus.emit("CONTENT_STEP_COMPLETED", payload)
            logger.info(f"[Content Factory] Step {step} SUCCESS in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[Content Factory] Step {step} FAILED: {e}")
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
