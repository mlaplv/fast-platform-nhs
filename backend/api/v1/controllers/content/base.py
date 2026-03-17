# backend/api/v1/controllers/content/base.py
import logging
from typing import Dict, Optional
from uuid import UUID
from litestar import Controller, get, post, put, patch, delete, Request
from litestar.di import Provide

from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.api.v1.schemas.schemas import (
    ContentCampaign as CampaignSchema,
    CampaignListResponse,
    GenericResponse
)
from backend.database.repositories import ContentCampaignRepository, MediaRegistryRepository, provide_campaign_repo, provide_media_repo

logger = logging.getLogger("api-gateway")

class ContentBaseController(Controller):
    path = "/api/v1/content"
    dependencies = {
        "campaign_repo": Provide(provide_campaign_repo),
        "media_repo": Provide(provide_media_repo)
    }

    @get("/campaigns")
    async def list_campaigns(
        self,
        campaign_repo: ContentCampaignRepository,
        limit: int = 20,
        offset: int = 0
    ) -> CampaignListResponse:
        """Lấy danh sách các chiến dịch hỗ trợ phân trang (V72.10: Dynamic Paging)."""
        from sqlalchemy import select, func
        from backend.database.models import ContentCampaign as CampaignModel

        count_stmt = select(func.count()).select_from(CampaignModel)
        total_count = await campaign_repo.session.execute(count_stmt)
        total = total_count.scalar_one()

        stmt = select(
            CampaignModel.id,
            CampaignModel.topic_data,
            CampaignModel.status,
            CampaignModel.current_step,
            CampaignModel.created_at,
            CampaignModel.user_id
        ).order_by(CampaignModel.created_at.desc()).limit(limit).offset(offset)

        result = await campaign_repo.session.execute(stmt)
        rows = result.all()

        from backend.api.v1.schemas.schemas import CampaignListItem
        items = [
            CampaignListItem(
                id=str(row.id),
                topic_data=row.topic_data,
                status=row.status,
                current_step=row.current_step,
                created_at=row.created_at,
                user_id=str(row.user_id) if row.user_id else None
            )
            for row in rows
        ]

        return CampaignListResponse(
            items=items,
            total=total,
            has_more=(offset + limit) < total,
            limit=limit,
            offset=offset
        )

    @get("/campaigns/{campaign_id:uuid}")
    async def get_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> CampaignSchema:
        """Lấy thông tin chi tiết một chiến dịch (Undefer support)."""
        from sqlalchemy.orm import undefer
        from sqlalchemy import select
        from backend.database.models import ContentCampaign as CampaignModel
        try:
            stmt = select(CampaignModel).where(CampaignModel.id == str(campaign_id)).options(undefer(CampaignModel.final_html))
            result = await campaign_repo.session.execute(stmt)
            campaign = result.scalar_one_or_none()

            if not campaign:
                from litestar.exceptions import NotFoundException
                raise NotFoundException(f"Campaign {campaign_id} not found")
            return CampaignSchema.model_validate(campaign)
        except Exception as e:
            logger.error(f"[ContentController] Error fetching campaign {campaign_id}: {str(e)}")
            raise e

    @post("/campaigns/{campaign_id:uuid}/approve")
    async def approve_step(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """User phê duyệt bước sáng tạo hiện tại."""
        data: Dict[str, object] = await request.json()
        return await content_factory.approve_step(str(campaign_id), data, campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/retry")
    async def retry_step(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """Chạy lại bước sáng tạo hiện tại."""
        return await content_factory.retry_step(str(campaign_id), campaign_repo)

    @post("/campaigns/{campaign_id:uuid}/publish")
    async def publish_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        """Xuất bản và địa phương hóa toàn bộ tài nguyên."""
        from backend.database.models import ContentCampaign as CampaignModel
        campaign: Optional[CampaignModel] = await campaign_repo.get(str(campaign_id))
        if not campaign:
            return GenericResponse(status="error", message="Campaign not found")

        from backend.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
        compressor = MediaCompressor()
        await compressor.execute(str(campaign_id), campaign_repo, media_repo=media_repo)

        campaign.status = "COMPLETED"
        await campaign_repo.update(campaign)
        await campaign_repo.session.commit()
        return GenericResponse(status="success", message="Campaign published and registered.")

    @put("/campaigns/{campaign_id:uuid}/metadata")
    async def update_metadata(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """Cập nhật dữ liệu chiến dịch (keywords, assets...)."""
        data: Dict[str, object] = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @patch("/campaigns/{campaign_id:uuid}")
    async def patch_campaign(self, campaign_id: UUID, request: Request, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        """RESTful Alias cho update_metadata."""
        data: Dict[str, object] = await request.json()
        return await content_factory.update_metadata(str(campaign_id), data, campaign_repo)

    @delete("/campaigns/{campaign_id:uuid}", status_code=200)
    async def delete_campaign(self, campaign_id: UUID, campaign_repo: ContentCampaignRepository, media_repo: MediaRegistryRepository) -> GenericResponse:
        """Xóa chiến dịch, toàn bộ file vật lý và log liên quan (Full Surgical Purge)."""
        try:
            import os
            cid_str = str(campaign_id)
            campaign = await campaign_repo.get(cid_str)
            if not campaign:
                return GenericResponse(status="error", message="Campaign not found")
            user_id = str(campaign.user_id) if campaign.user_id else None

            from sqlalchemy import select
            from backend.database.models import MediaRegistry
            media_stmt = select(MediaRegistry).where(MediaRegistry.campaign_id == cid_str)
            media_result = await media_repo.session.execute(media_stmt)
            assets = media_result.scalars().all()

            files_purged = 0
            for asset in assets:
                rel_path = asset.file_path.lstrip("/")
                full_path = os.path.join("frontend/static", rel_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    files_purged += 1
                await media_repo.delete(asset.id)

            from sqlalchemy import delete as sa_delete
            from backend.database.models import ChatMessage
            stmt = sa_delete(ChatMessage).where(
                ChatMessage.content["campaign_id"].as_string() == cid_str
            )
            await campaign_repo.session.execute(stmt)

            if user_id:
                from backend.services.xohi_memory import xohi_memory
                cache_key = f"xohi:chat:{user_id}"
                if xohi_memory._use_redis:
                    await xohi_memory.client.delete(cache_key)

            await campaign_repo.delete(cid_str)

            from backend.services.event_bus import event_bus
            await event_bus.emit("CAMPAIGN_PURGED", {
                "campaign_id": cid_str,
                "type": "TERMINATE",
                "action": "PURGE"
            })
            await campaign_repo.session.commit()
            return GenericResponse(status="success", message=f"Campaign wiped. {files_purged} assets and neural logs purged.")
        except Exception as e:
            logger.error(f"[ContentController] Purge failed for {campaign_id}: {str(e)}")
            return GenericResponse(status="error", message=str(e))
