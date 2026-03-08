import os
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from src.database.models import ContentCampaign
from src.database.repositories import ContentCampaignRepository
from src.services.xohi.creative_studio.models.vision_insight import VisionInsight, TopicSeed
from src.services.xohi.creative_studio.operatives.asset_hunter import AssetHunter
from src.services.xohi.creative_studio.models.creative_pen import CreativePen
from src.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
from src.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
from shared.schemas.intent import IntentResponse, IntentAction, RouterTier
from src.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")


class ContentOrchestrator:
    """
    The brain of V62.1 Content Factory. 
    Manages the 6-step state machine with the Hardened "Golden Thread" logic.
    """

    def __init__(self):
        self.vision = VisionInsight()
        
        # Initialize AssetHunter with 3 key pairs from .env (Rule R90)
        keys = []
        for i in ["", "_1", "_2"]:
            k = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}")
            cx = os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
            if k and cx:
                keys.append({"key": k, "cx": cx})
        
        self.hunter = AssetHunter(keys)

    async def get_latest_pending(self, campaign_repo: ContentCampaignRepository, tenant_id: str = "default") -> Optional[ContentCampaign]:
        """Find the most recent campaign that is waiting for review."""
        results = await campaign_repo.list(
            limit_offset=None, # list all or use filter
            order_by=[("created_at", "desc")],
            deleted_at=None
        )
        # Filter manually for simplicity or use repo.get_one_or_none with filters if available
        for c in results:
            if c.status == "WAITING_FOR_REVIEW" and c.tenant_id == tenant_id:
                return c
        return None

    # ══════════════════════════════════════════
    # ENTRY POINT: Voice/Text → Auto Step 1
    # ══════════════════════════════════════════

    async def handle_voice_request(
        self, transcript: str, context: list = None, 
        campaign_repo: ContentCampaignRepository = None,
        tenant_id: str = "default"
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
            # 1. Resume Check: Nếu đang có bài dang dở, ưu tiên hỏi tiếp (R81: Continuity)
            stale = await self.get_latest_pending(campaign_repo, tenant_id)
            if stale and "tiếp" in transcript.lower():
                # Pseudo-intent: User wants to resume
                return await self.approve_step(stale.id, {"approved": True}, campaign_repo)

            # 1. Tạo campaign trong DB ngay lập tức (R86: Persistence)
            campaign = ContentCampaign(
                id=str(uuid.uuid4()),
                source_input=transcript,
                tenant_id=tenant_id,
                current_step=1,
                status="PROCESSING",
                gold_metadata={},
                error_logs=[],
                search_count=0
            )
            campaign = await campaign_repo.add(campaign)
            logger.info(f"[Content Factory] Campaign created: {campaign.id}")

            # 2. Gọi VisionInsight (AI) sinh keywords (Step 1)
            seed: TopicSeed = await self.vision.analyze_input(campaign)

            # 3. Lưu keywords vào DB (R86: Resume-able)
            campaign.topic_data = seed.model_dump()
            campaign.status = "WAITING_FOR_REVIEW"
            await campaign_repo.update(campaign)
            logger.info(f"[Content Factory] Step 1 done: {campaign.id} → WAITING_FOR_REVIEW")

            # 4. Format response cho voice + UI card
            voice_msg = self._format_keywords_for_voice(seed)

            # 5. Notify Nerve System for UI tracking
            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": campaign.id,
                "step": 1,
                "status": "WAITING_FOR_REVIEW",
                "tenant_id": tenant_id
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
                    "keywords": seed.model_dump(),
                    "step": 1
                },
                cost_tokens=0.0
            )

        except Exception as e:
            logger.error(f"[Content Factory] handle_voice_request failed: {e}")
            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message="Dạ sếp, em ghi nhận chủ đề rồi nhưng AI đang bận. Sếp thử lại sau chút nhé!",
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={"category": "CONTENT_CREATE", "source_input": transcript},
                cost_tokens=0.0
            )

    def _format_keywords_for_voice(self, seed: TopicSeed) -> str:
        """Format TopicSeed thành câu nói tự nhiên cho XoHi voice."""
        kw_list = ", ".join(seed.secondary_keywords[:3])
        return (
            f"Dạ sếp, em gợi ý cho bài viết như sau. "
            f"Tiêu đề: {seed.title}. "
            f"Từ khóa chính: {seed.primary_keyword}. "
            f"Từ khóa phụ: {kw_list}. "
            f"Phong cách: {seed.persona}. "
            f"Sếp duyệt bộ keyword này để em chạy tiếp không ạ?"
        )

    # ══════════════════════════════════════════
    # STEP EXECUTION METHODS (existing)
    # ══════════════════════════════════════════

    async def run_step_1_vision(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        try:
            seed = await self.vision.analyze_input(campaign)
            campaign.topic_data = seed.model_dump()
            campaign.status = "WAITING_FOR_REVIEW"
            await campaign_repo.update(campaign)
        except Exception as e:
            await self._log_error(campaign_id, campaign_repo, "ERROR", str(e))

    async def run_step_2_hunting(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        try:
            # Rule R90: Search Quota Enforcement (Max 3)
            if (campaign.search_count or 0) >= 3:
                logger.warning(f"[Content Factory] Search Quota EXHAUSTED for {campaign_id}")
                campaign.status = "WAITING_FOR_REVIEW"
                await campaign_repo.update(campaign)
                return

            query = campaign.topic_data.get("primary_keyword", campaign.source_input)
            urls = await self.hunter.fetch_images(query)
            
            campaign.assets_data = urls
            campaign.status = "WAITING_FOR_REVIEW"
            campaign.search_count = (campaign.search_count or 0) + 1
            await campaign_repo.update(campaign)
            
            # Notify Nerve System
            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": campaign.id,
                "step": 2,
                "status": "WAITING_FOR_REVIEW",
                "tenant_id": campaign.tenant_id,
                "data": {"keywords": campaign.topic_data, "assets": urls}
            })
        except Exception as e:
            await self._log_error(campaign_id, campaign_repo, "COOLDOWN", str(e))

    async def run_step_3_outline(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        try:
            pen = CreativePen()
            outline = await pen.generate_outline(campaign)
            campaign.outline_data = outline.model_dump()
            campaign.status = "WAITING_FOR_REVIEW"
            await campaign_repo.update(campaign)
            
            # Notify Nerve System
            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": campaign.id,
                "step": 3,
                "status": "WAITING_FOR_REVIEW",
                "tenant_id": campaign.tenant_id,
                "data": {"outline": campaign.outline_data}
            })
        except Exception as e:
            await self._log_error(campaign_id, campaign_repo, "ERROR", str(e))

    async def run_step_4_drafting(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        try:
            pen = CreativePen()
            content = await pen.write_draft_stream(campaign)
            campaign.draft_content = content
            campaign.status = "WAITING_FOR_REVIEW"
            await campaign_repo.update(campaign)

            # Notify Nerve System
            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": campaign.id,
                "step": 4,
                "status": "WAITING_FOR_REVIEW",
                "tenant_id": campaign.tenant_id,
                "data": {"content_preview": content[:100] + "..."}
            })
        except Exception as e:
            await self._log_error(campaign_id, campaign_repo, "ERROR", str(e))

    async def run_step_5_plagiarism_check(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        try:
            cop = PlagiarismCop()
            await cop.run_audit(campaign)
            campaign.status = "WAITING_FOR_REVIEW"
            await campaign_repo.update(campaign)

            # Notify Nerve System
            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": campaign.id,
                "step": 5,
                "status": "WAITING_FOR_REVIEW",
                "tenant_id": campaign.tenant_id,
                "data": {"unique_score": campaign.unique_score}
            })
        except Exception as e:
            await self._log_error(campaign_id, campaign_repo, "ERROR", str(e))

    async def run_step_6_finalization(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        try:
            media = MediaCompressor()
            local_assets = await media.localize_assets(campaign)
            final_html = media.wrap_html(campaign.draft_content, local_assets, campaign.gold_metadata)
            campaign.final_html = final_html
            campaign.assets_data = local_assets
            campaign.status = "COMPLETED"
            campaign.current_step = 6
            await campaign_repo.update(campaign)

            # Notify Nerve System
            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": campaign.id,
                "step": 6,
                "status": "COMPLETED",
                "tenant_id": campaign.tenant_id
            })
        except Exception as e:
            await self._log_error(campaign_id, campaign_repo, "ERROR", str(e))

    # ══════════════════════════════════════════
    # APPROVAL GATE (R80: Human-in-the-loop)
    # ══════════════════════════════════════════

    async def approve_step(self, campaign_id: str, data: Dict[str, Any], 
                           campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """
        R80: Human-in-the-loop — Duyệt bước hiện tại và chạy tiếp.
        """
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        step = campaign.current_step
        approved = data.get("approved", True)
        feedback = data.get("feedback")
        edited_data = data.get("edited_data")

        logger.info(f"[Content Factory] Human Review step {step} for {campaign_id} (Approved: {approved})")

        if approved:
            # 1. Nếu có sửa data bằng tay (R80: Manual Edits Override)
            if edited_data:
                if step == 1: campaign.topic_data = edited_data
                elif step == 3: campaign.outline_data = edited_data
                elif step == 4: campaign.draft_content = edited_data.get("content", campaign.draft_content)

            # 2. Golden Thread Lockdown (Step 1 -> Gold Metadata)
            if step == 1:
                campaign.gold_metadata = campaign.topic_data

            # 3. Chuyển trạng thái sang PROCESSING để chạy AI bước sau
            campaign.current_step += 1
            campaign.status = "PROCESSING"
            await campaign_repo.update(campaign)

            # 4. Kích hoạt AI chạy bước tiếp theo (Async Fire-and-Forget trong môi trường dev)
            # Trong production nên dùng Task Queue (Celery/Redis), ở đây dùng asyncio.create_task
            import asyncio
            asyncio.create_task(self._trigger_next_step(campaign_id, campaign_repo))

            return {
                "status": "success", 
                "message": f"Duyệt bước {step} thành công. Em đang chạy tiếp bước {campaign.current_step} cho sếp!",
                "campaign_id": campaign_id,
                "next_step": campaign.current_step
            }
        else:
            # Sếp không duyệt (Feedback)
            campaign.status = "REJECTED"
            await campaign_repo.update(campaign)
            return {"status": "success", "message": "Đã ghi nhận sếp không duyệt bước này.", "campaign_id": campaign_id}

    async def retry_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        """Retry the current step (Force Re-generate)."""
        campaign = await campaign_repo.get(campaign_id)
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        campaign.status = "PROCESSING"
        await campaign_repo.update(campaign)

        import asyncio
        asyncio.create_task(self._run_current_step(campaign_id, campaign_repo))

        return {"status": "success", "message": f"Em đang chạy lại bước {campaign.current_step} cho sếp đây!", "campaign_id": campaign_id}

    async def _trigger_next_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        """Background executor for the next step."""
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        await self._run_current_step(campaign_id, campaign_repo)

    async def _run_current_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository):
        """Map current_step to the correct worker method."""
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        
        step = campaign.current_step
        logger.info(f"[Content Factory] Background run: Step {step} for {campaign_id}")
        
        try:
            if step == 1: await self.run_step_1_vision(campaign_id, campaign_repo)
            elif step == 2: await self.run_step_2_hunting(campaign_id, campaign_repo)
            elif step == 3: await self.run_step_3_outline(campaign_id, campaign_repo)
            elif step == 4: await self.run_step_4_drafting(campaign_id, campaign_repo)
            elif step == 5: await self.run_step_5_plagiarism_check(campaign_id, campaign_repo)
            elif step == 6: await self.run_step_6_finalization(campaign_id, campaign_repo)
        except Exception as e:
            logger.error(f"[Content Factory] Step {step} failed: {e}")
            await self._log_error(campaign_id, campaign_repo, "ERROR", str(e))

    # ══════════════════════════════════════════
    # INTERNAL HELPERS
    # ══════════════════════════════════════════

    async def _log_error(self, campaign_id: str, campaign_repo: ContentCampaignRepository, 
                         status: str, error_msg: str):
        campaign = await campaign_repo.get(campaign_id)
        if not campaign: return
        campaign.status = status
        if not campaign.error_logs:
            campaign.error_logs = []
        campaign.error_logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": campaign.current_step,
            "error": error_msg
        })
        await campaign_repo.update(campaign)


# Singleton — import from anywhere
content_factory = ContentOrchestrator()
