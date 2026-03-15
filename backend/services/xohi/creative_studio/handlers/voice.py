import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Union
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import TopicSeed
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.event_bus import event_bus
from backend.services.ai_engine.core.trinity_bridge import AIConfigurationError
from litestar.repository.filters import LimitOffset

logger = logging.getLogger("api-gateway")

class VoiceHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def get_active_campaign(self, campaign_repo: ContentCampaignRepository, user_id: Optional[str] = None, tenant_id: str = "default", query: Optional[str] = None) -> Optional[ContentCampaign]:
        if user_id == "undefined" or not user_id:
            user_id = None

        # R104: Scan last 5 campaigns for potential resume (V76.2)
        results = await campaign_repo.list(
            LimitOffset(limit=5, offset=0),
            order_by=[("created_at", "desc")],
            deleted_at=None
        )

        # If a query is provided, try to find a title/keyword match first
        if query:
            q_norm = query.lower()
            for c in results:
                title = c.topic_data.get("title", "").lower() if c.topic_data else ""
                source = c.source_input.lower() if c.source_input else ""
                # Strict match: Query must relate to the title or original input
                if (title and (title in q_norm or q_norm in title)) or (source and (source in q_norm or q_norm in source)):
                    return c
            # If query doesn't match any recent campaign, DO NOT resume a random one
            return None
        return None

    def format_resume_greeting(self, campaign: ContentCampaign) -> str:
        step = campaign.current_step
        title = campaign.topic_data.get("title", "bài viết mới") if campaign.topic_data else "bài viết mới"
        if campaign.status == "PROCESSING":
            return f"Dạ sếp, em đang tiếp tục thực hiện Bước {step} cho bài viết '{title}' ạ. Sếp đợi em một chút nhé!"
        else:
            return f"Dạ sếp, em đã sẵn sàng ở Bước {step} cho bài viết '{title}'. Mời sếp xem qua và duyệt để em chạy tiếp ạ!"

    async def handle_request(
        self, transcript: str, campaign_repo: ContentCampaignRepository,
        tenant_id: str = "default", user_id: Optional[str] = None,
        intent_data: Optional[Dict] = None
    ) -> IntentResponse:
        if user_id == "undefined" or not user_id:
            user_id = None

        t_lower = transcript.lower()
        resume_keywords = ["tiếp", "làm tiếp", "chạy tiếp", "duyệt đi", "tiếp tục"]
        is_resume_request = any(kw in t_lower for kw in resume_keywords)

        try:
            # V76.2: Smarter Resume Detection
            stale = await self.get_active_campaign(campaign_repo, user_id, tenant_id, query=transcript if not is_resume_request else None)

            if stale:
                # 1. Explicit Resume Request
                if is_resume_request:
                    if stale.status == "WAITING_FOR_REVIEW":
                        # If user says "approve" or "tiếp" while waiting for review, proceed
                        return await self.orchestrator.approve_step(stale.id, {"approved": True}, campaign_repo)
                    else:
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=self.format_resume_greeting(stale),
                            router_tier=RouterTier.TIER_2_SEMANTIC, data={"campaign_id": stale.id, "step": stale.current_step}, cost_tokens=0.0
                        )

                # 2. Idempotency Latch (Extended to 5 mins for V76.2)
                now = datetime.now(timezone.utc)
                stale_time = stale.created_at
                if stale_time.tzinfo is None:
                    stale_time = stale_time.replace(tzinfo=timezone.utc)

                if (now - stale_time).total_seconds() < 300.0:
                    # If user repeats a request for a very recent campaign, don't create a duplicate
                    if stale.status == "WAITING_FOR_REVIEW":
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=f"Dạ sếp, bài viết '{stale.topic_data.get('title', 'này')}' em vừa phân tích xong. Mời sếp duyệt trên màn hình ạ!",
                            router_tier=RouterTier.TIER_2_SEMANTIC, data={"campaign_id": stale.id, "step": stale.current_step, "keywords": stale.topic_data}, cost_tokens=0.0
                        )

                    # 3. Proactive Reminder (V76.2)
                    # If user asks for something NEW while a RECENT campaign is pending review
                    if not is_resume_request and stale.status == "WAITING_FOR_REVIEW":
                        title = stale.topic_data.get("title", "bài viết cũ")
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=f"Dạ sếp, em thấy bài '{title}' đang chờ sếp duyệt ở Bước {stale.current_step}. Sếp muốn em làm tiếp bài đó hay khởi tạo bài mới này ạ?",
                            router_tier=RouterTier.TIER_2_SEMANTIC,
                            data={"campaign_id": stale.id, "step": stale.current_step, "pending_review": True, "new_request": transcript},
                            cost_tokens=0.0
                        )

            # Phase 77: Inject content_mode into gold_metadata
            gold_meta = {}
            if intent_data and "content_mode" in intent_data:
                gold_meta["content_mode"] = intent_data["content_mode"]
                logger.info(f"[Phase 77] Content Mode detected: {gold_meta['content_mode']}")

            campaign = ContentCampaign(
                id=str(uuid.uuid4()), user_id=user_id, source_input=transcript,
                tenant_id=tenant_id, current_step=1, status="PROCESSING", gold_metadata=gold_meta
            )
            c_id = campaign.id
            u_id_str = str(campaign.user_id) if campaign.user_id else "default"
            await campaign_repo.add(campaign)
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()
                await campaign_repo.session.refresh(campaign)

            seed: TopicSeed = await self.orchestrator.vision.analyze_input(
                transcript,
                c_id,
                u_id_str,
                content_mode=gold_meta.get("content_mode", "viral")
            )
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
                message=f"Dạ sếp, hệ thống AI đang tạm thời gián đoạn: {str(ae)}. Sếp đợi vài phút hoặc kiểm tra cấu hình Key nhé!",
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
