import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from backend.database.repositories import ContentCampaignRepository
from backend.schemas.content import GenericResponse


from backend.services.event_bus import event_bus
from backend.services.xohi.creative_studio.formatters.publisher import publish_campaign_to_news
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import select, delete as sql_delete

from backend.database.models import Appointment
from backend.database.repositories import AppointmentRepository

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
            from backend.services.xohi.creative_studio.formatters.publisher import publish_campaign_to_news, publish_campaign_to_products
            
            ent = c.get_gold_config().get("target_entity", "article")
            topic_data = c.topic_data or {}
            cat_id = topic_data.get("category_id")
            
            success = False
            if ent == "product":
                success = await publish_campaign_to_products(c, campaign_repo, category_id=cat_id)
            else:
                success = await publish_campaign_to_news(c, campaign_repo, category_id=cat_id)

            if success:
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
            
        # CNS V82.1: Neural Autopilot Sync Logic
        # If scheduling data is present, sync with Appointment system and persist in gold_metadata
        if "keywords" in data and isinstance(data["keywords"], dict):
            sch = data["keywords"].get("scheduling")
            if sch:
                # Elite Persistence: Store in gold_metadata for clean separation
                gold["scheduling"] = sch
                c.gold_metadata = gold
                flag_modified(c, "gold_metadata")
                await self._sync_appointment(campaign_id, sch, campaign_repo)

        return GenericResponse(status="success", message="Neural data synced.")

    async def _sync_appointment(self, campaign_id: str, sch: dict, campaign_repo: ContentCampaignRepository):
        """Elite Core: Synchronizes campaign scheduling with the global Appointment system."""
        from datetime import datetime, time, timedelta
        
        is_active = sch.get("is_active", False)
        freq = sch.get("frequency", "daily")
        time_str = sch.get("schedule_at", "08:00")
        days = sch.get("days", [])
        
        session = campaign_repo.session
        
        # 1. Clean up existing appointment for this campaign if it exists
        stmt = select(Appointment).where(Appointment.campaign_id == campaign_id)
        result = await session.execute(stmt)
        existing = result.scalars().first()
        
        if not is_active:
            if existing:
                await session.delete(existing)
                logger.info(f"🗑️ [Autopilot] Disabled and removed appointment for {campaign_id}")
            return

        # 2. Calculate next run time
        try:
            h, m = map(int, time_str.split(":"))
            now = datetime.now()
            next_run = datetime(now.year, now.month, now.day, h, m)
            
            if next_run <= now:
                next_run += timedelta(days=1)
                
            # For weekly, adjust to the next available day
            if freq == "weekly" and days:
                current_weekday = now.weekday() # 0-6 (Mon-Sun)
                # Frontend days might be 0-6 for T2-CN
                target_days = sorted(days)
                found = False
                for d in target_days:
                    if d > current_weekday:
                        days_diff = d - current_weekday
                        next_run = datetime(now.year, now.month, now.day, h, m) + timedelta(days=days_diff)
                        found = True
                        break
                if not found:
                    days_diff = 7 - current_weekday + target_days[0]
                    next_run = datetime(now.year, now.month, now.day, h, m) + timedelta(days=days_diff)

        except Exception as e:
            logger.error(f"❌ [Autopilot] Time calculation error: {e}")
            next_run = datetime.now() + timedelta(hours=1)

        # 3. Create or Refresh valid Appointment
        if existing:
            existing.start_time = next_run
            existing.end_time = next_run + timedelta(minutes=30)
            existing.recurring_type = freq
            existing.recurring_metadata = {"days": days}
            existing.status = "UPCOMING"
            logger.info(f"🔄 [Autopilot] Updated schedule for {campaign_id} to {next_run}")
        else:
            new_app = Appointment(
                id=str(uuid.uuid4()),
                title=f"Neural Autopilot: {campaign_id[:8]}",
                description="Automated content generation session.",
                start_time=next_run,
                end_time=next_run + timedelta(minutes=30),
                type="STRATEGY",
                status="UPCOMING",
                recurring_type=freq,
                recurring_metadata={"days": days},
                campaign_id=campaign_id,
                tenant_id=getattr(campaign_repo, "tenant_id", "default")
            )
            session.add(new_app)
            logger.info(f"📅 [Autopilot] Created NEW schedule for {campaign_id} at {next_run}")
