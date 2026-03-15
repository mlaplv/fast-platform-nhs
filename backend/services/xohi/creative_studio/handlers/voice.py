import uuid
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Union, List
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import TopicSeed, CampaignCategory
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.event_bus import event_bus
from backend.services.ai_engine.core.trinity_bridge import AIConfigurationError
from litestar.repository.filters import LimitOffset

logger = logging.getLogger("api-gateway")

class VoiceHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def get_active_campaign(self, campaign_repo: ContentCampaignRepository, user_id: Optional[str] = None, tenant_id: str = "default", query: Optional[str] = None, campaign_id: Optional[str] = None) -> Optional[ContentCampaign]:
        if user_id == "undefined" or not user_id:
            user_id = None

        # 1. Explicit ID lookup (Highest Priority)
        if campaign_id:
            try:
                c = await campaign_repo.get(campaign_id)
                if c and c.status not in ["COMPLETED", "REJECTED"]:
                    return c
            except Exception: pass

        # 2. Strict scan for unfinished campaigns (Global Management)
        results = await campaign_repo.list(
            LimitOffset(limit=5, offset=0),
            order_by=[("created_at", "desc")],
            deleted_at=None
        )
        
        # Filter for truly active (not dead) campaigns
        active_campaigns = [c for c in results if c.status not in ["COMPLETED", "REJECTED"]]
        if not active_campaigns:
            return None

        # 3. Query-based matching
        if query:
            q_norm = query.lower()
            for c in active_campaigns:
                title = c.topic_data.get("title", "").lower() if c.topic_data else ""
                source = c.source_input.lower() if c.source_input else ""
                # R104: Tighter matching to avoid "Neural Link" hallucinations
                if (title and title in q_norm) or (source and source in q_norm):
                    return c
        
        # 4. Fallback: Return the most recent active one if it's very fresh (< 10 mins)
        latest = active_campaigns[0]
        now = datetime.now(timezone.utc)
        created_at = latest.created_at.replace(tzinfo=timezone.utc) if latest.created_at.tzinfo is None else latest.created_at
        if (now - created_at).total_seconds() < 600.0:
             return latest

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
        resume_keywords = ["tiếp", "làm tiếp", "chạy tiếp", "duyệt đi", "tiếp tục", "ok", "đúng", "vâng"]
        force_new_keywords = ["mới", "bỏ qua", "hủy", "tạo bài khác", "viết bài khác"]
        
        is_resume_request = any(kw in t_lower for kw in resume_keywords)
        is_force_new = any(kw in t_lower for kw in force_new_keywords)

        # Detect Category (Global Class Enum)
        category = CampaignCategory.CREATIVE_CONTENT
        if any(kw in t_lower for kw in ["quảng cáo", "ads", "marketing", "facebook ads", "google ads"]):
            category = CampaignCategory.AD_MANAGEMENT

        try:
            # 1. Safety Gate: Detect Conflict
            # Check for campaign_id in intent_data (e.g. from Dashboard)
            target_id = intent_data.get("campaign_id") if intent_data else None
            stale = await self.get_active_campaign(campaign_repo, user_id, tenant_id, query=transcript if not is_resume_request else None, campaign_id=target_id)

            if stale and not is_force_new:
                # Type sanity: check category if present
                stale_cat = getattr(stale, "category", CampaignCategory.CREATIVE_CONTENT)
                
                # Rule R82: Explicit Resume (or "ok" confirmation)
                if is_resume_request or target_id == stale.id:
                    if stale.status == "WAITING_FOR_REVIEW":
                        return await self.orchestrator.approve_step(stale.id, {"approved": True}, campaign_repo)
                    else:
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=self.format_resume_greeting(stale),
                            router_tier=RouterTier.TIER_2_SEMANTIC,
                            data={
                                "category": "CONTENT_CREATE",
                                "intent_type": "CONTENT_CREATE",
                                "ui_action": "show_content_factory",
                                "campaign_id": stale.id,
                                "step": stale.current_step,
                                "campaign_category": stale_cat
                            },
                            cost_tokens=0.0
                        )

                # Conflict Detection: User asks for something NEW while a campaign is ACTIVE
                # If they didn't explicitly say "tiếp", and the new request doesn't match the current one
                if not is_resume_request:
                    title = stale.topic_data.get("title", "bài viết cũ")
                    return IntentResponse(
                        status="success", action=IntentAction.CONTENT_CREATE,
                        message=f"Dạ sếp, em thấy bài '{title}' ({stale_cat}) đang làm dở. Sếp muốn làm tiếp hay hủy bài đó để tạo bài mới này ạ?",
                        router_tier=RouterTier.TIER_2_SEMANTIC,
                        data={
                            "category": "CONTENT_CREATE",
                            "intent_type": "CONTENT_CREATE",
                            "ui_action": "show_content_factory",
                            "campaign_id": stale.id,
                            "step": stale.current_step,
                            "pending_review": True,
                            "conflict_detected": True,
                            "new_request": transcript,
                            "campaign_category": stale_cat
                        },
                        cost_tokens=0.0
                    )

            # 2. Execution Phase: Create New Campaign
            # If user said "hủy" or "mới", or there was no stale campaign
            if is_force_new and stale:
                logger.info(f"[SafetyGate] Overwriting stale campaign {stale.id} as per user request")
                # Optional: mark as rejected instead of deleting?
                stale.status = "REJECTED"
                await campaign_repo.update(stale)

            # Phase 77: Inject content_mode into gold_metadata
            gold_meta = {}
            if intent_data and "content_mode" in intent_data:
                gold_meta["content_mode"] = intent_data["content_mode"]
                logger.info(f"[Phase 77] Content Mode detected: {gold_meta['content_mode']}")

            campaign = ContentCampaign(
                id=str(uuid.uuid4()), user_id=user_id, source_input=transcript,
                tenant_id=tenant_id, current_step=1, status="PROCESSING", 
                gold_metadata=gold_meta, category=category.value
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
                data={
                    "category": "CONTENT_CREATE",
                    "intent_type": "CONTENT_CREATE",
                    "ui_action": "show_content_factory",
                    "action": "STEP1_REVIEW",
                    "campaign_id": c_id,
                    "status": "WAITING_FOR_REVIEW",
                    "keywords": seed_data,
                    "step": 1,
                    "campaign_category": category.value
                },
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
