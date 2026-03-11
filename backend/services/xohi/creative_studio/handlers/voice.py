import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import TopicSeed
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.event_bus import event_bus
from backend.services.ai_engine.core.trinity_bridge import AIConfigurationError
from litestar.repository.filters import LimitOffset

logger = logging.getLogger("api-gateway")

class VoiceHandler:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def get_active_campaign(self, campaign_repo: ContentCampaignRepository, user_id: str = None, tenant_id: str = "default") -> Optional[ContentCampaign]:
        if user_id == "undefined" or not user_id:
            user_id = None

        results = await campaign_repo.list(
            LimitOffset(limit=5, offset=0),
            order_by=[("created_at", "desc")],
            deleted_at=None
        )
        for c in results:
            if c.status in ["PROCESSING", "WAITING_FOR_REVIEW"] and c.tenant_id == tenant_id:
                if user_id and c.user_id == user_id:
                    return c
                elif not user_id:
                    return c
        return None

    def format_resume_greeting(self, campaign: ContentCampaign) -> str:
        step = campaign.current_step
        title = campaign.topic_data.get("title", "bài viết mới")
        if campaign.status == "PROCESSING":
            return f"Chào sếp, em đang tiếp tục thực hiện Bước {step} cho bài viết '{title}' ạ. Sếp đợi em chút nhé!"
        else:
            return f"Chào sếp, em đã hoàn thành xong Bước {step} cho bài viết '{title}'. Mời sếp xem qua và duyệt để em chạy tiếp ạ!"

    async def handle_request(
        self, transcript: str, campaign_repo: ContentCampaignRepository,
        tenant_id: str = "default", user_id: str = None
    ) -> IntentResponse:
        if user_id == "undefined" or not user_id:
            user_id = None

        try:
            stale = await self.get_active_campaign(campaign_repo, user_id, tenant_id)
            if stale:
                if "tiếp" in transcript.lower():
                    if stale.status == "WAITING_FOR_REVIEW":
                        return await self.orchestrator.approve_step(stale.id, {"approved": True}, campaign_repo)
                    else:
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=self.format_resume_greeting(stale),
                            router_tier=RouterTier.TIER_2_SEMANTIC, data={"campaign_id": stale.id, "step": stale.current_step}, cost_tokens=0.0
                        )
                
                # Idempotency Latch
                now = datetime.now(timezone.utc)
                stale_time = stale.created_at
                if stale_time.tzinfo is None:
                    stale_time = stale_time.replace(tzinfo=timezone.utc)
                if (now - stale_time).total_seconds() < 15.0:
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

            campaign = ContentCampaign(
                id=str(uuid.uuid4()), user_id=user_id, source_input=transcript,
                tenant_id=tenant_id, current_step=1, status="PROCESSING", gold_metadata={}
            )
            c_id = campaign.id
            u_id_str = str(campaign.user_id) if campaign.user_id else "default"
            await campaign_repo.add(campaign)
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()
                await campaign_repo.session.refresh(campaign)

            seed: TopicSeed = await self.orchestrator.vision.analyze_input(transcript, c_id, u_id_str)
            seed_data = seed.model_dump()
            campaign.topic_data = seed_data
            campaign.status = "WAITING_FOR_REVIEW"
            await campaign_repo.update(campaign)
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()

            await event_bus.emit("CONTENT_STEP_COMPLETED", {
                "campaign_id": c_id, "step": 1, "status": "WAITING_FOR_REVIEW",
                "user_id": u_id_str, "data": {"keywords": seed_data}
            })

            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message=f"Dạ sếp, em đã phân tích xong từ khóa cho chủ đề '{seed_data.get('title', 'mới')}'. Mời sếp duyệt trên màn hình ạ!",
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={"category": "CONTENT_CREATE", "action": "STEP1_REVIEW", "campaign_id": c_id, "status": "WAITING_FOR_REVIEW", "keywords": seed_data, "step": 1},
                cost_tokens=0.0
            )

        except AIConfigurationError as ae:
            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message=f"Dạ sếp, lỗi LLM: {str(ae)}. Sếp kiểm tra lại Key hoặc Model trong .env nhé!",
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={"category": "CONTENT_CREATE", "source_input": transcript, "error_type": "AI_CONFIG"},
                cost_tokens=0.0
            )
        except Exception as e:
            logger.exception(f"[VoiceHandler] Execution failed: {e}")
            if campaign_repo and hasattr(campaign_repo, "session"):
                await campaign_repo.session.rollback()
            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message=f"Dạ sếp, có lỗi hệ thống: {str(e)}. Sếp thử lại sau nhé!",
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={"category": "CONTENT_CREATE", "source_input": transcript},
                cost_tokens=0.0
            )
