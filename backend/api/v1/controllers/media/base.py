# backend/api/v1/controllers/media/base.py
import logging
from typing import Optional, Union
from litestar import get, post, patch, delete, Request
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.di import Provide

from backend.database.repositories import MediaRegistryRepository, provide_media_repo
from backend.services.media.media_service import media_service
from backend.services.media.schemas import (
    MediaListResponse,
    MediaStatsResponse,
    MediaUpdateMetadata,
    MediaDetailResponse,
    MediaAssetResponse,
    MediaListResponseData,
    MediaStatsResponseData
)
from backend.api.v1.schemas.schemas import GenericResponse

logger = logging.getLogger("media-api")

class MediaBaseController:
    @get("/")
    async def list_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        campaign_id: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        trash: bool = False
    ) -> MediaListResponse:
        """FileManager: Liệt kê tài nguyên tập trung."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        result = await media_service.list_assets(
            repo=media_repo,
            campaign_id=campaign_id,
            search_query=q,
            limit=limit,
            offset=offset,
            include_deleted=trash,
            owner_id=owner_id
        )

        return MediaListResponse(
            status="success",
            data=MediaListResponseData(
                items=result.items,
                total=result.total,
                limit=result.limit,
                offset=result.offset
            )
        )

    @post("/", media_type=RequestEncodingType.MULTI_PART)
    async def upload_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
        campaign_id: Optional[str] = None
    ) -> MediaDetailResponse:
        """Upload file trực tiếp."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        content = await data.read()
        asset = await media_service.upload_asset(
            repo=media_repo,
            file_content=content,
            filename=data.filename,
            content_type=data.content_type,
            campaign_id=campaign_id,
            owner_id=owner_id
        )

        if not asset:
             from backend.api.common.exceptions import ClientException
             raise ClientException(status_code=400, detail="Failed to upload asset")

        return MediaDetailResponse(
            status="success",
            data=MediaAssetResponse.model_validate(asset)
        )

    @get("/stats")
    async def get_media_stats(self, request: Request, media_repo: MediaRegistryRepository) -> MediaStatsResponse:
        """Lấy số liệu thống kê kho tài nguyên."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")
        stats = await media_service.get_stats(media_repo, owner_id=owner_id)

        return MediaStatsResponse(
            status="success",
            data=MediaStatsResponseData(
                total_count=stats.total_count,
                total_size=stats.total_size,
                breakdown=stats.breakdown,
                storage_provider=stats.storage_provider
            )
        )

    @get("/{asset_id:str}")
    async def get_media_detail(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository) -> Union[MediaDetailResponse, GenericResponse]:
        """Lấy thông tin chi tiết một tài nguyên."""
        asset = await media_repo.get(str(asset_id))
        if not asset:
            return GenericResponse(status="error", message="Asset not found")

        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")
        if not asset.is_public and asset.owner_id and asset.owner_id != owner_id:
            return GenericResponse(status="error", message="Access denied")

        return MediaDetailResponse(
            status="success",
            data=MediaAssetResponse.model_validate(asset)
        )

    @patch("/{asset_id:str}")
    async def update_media(
        self,
        asset_id: str,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: MediaUpdateMetadata
    ) -> GenericResponse:
        """Cập nhật Metadata."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        updated = await media_service.update_metadata(
            media_repo,
            str(asset_id),
            data,
            owner_id=owner_id
        )

        if not updated:
            return GenericResponse(status="error", message="Asset not found or unauthorized")

        return GenericResponse(status="success", message="Media metadata updated.")

    @delete("/{asset_id:str}", status_code=200)
    async def delete_media(
        self,
        asset_id: str,
        request: Request,
        media_repo: MediaRegistryRepository,
        permanent: bool = False
    ) -> GenericResponse:
        """Xóa tài nguyên."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        success = await media_service.delete_asset(media_repo, str(asset_id), permanent=permanent, owner_id=owner_id)

        if success:
            msg = "Asset moved to trash." if not permanent else "Asset permanently purged."
            return GenericResponse(status="success", message=msg)
        else:
            return GenericResponse(status="error", message="Asset not found or unauthorized")

    @post("/{asset_id:str}/restore")
    async def restore_media(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository) -> GenericResponse:
        """Khôi phục tài nguyên từ Thùng rác."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        success = await media_service.restore_asset(media_repo, str(asset_id), owner_id=owner_id)
        if success:
            return GenericResponse(status="success", message="Asset restored successfully.")
        else:
            return GenericResponse(status="error", message="Failed to restore asset or unauthorized.")
