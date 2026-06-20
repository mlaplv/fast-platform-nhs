import uuid
from backend.utils.uid import new_id
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database.models import Banner
from backend.schemas.banner import CreateBannerRequest, UpdateBannerRequest, BannerResponse, BannerListResponse
from backend.schemas.common import SuccessResponse
from backend.services.event_bus import event_bus
from backend.utils.media import extract_media_urls

logger = logging.getLogger("api-gateway")

class BannerService:
    @staticmethod
    async def list_banners(db_session: AsyncSession, position: Optional[str] = None, active_only: bool = False, limit: int = 100, offset: int = 0) -> BannerListResponse:
        """List banners with filtering and pagination (Cached)."""
        import json
        from backend.services.xohi_memory import xohi_memory
        
        cache_key = f"system:banners:v1:active:{active_only}:pos:{position or 'all'}:lim:{limit}:off:{offset}"
        try:
            cached = await xohi_memory.client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return BannerListResponse(
                    data=[BannerResponse(**b) for b in data["data"]],
                    total=data["total"]
                )
        except Exception as e:
            logger.debug(f"[BannerService] Cache read failed: {e}")

        # 1. Count
        count_stmt = select(func.count(Banner.id)).where(Banner.deleted_at == None)
        if position:
            count_stmt = count_stmt.where(Banner.position == position)
        if active_only:
            count_stmt = count_stmt.where(Banner.is_active == True)
        
        total = await db_session.scalar(count_stmt) or 0

        # 2. Fetch
        stmt = select(Banner).where(Banner.deleted_at == None)
        if position:
            stmt = stmt.where(Banner.position == position)
        if active_only:
            stmt = stmt.where(Banner.is_active == True)
        
        stmt = stmt.order_by(Banner.order_index.asc(), Banner.created_at.desc()).limit(limit).offset(offset)
        
        res = await db_session.execute(stmt)
        banners = res.scalars().all()

        resp_data = [BannerResponse.model_validate(b) for b in banners]
        result = BannerListResponse(
            data=resp_data,
            total=total
        )

        try:
            payload = {
                "data": [b.model_dump(mode="json") for b in resp_data],
                "total": total
            }
            await xohi_memory.client.set(cache_key, json.dumps(payload), ex=600)
        except Exception as e:
            logger.debug(f"[BannerService] Cache write failed: {e}")

        return result

    @staticmethod
    async def _invalidate_cache() -> None:
        from backend.services.xohi_memory import xohi_memory
        try:
            keys = await xohi_memory.client.keys("system:banners:*")
            if keys:
                await xohi_memory.client.delete(*keys)
        except Exception as e:
            logger.debug(f"[BannerService] Cache invalidation failed: {e}")

    @staticmethod
    async def create_banner(db_session: AsyncSession, data: CreateBannerRequest) -> SuccessResponse:
        """Create a new banner."""
        new_id_val = new_id()
        banner = Banner(
            id=new_id_val,
            title=data.title,
            description=data.description,
            image_url=data.image_url,
            mobile_image_url=data.mobile_image_url,
            link_url=data.link_url,
            position=data.position,
            order_index=data.order_index,
            is_active=data.is_active,
            device_type=data.device_type
        )
        db_session.add(banner)
        await db_session.commit()
        
        # Invalidate cache
        await BannerService._invalidate_cache()
        
        # Elite V2.2: Sync Media
        await BannerService._sync_media_links(new_id_val, data.image_url, data.mobile_image_url)
        
        return SuccessResponse(ok=True, id=new_id_val)

    @staticmethod
    async def update_banner(db_session: AsyncSession, banner_id: str, data: UpdateBannerRequest) -> SuccessResponse:
        """Update an existing banner."""
        stmt = select(Banner).where(Banner.id == banner_id)
        res = await db_session.execute(stmt)
        banner = res.scalar_one_or_none()

        if not banner:
            raise NotFoundException(f"Banner {banner_id} not found")

        if data.title is not None: banner.title = data.title
        if data.description is not None: banner.description = data.description
        if data.image_url is not None: banner.image_url = data.image_url
        if data.mobile_image_url is not None: banner.mobile_image_url = data.mobile_image_url
        if data.link_url is not None: banner.link_url = data.link_url
        if data.position is not None: banner.position = data.position
        if data.order_index is not None: banner.order_index = data.order_index
        if data.is_active is not None: banner.is_active = data.is_active
        if data.device_type is not None: banner.device_type = data.device_type

        banner.updated_at = datetime.now(timezone.utc)
        await db_session.commit()

        # Invalidate cache
        await BannerService._invalidate_cache()

        # Elite V2.2: Sync Media
        await BannerService._sync_media_links(banner_id, banner.image_url, banner.mobile_image_url)

        return SuccessResponse(ok=True, id=banner_id)

    @staticmethod
    async def delete_banner(db_session: AsyncSession, banner_id: str) -> SuccessResponse:
        """Soft delete a banner."""
        stmt = select(Banner).where(Banner.id == banner_id)
        res = await db_session.execute(stmt)
        banner = res.scalar_one_or_none()

        if not banner:
            raise NotFoundException(f"Banner {banner_id} not found")

        banner.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        
        # Invalidate cache
        await BannerService._invalidate_cache()
        
        return SuccessResponse(ok=True, id=banner_id)

    @staticmethod
    async def _sync_media_links(banner_id: str, image_url: Optional[str], mobile_image_url: Optional[str] = None) -> None:
        """
        Elite V2.2: Neural Media Sync for Banners.
        Đảm bảo ảnh Banner được bảo vệ.
        """
        try:
            combined_urls = (image_url or "") + " " + (mobile_image_url or "")
            urls = extract_media_urls(combined_urls)
            if urls:
                await event_bus.emit("MEDIA_SYNC_REQUIRED", {
                    "entity_id": str(banner_id),
                    "entity_type": "banner",
                    "urls": list(urls)
                })
                logger.info(f"[BannerService] Emitted MEDIA_SYNC_REQUIRED for banner {banner_id} with {len(urls)} URLs")
        except Exception as e:
            logger.error(f"[BannerService] Failed to emit media sync: {e}")

banner_service = BannerService()

async def provide_banner_service() -> BannerService:
    """Standard Litestar Provider for BannerService."""
    return banner_service
