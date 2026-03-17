import uuid
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Union, List, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.campaign_service import campaign_service

if TYPE_CHECKING:
    from backend.services.creative_studio.orchestrator import ContentOrchestrator
from backend.schemas.campaign import TopicSeed, CampaignCategory
from backend.utils.text import sanitize_id, normalize_vn
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.event_bus import event_bus
from backend.services.ai_engine.trinity_bridge import AIConfigurationError

logger = logging.getLogger("api-gateway")

class VoiceHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

    async def get_active_campaign(self, session: AsyncSession, user_id: Optional[str] = None, tenant_id: str = "default", query: Optional[str] = None, campaign_id: Optional[str] = None) -> Optional[Dict[str, object]]:
        """Elite V2.2: Zero-Hydration lookup via CampaignService."""
        return await campaign_service.get_active_campaign(session, user_id, tenant_id, query, campaign_id)

    def format_resume_greeting(self, campaign: Dict[str, object]) -> str:
        step = campaign["current_step"]
        topic_data = campaign.get("topic_data") or {}
        title = topic_data.get("title", "bài viết mới")
        if campaign["status"] == "PROCESSING":
            return f"Dạ sếp, em đang tiếp tục thực hiện Bước {step} cho bài viết '{title}' ạ. Sếp đợi em một chút nhé!"
        else:
            return f"Dạ sếp, em đã sẵn sàng ở Bước {step} cho bài viết '{title}'. Mời sếp xem qua và duyệt để em chạy tiếp ạ!"

    async def handle_request(
        self, transcript: str, session: AsyncSession,
        tenant_id: str = "default", user_id: Optional[str] = None,
        intent_data: Optional[Dict[str, object]] = None
    ) -> IntentResponse:
        # Standardize user_id logic
        user_id = sanitize_id(user_id)

        t_norm = normalize_vn(transcript)
        # Standardized keywords (no accents, lowercase)
        resume_keywords = ["tiep", "lam tiep", "chay tiep", "duyet di", "tiep tuc", "ok", "dung", "vang"]
        force_new_keywords = ["moi", "bo qua", "huy", "tao bai khac", "viet bai khac"]

        is_resume_request = any(kw in t_norm for kw in resume_keywords)
        is_force_new = any(kw in t_norm for kw in force_new_keywords)

        # Detect Category (Global Class Enum)
        category = CampaignCategory.CREATIVE_CONTENT
        if any(kw in t_norm for kw in ["quang cao", "ads", "marketing", "facebook ads", "google ads"]):
            category = CampaignCategory.AD_MANAGEMENT

        try:
            # 1. Safety Gate: Detect Conflict
            # Check for campaign_id in intent_data (e.g. from Dashboard)
            target_id = sanitize_id(intent_data.get("campaign_id")) if intent_data else None
            stale = await self.get_active_campaign(session, user_id, tenant_id, query=transcript if not is_resume_request else None, campaign_id=target_id)

            if stale and not is_force_new:
                # Type sanity: check category if present
                stale_cat = stale.get("category", CampaignCategory.CREATIVE_CONTENT)

                # Rule R82: Explicit Resume (or "ok" confirmation)
                if is_resume_request or target_id == stale["id"]:
                    if stale["status"] == "WAITING_FOR_REVIEW":
                        return await self.orchestrator.approve_step(stale["id"], {"approved": True}, session)
                    else:
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=self.format_resume_greeting(stale),
                            router_tier=RouterTier.TIER_2_SEMANTIC,
                            data={
                                "category": "CONTENT_CREATE",
                                "intent_type": "CONTENT_CREATE",
                                "ui_action": "show_content_factory",
                                "campaign_id": stale["id"],
                                "step": stale["current_step"],
                                "campaign_category": stale_cat
                            },
                            cost_tokens=0.0
                        )

                # Conflict Detection: User asks for something NEW while a campaign is ACTIVE
                # If they didn't explicitly say "tiếp", and the new request doesn't match the current one
                if not is_resume_request:
                    title = stale.get("topic_data", {}).get("title", "bài viết cũ")
                    return IntentResponse(
                        status="success", action=IntentAction.CONTENT_CREATE,
                        message=f"Dạ sếp, em thấy bài '{title}' ({stale_cat}) đang làm dở. Sếp muốn làm tiếp hay hủy bài đó để tạo bài mới này ạ?",
                        router_tier=RouterTier.TIER_2_SEMANTIC,
                        data={
                            "category": "CONTENT_CREATE",
                            "intent_type": "CONTENT_CREATE",
                            "ui_action": "show_content_factory",
                            "campaign_id": stale["id"],
                            "step": stale["current_step"],
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
                logger.info(f"[SafetyGate] Overwriting stale campaign {stale['id']} as per user request")
                await campaign_service.update_campaign(session, stale["id"], {"status": "REJECTED"})

            # Phase 77: Inject content_mode into gold_metadata
            gold_meta = {}
            if intent_data and "content_mode" in intent_data:
                gold_meta["content_mode"] = intent_data["content_mode"]
                logger.info(f"[Phase 77] Content Mode detected: {gold_meta['content_mode']}")

            campaign = await campaign_service.create_campaign(
                session=session,
                user_id=user_id,
                source_input=transcript,
                tenant_id=tenant_id,
                gold_metadata=gold_meta,
                category=category.value
            )
            c_id = campaign["id"]
            u_id_str = str(campaign["user_id"]) if campaign["user_id"] else "default"
            await session.commit()

            seed: TopicSeed = await self.orchestrator.vision.analyze_input(
                transcript,
                c_id,
                u_id_str,
                content_mode=gold_meta.get("content_mode", "viral")
            )
            seed_data = seed.model_dump()

            await campaign_service.update_campaign(session, c_id, {
                "topic_data": seed_data,
                "status": "WAITING_FOR_REVIEW"
            })

            await session.commit()

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
            await session.rollback()
            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message=f"Dạ sếp, có lỗi hệ thống: {str(e)}. Sếp thử lại sau nhé!",
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={"category": "CONTENT_CREATE", "source_input": transcript},
                cost_tokens=0.0
            )

