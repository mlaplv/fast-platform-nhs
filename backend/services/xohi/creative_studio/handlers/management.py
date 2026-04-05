import os
import logging
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.orm import undefer
from backend.database.models import ContentCampaign as CampaignModel, MediaRegistry, ChatMessage
from backend.database.repositories import ContentCampaignRepository, MediaRegistryRepository
from backend.models.schemas import CampaignListResponse, CampaignListItem, GenericResponse, CampaignStatus

logger = logging.getLogger("api-gateway")

class ManagementHandler:
    def __init__(self, orchestrator: "ContentOrchestrator"):
        self.orchestrator = orchestrator

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
        ).order_by(CampaignModel.created_at.desc()).limit(limit).offset(offset)
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
        try:
            campaign = await repo.get(campaign_id); 
            if not campaign: return GenericResponse(status="error", message="Campaign not found")
            user_id = str(campaign.user_id) if campaign.user_id else None
            assets = (await media_repo.session.execute(select(MediaRegistry).where(MediaRegistry.campaign_id == campaign_id))).scalars().all()
            files_purged = 0
            for a in assets:
                p = os.path.join("frontend/static", a.file_path.lstrip("/")); 
                if os.path.exists(p): os.remove(p); files_purged += 1
                await media_repo.delete(a.id)
            await repo.session.execute(sa_delete(ChatMessage).where(ChatMessage.content["campaign_id"].as_string() == campaign_id))
            if user_id:
                from backend.services.xohi_memory import xohi_memory
                if xohi_memory._use_redis: await xohi_memory.client.delete(f"xohi:chat:{user_id}")
            await repo.delete(campaign_id)
            from backend.services.event_bus import event_bus
            await event_bus.emit("CAMPAIGN_PURGED", {"campaign_id": campaign_id, "type": "TERMINATE", "action": "PURGE"})
            await repo.session.commit()
            return GenericResponse(status="success", message=f"Campaign wiped. {files_purged} assets purged.")
        except Exception as e:
            return GenericResponse(status="error", message=str(e))

    async def cancel_campaign(self, campaign_id: str, repo: ContentCampaignRepository) -> GenericResponse:
        """[R100] Logic to terminate a campaign and notify the event bus."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")
        
        campaign.status = "REJECTED"
        await repo.update(campaign)
        
        from backend.services.event_bus import event_bus
        await event_bus.emit(
            "CAMPAIGN_PURGED", 
            {"campaign_id": campaign_id, "type": "TERMINATE", "action": "CANCEL"}
        )
        await repo.session.commit()
        return GenericResponse(status="success", message="Hệ thống đã ngắt và hủy tiến trình theo lệnh sếp.")

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
