import asyncio
import logging
import uuid
import numpy as np
from typing import Dict, Union, Optional
from backend.database.repositories import ContentCampaignRepository, ArticleRepository, ArticleEmbeddingRepository
from backend.database.models import Article, ArticleEmbedding
from backend.utils.text import slugify
from backend.services.event_bus import event_bus
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder

logger = logging.getLogger("api-gateway")

class ActionHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def approve_step(self, campaign_id: str, data: Dict[str, object], campaign_repo: ContentCampaignRepository) -> Dict[str, object]:
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

            if step == 6:
                # Terminal Step: Publish to News + Cleanup
                success = await self._publish_and_cleanup(campaign, campaign_repo)
                if success:
                    if hasattr(campaign_repo, "session"):
                        await campaign_repo.session.commit()

                    # Notify Responder to announce success
                    await event_bus.emit("CONTENT_STEP_COMPLETED", {
                        "campaign_id": campaign_id,
                        "user_id": campaign.user_id,
                        "step": 6,
                        "status": "COMPLETED",
                        "tenant_id": campaign.tenant_id
                    })

                    return {
                        "status": "success",
                        "message": "🎉 Chúc mừng sếp! Bài viết đã được xuất bản vào mục 'Tin tức' và hệ thống đã được dọn dẹp sạch sẽ ạ.",
                        "campaign_id": campaign_id,
                        "next_step": 7
                    }
                else:
                    return {"status": "error", "message": "Dạ sếp, có lỗi khi xuất bản bài viết. Sếp thử lại giúp em nhé."}

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

    async def _publish_and_cleanup(self, campaign, campaign_repo: ContentCampaignRepository) -> bool:
        """
        Phase 76.3: Publication to News (Articles) + Hard Memory Cleanup.
        Moves final content to the public table and strips heavy JSON from campaign to save 2GB RAM.
        """
        try:
            # 1. Ensure final_html is loaded (it is a deferred column)
            if hasattr(campaign_repo, "session"):
                from sqlalchemy import inspect
                ins = inspect(campaign)
                if "final_html" in ins.unloaded:
                    await campaign_repo.session.refresh(campaign, ["final_html"])

            # 2. Create Article (Tin tức)
            article_repo = ArticleRepository(session=campaign_repo.session)

            title = campaign.get_gold_val("topic") or campaign.get_gold_val("title", "Bài viết sáng tạo mới")
            content = campaign.final_html or campaign.draft_content

            if not content:
                logger.warning(f"[ActionHandler] No content found for campaign {campaign.id}")
                return False

            new_article = Article(
                id=str(uuid.uuid4()),
                title=title,
                slug=f"{slugify(title)}-{str(uuid.uuid4())[:8]}",
                content=content,
                author_id=campaign.user_id,
                status="PUBLISHED",
                tenant_id=campaign.tenant_id,
                category="Tin tức"
            )
            await article_repo.add(new_article)

            # 2.5. Generate and save Embedding (Phase 77: Deep Memory)
            try:
                encoder = get_shared_encoder()
                if encoder:
                    loop = asyncio.get_event_loop()
                    # We embed the title for semantic retrieval
                    vector = (await loop.run_in_executor(None, lambda: list(encoder.embed([title]))))[0]
                    vector_np = np.array(vector, dtype=np.float32)

                    emb_repo = ArticleEmbeddingRepository(session=campaign_repo.session)
                    new_emb = ArticleEmbedding(
                        id=str(uuid.uuid4()),
                        article_id=new_article.id,
                        embedding=vector_np.tobytes().hex()
                    )
                    await emb_repo.add(new_emb)
                    logger.info(f"[ActionHandler] Generated embedding for article {new_article.id}")
            except Exception as emb_err:
                logger.error(f"[ActionHandler] Embedding generation failed: {emb_err}")

            # 3. Hard Cleanup (Rule R82.25: Zero-Allocation & Memory Safety)
            campaign.status = "COMPLETED"
            # Strip heavy metadata to keep DB and memory lean on 2GB RAM VPS
            campaign.topic_data = {}
            campaign.assets_data = []
            campaign.outline_data = {}
            campaign.draft_content = ""
            campaign.final_html = ""

            await campaign_repo.update(campaign)
            logger.info(f"[ActionHandler] Published campaign {campaign.id} to Article {new_article.id} and cleaned up.")
            return True
        except Exception as e:
            logger.exception(f"[ActionHandler] Publication failed for campaign {campaign.id}: {e}")
            return False

    async def retry_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository) -> Dict[str, object]:
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

    async def update_metadata(self, campaign_id: str, data: Dict[str, object], campaign_repo: ContentCampaignRepository) -> Dict[str, object]:
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
