import asyncio
import logging
import uuid
import numpy as np
from typing import Dict, Union, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Article, ContentCampaign
from backend.services.content_service import content_service
from backend.services.event_bus import event_bus
from backend.models.schemas import GenericResponse
from backend.schemas.article import CreateArticleRequest

logger = logging.getLogger("api-gateway")

class ActionHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def approve_step(self, campaign_id: str, data: Dict[str, object], session: AsyncSession) -> GenericResponse:
        campaign = await session.get(ContentCampaign, campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        step = campaign.current_step
        request_step = data.get("step")
        if request_step is not None and int(request_step) != step:
            return GenericResponse(status="error", message=f"Dạ sếp, bước {request_step} này đã qua hoặc chưa tới ạ.", data={"current_step": step})

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
                return GenericResponse(status="error", message="Bước này đang được xử lý hoặc đã duyệt rồi ạ.")

            if step == 6:
                # Terminal Step: Publish to News + Cleanup
                success = await self._publish_and_cleanup(campaign, session)
                if success:
                    await session.commit()

                    # Notify Responder to announce success
                    await event_bus.emit("CONTENT_STEP_COMPLETED", {
                        "campaign_id": campaign_id,
                        "user_id": campaign.user_id,
                        "step": 6,
                        "status": "COMPLETED",
                        "tenant_id": campaign.tenant_id
                    })

                    return GenericResponse(
                        status="success",
                        message="🎉 Chúc mừng sếp! Bài viết đã được xuất bản vào mục 'Tin tức' và hệ thống đã được dọn dẹp sạch sẽ ạ.",
                        data={"campaign_id": campaign_id, "next_step": 7}
                    )
                else:
                    return GenericResponse(status="error", message="Dạ sếp, có lỗi khi xuất bản bài viết. Sếp thử lại giúp em nhé.")

            campaign.current_step += 1
            campaign.status = "PROCESSING"

            target_step = campaign.current_step
            await session.commit()

            # Ensure we don't exceed max steps
            if target_step <= 6:
                asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id, force_step=target_step))
            return GenericResponse(status="success", message=f"Dạ sếp, em đang bắt đầu Bước {target_step} ạ.", data={"campaign_id": campaign_id, "next_step": target_step})
        else:
            campaign.status = "REJECTED"
            await session.commit()
            return GenericResponse(status="success", message="Đã ghi nhận sếp không duyệt bước này.", data={"campaign_id": campaign_id})

    async def _publish_and_cleanup(self, campaign: ContentCampaign, session: AsyncSession) -> bool:
        """
        Phase 76.3: Publication to News (Articles) + Hard Memory Cleanup.
        Moves final content to the public table and strips heavy JSON from campaign to save 2GB RAM.
        """
        try:
            # 1. Ensure final_html is loaded (it is a deferred column)
            from sqlalchemy import inspect
            ins = inspect(campaign)
            if "final_html" in ins.unloaded:
                await session.refresh(campaign, ["final_html"])

            # 2. Create Article via ContentService (Elite V2.2)
            title = campaign.get_gold_val("topic") or campaign.get_gold_val("title", "Bài viết sáng tạo mới")
            content = campaign.final_html or campaign.draft_content

            if not content:
                logger.warning(f"[ActionHandler] No content found for campaign {campaign.id}")
                return False

            article_req = CreateArticleRequest(
                title=title,
                content=content,
                authorId=campaign.user_id,
                status="PUBLISHED",
                category="Tin tức"
            )

            # ContentService handles slug generation and embedding
            new_article = await content_service.create_article(session, article_req)
            logger.info(f"[ActionHandler] Published campaign {campaign.id} to Article {new_article.id} via ContentService")

            # 3. Hard Cleanup (Rule R82.25: Zero-Allocation & Memory Safety)
            campaign.status = "COMPLETED"
            # Strip heavy metadata to keep DB and memory lean on 2GB RAM VPS
            campaign.topic_data = {}
            campaign.assets_data = []
            campaign.outline_data = {}
            campaign.draft_content = ""
            campaign.final_html = ""

            logger.info(f"[ActionHandler] Published campaign {campaign.id} to Article {new_article.id} and cleaned up.")
            return True
        except Exception as e:
            logger.exception(f"[ActionHandler] Publication failed for campaign {campaign.id}: {e}")
            return False

    async def retry_step(self, campaign_id: str, session: AsyncSession) -> GenericResponse:
        campaign = await session.get(ContentCampaign, campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        campaign.status = "PROCESSING"
        step_val = campaign.current_step
        await session.commit()

        asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id, force_step=step_val))
        return GenericResponse(status="success", message=f"Em đang chạy lại bước {step_val} cho sếp đây!", data={"campaign_id": campaign_id})

    async def update_metadata(self, campaign_id: str, data: Dict[str, object], session: AsyncSession) -> GenericResponse:
        campaign = await session.get(ContentCampaign, campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

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

        await session.commit()
        return GenericResponse(status="success", message="Neural data synchronized.", data={"campaign_id": campaign_id})

