import logging
from typing import List, Dict, Optional, Union, cast
from litestar import Controller, get, post, patch, delete, Request
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Redirect
from litestar.di import Provide

from backend.database.repositories import MediaRegistryRepository, provide_media_repo
from backend.services.media.media_service import media_service
from backend.services.media.schemas import (
    MediaListResponse,
    MediaStatsResponse,
    MediaUpdateMetadata,
    QuickEditParams,
    MediaDetailResponse,
    QuickEditResponse,
    BulkDownloadResponse,
    MediaAssetResponse,
    MediaListResponseData,
    MediaStatsResponseData,
    BulkDownloadResponseData,
    QuickEditRequest,
    BulkDeleteRequest,
    BulkDownloadRequest,
    FetchRemoteRequest,
    MimeTypeBreakdown
)
from backend.models.schemas import GenericResponse

logger = logging.getLogger("media-api")

class MediaController(Controller):
    path = "/api/v1/media"
    dependencies = {"media_repo": Provide(provide_media_repo)}

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
        """
        FileManager: Liệt kê tài nguyên tập trung.
        Hỗ trợ lọc theo campaign_id, Tìm kiếm ngữ nghĩa AI (V76) và Thùng rác (V10).
        """
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
        """Upload file trực tiếp (V65.0 Upload Path)."""
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
             from backend.exceptions import ClientException
             raise ClientException(status_code=400, detail="Failed to upload asset")

        return MediaDetailResponse(
            status="success",
            data=MediaAssetResponse.model_validate(asset)
        )

    @get("/stats")
    async def get_media_stats(self, request: Request, media_repo: MediaRegistryRepository) -> MediaStatsResponse:
        """Lấy số liệu thống kê kho tài nguyên (V9.0 Analytics)."""
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
        logger.info(f"[MediaRouter] GET detail for asset: {asset_id}")
        asset = await media_repo.get(str(asset_id))
        if not asset:
            return GenericResponse(status="error", message="Asset not found")

        # RBAC Check (V10.0 Elite)
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
        """Cập nhật Metadata (Alt text, Tags) - Đẳng cấp SEO."""
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
        """
        Xóa tài nguyên.
        Mặc định là Soft-delete (V10.0 Trash Bin).
        Nếu permanent=True sẽ xóa vĩnh viễn.
        """
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
        """Khôi phục tài nguyên từ Thùng rác (V10.0)."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        success = await media_service.restore_asset(media_repo, str(asset_id), owner_id=owner_id)
        if success:
            return GenericResponse(status="success", message="Asset restored successfully.")
        else:
            return GenericResponse(status="error", message="Failed to restore asset or unauthorized.")

    @post("/bulk-delete")
    async def bulk_delete_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: BulkDeleteRequest
    ) -> GenericResponse:
        """Xóa hàng loạt tài nguyên (Hỗ trợ Soft-delete V10.0)."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        success = await media_service.bulk_delete(
            media_repo,
            data.ids,
            permanent=data.permanent,
            owner_id=owner_id
        )

        if success:
            msg = f"Successfully moved {len(data.ids)} assets to trash." if not data.permanent else f"Successfully purged {len(data.ids)} assets."
            return GenericResponse(status="success", message=msg)
        else:
            return GenericResponse(status="error", message="Bulk delete failed or unauthorized.")

    @get("/{asset_id:str}/thumb")
    async def get_media_thumbnail(
        self,
        asset_id: str,
        request: Request,
        media_repo: MediaRegistryRepository,
        w: int = 300,
        q: int = 75
    ) -> Redirect:
        """Lấy đường dẫn Thumbnail cho ảnh (V76 Dynamic Engine)."""
        asset = await media_repo.get(str(asset_id))
        if not asset:
            return Redirect(path="/v65_assets/placeholder.webp")

        # RBAC Check (V10.0 Elite)
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")
        if not asset.is_public and asset.owner_id and asset.owner_id != owner_id:
            # Nếu không có quyền xem, trả về placeholder mờ ảo
            return Redirect(path="/v65_assets/placeholder.webp")

        thumb_path = await media_service.get_thumbnail(asset.file_path, width=w, quality=q)
        return Redirect(path=thumb_path or "/v65_assets/placeholder.webp")

    @post("/{asset_id:str}/edit")
    async def quick_edit_media(
        self,
        asset_id: str,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: QuickEditRequest
    ) -> Union[QuickEditResponse, GenericResponse]:
        """Xử lý nhanh ảnh (Xoay/Lật/Crop/Watermark) - V10.0 Elite Engine."""
        logger.info(f"[MediaRouter] Quick edit request for asset: {asset_id}, action: {data.action}")
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        asset = await media_service.quick_edit(
            media_repo,
            str(asset_id),
            data.action,
            params=data.params,
            owner_id=owner_id,
            source_url=data.source_url,
            campaign_id=data.campaign_id
        )

        if asset:
            return QuickEditResponse(
                status="success",
                data=MediaAssetResponse.model_validate(asset)
            )
        else:
            return GenericResponse(status="error", message="Quick edit failed or unauthorized.")

    @post("/bulk-download")
    async def bulk_download_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: BulkDownloadRequest
    ) -> Union[BulkDownloadResponse, GenericResponse]:
        """Tạo gói ZIP tải xuống hàng loạt (V76 Smart Download)."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        zip_url = await media_service.create_bulk_zip(media_repo, data.ids, owner_id=owner_id)

        if zip_url:
            return BulkDownloadResponse(
                status="success",
                data=BulkDownloadResponseData(zip_url=zip_url)
            )
        else:
            return GenericResponse(status="error", message="Failed to generate ZIP or unauthorized.")

    @post("/fetch-remote")
    async def fetch_remote_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: FetchRemoteRequest
    ) -> Union[MediaDetailResponse, GenericResponse]:
        """Tải ảnh từ URL bên ngoài vào hệ thống (V9.0)."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        asset = await media_service.fetch_remote_asset(
            repo=media_repo,
            url=data.url,
            campaign_id=data.campaign_id,
            owner_id=owner_id
        )

        if asset:
            return MediaDetailResponse(
                status="success",
                data=MediaAssetResponse.model_validate(asset)
            )
        else:
            return GenericResponse(status="error", message="Failed to fetch remote asset.")
