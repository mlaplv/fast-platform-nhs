import uuid
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Union, List
from backend.database.models import ContentCampaign, ChatMessage
import sqlalchemy as sa
from sqlalchemy import delete as sa_delete
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import TopicSeed, CampaignCategory
from backend.utils.text import sanitize_id, normalize_vn
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.event_bus import event_bus
from backend.services.ai_engine.core.trinity_bridge import AIConfigurationError
from litestar.repository.filters import LimitOffset
import asyncio
from backend.database.alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")

class VoiceHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator
        # [Elite V2.2] Decentralized Cleanup Registration
        event_bus.subscribe("XOHI_CAMPAIGN_PURGED", self._handle_campaign_purge)

    async def get_active_campaign(self, campaign_repo: ContentCampaignRepository, user_id: Optional[str] = None, tenant_id: str = "default", query: Optional[str] = None, campaign_id: Optional[str] = None) -> Optional[ContentCampaign]:
        # R105: Standardize user_id logic
        user_id = sanitize_id(user_id)
        campaign_id = sanitize_id(campaign_id)

        # 1. Explicit ID lookup (Highest Priority)
        if campaign_id:
            try:
                c = await campaign_repo.get(campaign_id)
                # [Elite V2.2] Terminal statuses: COMPLETED, REJECTED, FAILED
                if c and c.status not in ["COMPLETED", "REJECTED", "FAILED"]:
                    return c
            except Exception: pass

        # 2. Strict scan for unfinished campaigns (Scoped to User)
        filters = {"deleted_at": None}
        if user_id:
            filters["user_id"] = user_id

        results = await campaign_repo.list(
            LimitOffset(limit=5, offset=0),
            order_by=[("created_at", "desc")],
            **filters
        )
        
        # Filter for truly active (not dead) campaigns
        active_campaigns = [c for c in results if c.status not in ["COMPLETED", "REJECTED", "FAILED"]]
        if not active_campaigns:
            return None

        # 3. Query-based matching
        if query:
            q_norm = normalize_vn(query)
            for c in active_campaigns:
                title = normalize_vn(c.topic_data.get("title", "")) if c.topic_data else ""
                source = normalize_vn(c.source_input) if c.source_input else ""
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
        # R105: Standardize user_id logic
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
            stale = await self.get_active_campaign(campaign_repo, user_id, tenant_id, query=transcript if not is_resume_request else None, campaign_id=target_id)

            if stale:
                stale_cat = getattr(stale, "category", CampaignCategory.CREATIVE_CONTENT)
                title = stale.topic_data.get("title", "bài viết cũ")
                
                # Rule R82: Explicit Resume (or "ok" confirmation)
                if is_resume_request or target_id == stale.id:
                    if stale.status == "WAITING_FOR_REVIEW":
                        gr = await self.orchestrator.approve_step(stale.id, {"approved": True}, campaign_repo)
                        return IntentResponse(
                            status=gr.status, action=IntentAction.CONTENT_APPROVE, message=gr.message,
                            router_tier=RouterTier.TIER_2_SEMANTIC,
                            data={
                                "category": "CONTENT_CREATE", "intent_type": "CONTENT_CREATE", "ui_action": "show_content_factory",
                                "campaign_id": stale.id, "step": stale.current_step, "campaign_category": stale_cat,
                                **(gr.data or {})
                            },
                            cost_tokens=0.0
                        )
                    else:
                        return IntentResponse(
                            status="success", action=IntentAction.CONTENT_CREATE,
                            message=self.format_resume_greeting(stale),
                            router_tier=RouterTier.TIER_2_SEMANTIC,
                            data={
                                "category": "CONTENT_CREATE", "intent_type": "CONTENT_CREATE", "ui_action": "show_content_factory",
                                "campaign_id": stale.id, "step": stale.current_step, "campaign_category": stale_cat
                            },
                            cost_tokens=0.0
                        )

                # [Elite V2.2] SINGLE-TASK ARMOR: Hard block ANY new creation if active campaignexists.
                # No more "force new" bypass. User MUST finish or delete.
                return IntentResponse(
                    status="success", action=IntentAction.CONTENT_CREATE,
                    message=f"Hệ thống đang ưu tiên tài nguyên cho bài '{title}' ({stale.status}). Vui lòng hoàn thành bài hiện tại hoặc xóa nó đi trước khi yêu cầu viết bài mới.",
                    router_tier=RouterTier.TIER_2_SEMANTIC,
                    data={
                        "category": "CONTENT_CREATE", "intent_type": "CONTENT_CREATE", 
                        "campaign_id": stale.id, "step": stale.current_step, "conflict_detected": True,
                        "campaign_category": stale_cat, "armor_blocked": True
                    },
                    cost_tokens=0.0
                )

            # 2. Execution Phase: Create New Campaign
            # (Execution only reached if NO stale campaign exists)
            
            # CNS V85.1: Neural Intent Decoding (Vừng ơi mở cửa ra)
            gold_meta = {}
            clean_transcript = transcript
            
            # Article Intent
            if re.match(r"^(adm\s+)?(viet bai|van bai:?)\s*", t_norm, re.IGNORECASE):
                gold_meta["target_entity"] = "article"
                gold_meta["style"] = "Viral"
                clean_transcript = re.sub(r"^(adm\s+)?(viết bài:?\s*|vân bài:?\s*)", "", transcript, flags=re.IGNORECASE).strip()
                response_msg = f"Dạ thưa Sếp, em đã bẻ lái sang dây chuyền TIN TỨC để xử lý chủ đề '{clean_transcript}' đây ạ! 🚀"
            
            # Product Intent
            elif re.match(r"^(adm\s+)?(tao san pham|san pham:?)\s*", t_norm, re.IGNORECASE):
                gold_meta["target_entity"] = "product"
                gold_meta["style"] = "Chuyên nghiệp"
                clean_transcript = re.sub(r"^(adm\s+)?(tạo sản phẩm:?\s*|san pham:?\s*)", "", transcript, flags=re.IGNORECASE).strip()
                response_msg = f"Dạ thưa Sếp, em đã bẻ lái sang dây chuyền SẢN PHẨM để thiết kế '{clean_transcript}' chuẩn Elite ạ! 💎"
            
            else:
                response_msg = f"Dạ thưa Sếp, em đang khởi tạo XoHi Core để phân tích '{transcript}' đây ạ. Sếp đợi em một chút nhé!"

            if intent_data and "content_mode" in intent_data:
                gold_meta["content_mode"] = intent_data["content_mode"]

            campaign = ContentCampaign(
                id=str(uuid.uuid4()), user_id=user_id, source_input=clean_transcript,
                tenant_id=tenant_id, current_step=1, status="PROCESSING", 
                gold_metadata=gold_meta, category=category.value
            )
            c_id = campaign.id
            u_id_str = str(campaign.user_id) if campaign.user_id else "default"
            await campaign_repo.add(campaign)
            if hasattr(campaign_repo, "session"):
                await campaign_repo.session.commit()

            # Phase 16.1: Zero-Latency Trigger
            asyncio.create_task(self._run_background_analysis(
                c_id, clean_transcript, u_id_str, tenant_id, gold_meta.get("style", "viral").lower(), campaign_repo
            ))

            return IntentResponse(
                status="success", action=IntentAction.CONTENT_CREATE,
                message=response_msg,
                router_tier=RouterTier.TIER_2_SEMANTIC,
                data={
                    "category": "CONTENT_CREATE",
                    "intent_type": "CONTENT_CREATE",
                    "ui_action": "CONTENT_CREATE",
                    "action": "STEP1_REVIEW",
                    "campaign_id": c_id,
                    "status": "PROCESSING",
                    "step": 1,
                    "campaign_category": category.value,
                    "target_entity": gold_meta.get("target_entity")
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

    async def _run_background_analysis(
        self, campaign_id: str, transcript: str, user_id: str, 
        tenant_id: str, content_mode: str, old_repo: ContentCampaignRepository
    ):
        """
        [PHASE 16.1] Heavy-lifting background task for Step 1.
        Uses its own session to guarantee thread/greenlet safety.
        """
        try:
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as session:
                repo = ContentCampaignRepository(session=session)
                campaign = await repo.get(campaign_id)
                if not campaign:
                    logger.error(f"[XoHi Background] Campaign {campaign_id} not found!")
                    return

                # Execute Step 1 Analysis (AI)
                seed: TopicSeed = await self.orchestrator.vision.analyze_input(
                    transcript, campaign_id, repo, user_id, content_mode=content_mode
                )
                
                seed_data = seed.model_dump()
                campaign.topic_data = seed_data
                campaign.status = "WAITING_FOR_REVIEW"
                await repo.update(campaign)
                await session.commit()

                # Final signal to UI: Card is ready for review!
                await event_bus.emit("CONTENT_STEP_COMPLETED", {
                    "campaign_id": campaign_id, 
                    "step": 1, 
                    "status": "WAITING_FOR_REVIEW",
                    "user_id": user_id, 
                    "data": {"keywords": seed_data}
                })
                logger.info(f"[XoHi Background] Step 1 analysis complete for {campaign_id}")

        except Exception as e:
            logger.exception(f"[XoHi Background] Analysis failed for {campaign_id}: {e}")
            # Optional: update status to ERROR so UI doesn't hang forever
            async with alchemy_config.create_session_maker()() as err_session:
                err_repo = ContentCampaignRepository(session=err_session)
                err_campaign = await err_repo.get(campaign_id)
                if err_campaign:
                    err_campaign.status = "ERROR"
                    await err_repo.update(err_campaign)
                    await err_session.commit()

            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": campaign_id,
                "user_id": user_id,
                "step": 1,
                "message": f"Lỗi khởi tạo: {str(e)}",
                "status": "ERROR",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    async def _handle_campaign_purge(self, payload: dict) -> None:
        """
        [ELITE V2.2] Decentralized Purge Listener.
        Performs Vantablack Sweep (Deep JSON logic) for ChatMessages.
        """
        campaign_id = payload.get("campaign_id")
        if not campaign_id: return

        logger.info(f"[PurgeProtocol] VoiceHandler sweeping logs for {campaign_id}")
        
        try:
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as session:
                # [Vantablack Purge] Search all sessions for campaign references in JSON
                await session.execute(
                    sa_delete(ChatMessage).where(
                        sa.or_(
                            ChatMessage.session_id == campaign_id,
                            ChatMessage.content["campaign_id"].as_string() == campaign_id,
                            ChatMessage.content["data"]["campaign_id"].as_string() == campaign_id
                        )
                    )
                )
                await session.commit()
                logger.info(f"[PurgeProtocol] Chat log sweep complete for {campaign_id}")
        except Exception as e:
            logger.error(f"[PurgeProtocol] Chat log sweep failed for {campaign_id}: {e}")
