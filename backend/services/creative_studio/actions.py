import asyncio
import logging
import uuid
import numpy as np
from typing import Dict, Union, Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.content_service import content_service
from backend.services.campaign_service import campaign_service
from backend.services.event_bus import event_bus
from backend.schemas.campaign import GenericResponse
from backend.schemas.article import CreateArticleRequest

if TYPE_CHECKING:
    from backend.services.creative_studio.orchestrator import ContentOrchestrator

logger = logging.getLogger("api-gateway")

class ActionHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def approve_step(self, campaign_id: str, data: Dict[str, object], session: AsyncSession) -> GenericResponse:
        campaign = await campaign_service.get_campaign(session, campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        step = campaign["current_step"]
        request_step = data.get("step")
        if request_step is not None and int(request_step) != step:
            return GenericResponse(status="error", message=f"Dạ sếp, bước {request_step} này đã qua hoặc chưa tới ạ.", data={"current_step": step})

        approved = data.get("approved", True)
        edited_data = data.get("edited_data")
        update_fields = {}

        if approved:
            if edited_data:
                if step == 1:
                    # BUG-05 fix: Merge onto existing topic_data to preserve all TopicSeed fields
                    existing = dict(campaign.get("topic_data") or {})
                    existing.update(edited_data)
                    update_fields["topic_data"] = existing
                elif step == 3:
                    # BUG-06 fix: Step 3 ONLY writes outline_data. The html branch was wrong.
                    update_fields["outline_data"] = edited_data
                elif step == 4 or step == 5:
                    new_content = edited_data.get("html") or edited_data.get("content")
                    if new_content: update_fields["draft_content"] = new_content

            if step == 2:
                if "assets" in data and data["assets"] is not None:
                    update_fields["assets_data"] = data["assets"]
                avatar = data.get("avatar")
                selected_index = data.get("selected_index")
                if avatar or selected_index is not None:
                    gold = dict(campaign.get("gold_metadata") or {})
                    if avatar: gold["avatar"] = avatar
                    if selected_index is not None: gold["selected_index"] = selected_index
                    update_fields["gold_metadata"] = gold

            if step == 1:
                update_fields["gold_metadata"] = update_fields.get("topic_data", campaign.get("topic_data"))

            if campaign["status"] != "WAITING_FOR_REVIEW":
                return GenericResponse(status="error", message="Bước này đang được xử lý hoặc đã duyệt rồi ạ.")

            if step == 6:
                # Terminal Step: Publish to News + Cleanup
                success = await self._publish_and_cleanup(campaign, session)
                if success:
                    await session.commit()

                    # Notify Responder to announce success
                    await event_bus.emit("CONTENT_STEP_COMPLETED", {
                        "campaign_id": campaign_id,
                        "user_id": campaign["user_id"],
                        "step": 6,
                        "status": "COMPLETED",
                        "tenant_id": campaign["tenant_id"]
                    })

                    return GenericResponse(
                        status="success",
                        message="🎉 Chúc mừng sếp! Bài viết đã được xuất bản vào mục 'Tin tức' và hệ thống đã được dọn dẹp sạch sẽ ạ.",
                        data={"campaign_id": campaign_id, "next_step": 7}
                    )
                else:
                    return GenericResponse(status="error", message="Dạ sếp, có lỗi khi xuất bản bài viết. Sếp thử lại giúp em nhé.")

            update_fields["current_step"] = step + 1
            update_fields["status"] = "PROCESSING"

            await campaign_service.update_campaign(session, campaign_id, update_fields)
            target_step = update_fields["current_step"]
            await session.commit()

            # Ensure we don't exceed max steps
            if target_step <= 6:
                asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id, force_step=target_step))
            return GenericResponse(status="success", message=f"Dạ sếp, em đang bắt đầu Bước {target_step} ạ.", data={"campaign_id": campaign_id, "next_step": target_step})
        else:
            await campaign_service.update_campaign(session, campaign_id, {"status": "REJECTED"})
            await session.commit()
            return GenericResponse(status="success", message="Đã ghi nhận sếp không duyệt bước này.", data={"campaign_id": campaign_id})

    async def _publish_and_cleanup(self, campaign: Dict[str, object], session: AsyncSession) -> bool:
        """
        Phase 76.3: Publication to News (Articles) + Hard Memory Cleanup.
        Moves final content to the public table and strips heavy JSON from campaign to save 2GB RAM.
        """
        try:
            # 1. Extract values (Zero-Hydration dict access)
            gold_meta = campaign.get("gold_metadata") or {}
            topic_data = campaign.get("topic_data") or {}

            title = gold_meta.get("topic") or gold_meta.get("title") or topic_data.get("title", "Bài viết sáng tạo mới")
            content = campaign.get("final_html") or campaign.get("draft_content")

            if not content:
                logger.warning(f"[ActionHandler] No content found for campaign {campaign['id']}")
                return False

            article_req = CreateArticleRequest(
                title=title,
                content=content,
                authorId=campaign.get("user_id"),
                status="PUBLISHED",
                category="Tin tức"
            )

            # ContentService handles slug generation and embedding
            new_article = await content_service.create_article(session, article_req)
            logger.info(f"[ActionHandler] Published campaign {campaign['id']} to Article {new_article['id']} via ContentService")

            # 2. Hard Cleanup (Rule R82.25: Zero-Allocation & Memory Safety)
            # Strip heavy metadata to keep DB and memory lean on 2GB RAM VPS
            await campaign_service.update_campaign(session, campaign["id"], {
                "status": "COMPLETED",
                "topic_data": {},
                "assets_data": [],
                "outline_data": {},
                "draft_content": "",
                "final_html": ""
            })

            logger.info(f"[ActionHandler] Published campaign {campaign['id']} and cleaned up.")
            return True
        except Exception as e:
            logger.exception(f"[ActionHandler] Publication failed for campaign {campaign['id']}: {e}")
            return False

    async def retry_step(self, campaign_id: str, session: AsyncSession) -> GenericResponse:
        campaign = await campaign_service.get_campaign(session, campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        await campaign_service.update_campaign(session, campaign_id, {"status": "PROCESSING"})
        step_val = campaign["current_step"]
        await session.commit()

        asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id, force_step=step_val))
        return GenericResponse(status="success", message=f"Em đang chạy lại bước {step_val} cho sếp đây!", data={"campaign_id": campaign_id})

    async def update_metadata(self, campaign_id: str, data: Dict[str, object], session: AsyncSession) -> GenericResponse:
        update_fields = {}
        for field in ["assets", "keywords", "outline_data", "draft_content", "final_html"]:
            val = data.get(field)
            if val is not None:
                if field == "assets": update_fields["assets_data"] = val
                elif field == "keywords": update_fields["topic_data"] = val
                else: update_fields[field] = val

        avatar = data.get("avatar")
        selected_index = data.get("selected_index")
        if avatar or selected_index is not None:
            # Need current gold_metadata to merge
            campaign = await campaign_service.get_campaign(session, campaign_id)
            if campaign:
                gold = dict(campaign.get("gold_metadata") or {})
                if avatar: gold["avatar"] = avatar
                if selected_index is not None: gold["selected_index"] = selected_index
                update_fields["gold_metadata"] = gold

        if update_fields:
            await campaign_service.update_campaign(session, campaign_id, update_fields)
            await session.commit()

        return GenericResponse(status="success", message="Neural data synchronized.", data={"campaign_id": campaign_id})

