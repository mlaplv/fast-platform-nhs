import logging
import os
import sqlalchemy as sa
from sqlalchemy import select, func, delete as sa_delete
from typing import TypedDict, Optional, List, Dict, Union, TYPE_CHECKING

from backend.database.models import ContentCampaign as CampaignModel, MediaRegistry, ChatMessage, CampaignEvent, Appointment, AgentTelemetryLog, Notification
from backend.database.models.system import UnifiedAgentTask
from backend.database.repositories import ContentCampaignRepository, MediaRegistryRepository
from backend.database.alchemy_config import alchemy_config
from backend.services.event_bus import event_bus
from backend.models.schemas import CampaignListResponse, CampaignListItem, CampaignStatus, GenericResponse

if TYPE_CHECKING:
    from backend.services.xohi.creative_studio.orchestrator import ContentOrchestrator

logger = logging.getLogger("api-gateway")

class PurgePayload(TypedDict):
    campaign_id: str
    user_id: Optional[str]

class ManagementHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator
        # [Elite V2.2] Decentralized Cleanup Registration
        event_bus.subscribe("XOHI_CAMPAIGN_PURGED", self._handle_campaign_purge)

    async def list_campaigns(self, repo: ContentCampaignRepository, limit: int = 20, offset: int = 0) -> CampaignListResponse:
        count_stmt = select(func.count()).select_from(CampaignModel)
        total = (await repo.session.execute(count_stmt)).scalar_one()
        stmt = select(
            CampaignModel.id, 
            CampaignModel.topic_data, 
            CampaignModel.status, 
            CampaignModel.current_step, 
            CampaignModel.created_at, 
            CampaignModel.user_id,
            CampaignModel.category
        ).where(CampaignModel.deleted_at == None).order_by(CampaignModel.created_at.desc()).limit(limit).offset(offset)
        rows = (await repo.session.execute(stmt)).all()
        items = [
            CampaignListItem(
                id=str(r.id), 
                topic_data=r.topic_data, 
                status=CampaignStatus(r.status), 
                current_step=r.current_step, 
                created_at=r.created_at, 
                user_id=str(r.user_id) if r.user_id else None,
                category=r.category
            ) for r in rows
        ]
        return CampaignListResponse(items=items, total=total, has_more=(offset + limit) < total, limit=limit, offset=offset)

    async def delete_campaign(self, campaign_id: str, repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        """
        [PHASE 18.2] Atomic Delete: Emits XOHI_CAMPAIGN_PURGED for background cleanup 
        and removes the core record to seal the "ghost" hole immediately.
        """
        try:
            campaign = await repo.get(campaign_id)
            if not campaign: return GenericResponse(status="error", message="Campaign not found")
            
            user_id = str(campaign.user_id) if campaign.user_id else None

            # 1. Emit Purge Event (Decoupled Cleanup Trigger)
            # This triggers Chat, Media, and Appointment cleanup across all modules.
            await event_bus.emit("XOHI_CAMPAIGN_PURGED", {
                "campaign_id": campaign_id,
                "user_id": user_id
            })

            # 2. Delete Core Record (Atomic)
            await repo.delete(campaign_id)
            if hasattr(repo, "session"):
                await repo.session.commit()

            return GenericResponse(status="success", message=f"Vantablack Purge: Chiến dịch {campaign_id[:8]}... đã bị xóa sổ hoàn toàn.")
        except Exception as e:
            logger.exception(f"Failed to delete campaign {campaign_id}: {e}")
            if repo and hasattr(repo, "session"):
                await repo.session.rollback()
            return GenericResponse(status="error", message=str(e))

    async def _handle_campaign_purge(self, payload: PurgePayload) -> None:
        """
        [ELITE V2.2] Decentralized Purge Listener.
        Handles domain cleanup: Media files, Appointments, Memory, Telemetry, and Active Tasks.
        """
        campaign_id = payload.get("campaign_id")
        user_id = payload.get("user_id")
        if not campaign_id: return

        logger.info(f"[PurgeProtocol] Phase 1: Signal received for {campaign_id}")
        
        try:
            # 1. Stop Active Processing & Cleanup Tasks
            await self.orchestrator.engine.terminate_campaign_tasks(campaign_id)
            
            # 2. Clear Stateful Memory (AI Context)
            if user_id:
                await self.orchestrator.memory.delete_campaign_memory(campaign_id, user_id=user_id)
            else:
                await self.orchestrator.memory.delete_campaign_memory(campaign_id)

            # 3. Purge Physical Assets and Related DB Records
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as session:
                logger.info(f"[PurgeProtocol] Phase 2: Purging assets and tracking for {campaign_id}")
                
                # Media Registry & Files
                assets_stmt = sa.select(MediaRegistry).where(MediaRegistry.campaign_id == campaign_id)
                assets = (await session.execute(assets_stmt)).scalars().all()
                for a in assets:
                    p = os.path.join("frontend/static", a.file_path.lstrip("/")); 
                    if os.path.exists(p): 
                        try: os.remove(p)
                        except Exception: pass
                    await session.delete(a)

                # Appointments & Domain Events
                await session.execute(sa_delete(Appointment).where(Appointment.campaign_id == campaign_id))
                await session.execute(sa_delete(CampaignEvent).where(CampaignEvent.campaign_id == campaign_id))
                
                # Unified Agent Tasks (Background jobs)
                await session.execute(sa_delete(UnifiedAgentTask).where(sa.or_(
                    UnifiedAgentTask.session_id == campaign_id,
                    UnifiedAgentTask.task_id == campaign_id
                )))
                
                # [Elite V2.2] Telemetry & Usage Tracking
                await session.execute(sa_delete(AgentTelemetryLog).where(AgentTelemetryLog.session_id == campaign_id))

                await session.commit()
            
            # 4. Final Pulse Broadcast (Notify UI to refresh/clear state)
            await event_bus.emit("CAMPAIGN_PURGED", {
                "campaign_id": campaign_id, 
                "type": "TERMINATE", 
                "action": "PURGE"
            })
            
            logger.info(f"[PurgeProtocol] Phase 3: Final Sweep complete for {campaign_id}")
        except Exception as e:
            logger.error(f"[PurgeProtocol] CRITICAL Cleanup failure for {campaign_id}: {e}")

    async def cancel_campaign(self, campaign_id: str, repo: ContentCampaignRepository) -> GenericResponse:
        """[R100] Logic to terminate a campaign and notify the event bus."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")
        
        campaign.status = "REJECTED"
        await repo.update(campaign)
        
        # [Elite V2.2] Kill active processing immediately
        await self.orchestrator.engine.terminate_campaign_tasks(campaign_id)
        
        await event_bus.emit(
            "CAMPAIGN_PURGED", 
            {"campaign_id": campaign_id, "type": "TERMINATE", "action": "CANCEL"}
        )
        await repo.session.commit()
        return GenericResponse(status="success", message="Hệ thống đã ngắt điện và hủy tiến trình theo lệnh sếp.")

    async def publish_campaign(self, campaign_id: str, repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        """[R100] Finalize and publish campaign assets."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")
        
        # Standardized Media Compression & Registration
        await self.orchestrator.media.execute(campaign_id, repo, media_repo=media_repo)
        
        campaign.status = "COMPLETED"
        await repo.update(campaign)
        await repo.session.commit()
        return GenericResponse(status="success", message="Campaign published and registered.")
