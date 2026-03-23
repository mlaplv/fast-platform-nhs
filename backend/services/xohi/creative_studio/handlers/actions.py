import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from backend.database.repositories import ContentCampaignRepository
from backend.models.schemas import GenericResponse
from backend.services.event_bus import event_bus
from backend.services.xohi.creative_studio.formatters.publisher import publish_campaign_to_news
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger("api-gateway")

class ActionHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"): self.orchestrator = orchestrator

    async def approve_step(self, campaign_id: str, data: Dict[str, object], campaign_repo: ContentCampaignRepository) -> GenericResponse:
        c = await campaign_repo.get(campaign_id)
        if not c: return GenericResponse(status="error", message="Campaign not found")
        step, req_step = c.current_step, data.get("step")
        if req_step is not None and int(req_step) != step:
            return GenericResponse(status="error", message=f"Dạ sếp, bước {req_step} này đã qua hoặc chưa tới ạ.", data={"current_step": step})
        
        if not data.get("approved", True):
            # Phase 82.50: Use immediate update for rejection (non-blocking if possible)
            c.status = "REJECTED"; await campaign_repo.update(c); 
            if hasattr(campaign_repo, "session"): await campaign_repo.session.commit()
            return GenericResponse(status="success", message="Đang hủy tiến trình...")
        
        if c.status != "WAITING_FOR_REVIEW": return GenericResponse(status="error", message="Bước này đang được xử lý hoặc đã duyệt rồi ạ.")
        
        ed = data.get("edited_data")
        if ed:
            from sqlalchemy.orm.attributes import flag_modified
            if step == 1:
                cur = dict(c.topic_data or {}); cur.update(ed); c.topic_data = cur; flag_modified(c, "topic_data")
            elif step == 3:
                c.outline_data = ed; flag_modified(c, "outline_data")
            elif step in [4, 5]:
                new = ed.get("html") or ed.get("content")
                if new: c.draft_content = new

        if step == 2:
            if data.get("assets"): c.assets_data = data["assets"]; from sqlalchemy.orm.attributes import flag_modified; flag_modified(c, "assets_data")
            avail, idx = data.get("avatar"), data.get("selected_index")
            if avail or idx is not None:
                gold = dict(c.gold_metadata or {}); gold["avatar"], gold["selected_index"] = avail or gold.get("avatar"), idx if idx is not None else gold.get("selected_index")
                c.gold_metadata = gold; from sqlalchemy.orm.attributes import flag_modified; flag_modified(c, "gold_metadata")
        elif step == 1:
            c.gold_metadata = c.topic_data; from sqlalchemy.orm.attributes import flag_modified; flag_modified(c, "gold_metadata")

        if step == 6:
            if await publish_campaign_to_news(c, campaign_repo):
                if hasattr(campaign_repo, "session"): await campaign_repo.session.commit()
                await event_bus.emit("CONTENT_STEP_COMPLETED", {"campaign_id": campaign_id, "user_id": c.user_id, "step": 6, "status": "COMPLETED", "tenant_id": c.tenant_id})
                return GenericResponse(status="success", message="🎉 Xuất bản thành công!", data={"campaign_id": campaign_id, "next_step": 7})
            return GenericResponse(status="error", message="Lỗi xuất bản.")

        c.current_step += 1; c.status = "PROCESSING"; await campaign_repo.update(c)
        if hasattr(campaign_repo, "session"): await campaign_repo.session.commit()
        await event_bus.emit("CONTENT_PROGRESS", {"campaign_id": campaign_id, "user_id": c.user_id, "step": c.current_step, "message": f"✅ Phase {step} Done.", "status": "PROCESSING", "timestamp": datetime.now(timezone.utc).isoformat()})
        if c.current_step <= 6: asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id, force_step=c.current_step))
        return GenericResponse(status="success", message=f"Bắt đầu bước {c.current_step}...", data={"campaign_id": campaign_id, "next_step": c.current_step})

    async def retry_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        # Phase 82.50: Zero-Blocking Trigger. Let the engine handle cancellation and status flip.
        # This prevents deadlocks when the background task holds a row lock.
        asyncio.create_task(self.orchestrator._trigger_next_step(campaign_id))
        return GenericResponse(status="success", message="Yêu cầu chạy lại đã được gửi.")

    async def update_metadata(self, campaign_id: str, data: Dict[str, object], campaign_repo: ContentCampaignRepository) -> GenericResponse:
        c = await campaign_repo.get(campaign_id)
        if not c:
            return GenericResponse(status="error", message="Campaign not found")
        
        gold, gold_changed = dict(c.gold_metadata or {}), False
        fields = ["assets", "keywords", "outline_data", "draft_content", "final_html", "reserve_assets", "avatar", "selected_index"]
        
        for f in fields:
            val = data.get(f)
            if val is not None:
                if f == "assets":
                    c.assets_data = val
                    flag_modified(c, "assets_data")
                elif f == "keywords":
                    c.topic_data = val
                    flag_modified(c, "topic_data")
                elif f == "outline_data":
                    c.outline_data = val
                    flag_modified(c, "outline_data")
                elif f in ["reserve_assets", "avatar", "selected_index"]:
                    gold[f] = val
                    gold_changed = True
                elif f == "draft_content":
                    c.draft_content = val
                elif f == "final_html":
                    c.final_html = val
        
        if gold_changed:
            c.gold_metadata = gold
            flag_modified(c, "gold_metadata")
        
        # CNS V82.50: Forced session sync for persistence
        await campaign_repo.update(c)
        if hasattr(campaign_repo, "session"):
            await campaign_repo.session.flush()
            await campaign_repo.session.commit()
            
        return GenericResponse(status="success", message="Neural data synced.")
