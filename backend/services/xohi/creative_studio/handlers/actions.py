import asyncio
import logging
from typing import Dict, Any
from backend.database.repositories import ContentCampaignRepository

logger = logging.getLogger("api-gateway")

class ActionHandler:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def approve_step(self, campaign_id: str, data: Dict[str, Any], campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        step = campaign.current_step
        request_step = data.get("step")
        if request_step is not None and int(request_step) != step:
            return {"status": "error", "message": f"Dạ sếp, bước {request_step} này đã qua hoặc chưa tới ạ.", "current_step": step}

        approved = data.get("approved", True)
        edited_data = data.get("edited_data")

        if approved:
            if edited_data:
                if step == 1:
                    # BUG-05 fix: Merge onto existing topic_data to preserve all TopicSeed fields
                    existing = dict(campaign.topic_data or {})
                    existing.update(edited_data)
                    campaign.topic_data = existing
                elif step == 3:
                    # BUG-06 fix: Step 3 ONLY writes outline_data. The html branch was wrong.
                    campaign.outline_data = edited_data
                elif step == 4:
                    new_content = edited_data.get("html") or edited_data.get("content")
                    if new_content: campaign.draft_content = new_content
                elif step == 5:
                    # Phase 73: Allow minor tweaks during Plagiarism Review
                    new_content = edited_data.get("html") or edited_data.get("content")
                    if new_content: campaign.draft_content = new_content

            if step == 2:
                if "assets" in data and data["assets"] is not None:
                    campaign.assets_data = data["assets"]
                avatar = data.get("avatar")
                selected_index = data.get("selected_index")
                if avatar or selected_index is not None:
                    gold = dict(campaign.gold_metadata or {})
                    if avatar: gold["avatar"] = avatar
                    if selected_index is not None: gold["selected_index"] = selected_index
                    campaign.gold_metadata = gold

            if step == 1:
                campaign.gold_metadata = campaign.topic_data  # Golden Thread sealed after Step 1 approval

            if campaign.status != "WAITING_FOR_REVIEW":
                return {"status": "error", "message": "Bước này đang được xử lý hoặc đã duyệt rồi ạ."}

            campaign.current_step += 1
            campaign.status = "PROCESSING"
            await campaign_repo.update(campaign)
            target_step = campaign.current_step
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()

            # Ensure we don't exceed max steps
            if target_step <= 6:
                asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id, force_step=target_step))
            return {"status": "success", "message": f"Dạ sếp, em đang bắt đầu Bước {target_step} ạ.", "campaign_id": campaign_id, "next_step": target_step}
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
            step_val = campaign.current_step
            await campaign_repo.session.commit()

        asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id, force_step=step_val))
        return {"status": "success", "message": f"Em đang chạy lại bước {step_val} cho sếp đây!", "campaign_id": campaign_id}

    async def update_metadata(self, campaign_id: str, data: Dict[str, Any], campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        for field in ["assets", "keywords", "outline_data", "draft_content", "final_html"]:
            val = data.get(field)
            if val is not None:
                if field == "assets": campaign.assets_data = val
                elif field == "keywords": campaign.topic_data = val
                elif field == "outline_data": campaign.outline_data = val
                elif field == "draft_content": campaign.draft_content = val
                elif field == "final_html": campaign.final_html = val

        avatar = data.get("avatar")
        selected_index = data.get("selected_index")
        if avatar or selected_index is not None:
            gold = dict(campaign.gold_metadata or {})
            if avatar: gold["avatar"] = avatar
            if selected_index is not None: gold["selected_index"] = selected_index
            campaign.gold_metadata = gold

        await campaign_repo.update(campaign)
        if hasattr(campaign_repo, "session"):
            await campaign_repo.session.commit()
        return {"status": "success", "message": "Neural data synchronized.", "campaign_id": campaign_id}
