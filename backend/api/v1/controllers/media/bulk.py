# backend/api/v1/controllers/media/bulk.py
from litestar import post, Request
from backend.database.repositories import MediaRegistryRepository
from backend.services.media.media_service import media_service
from backend.services.media.schemas import (
    BulkDeleteRequest,
    BulkDownloadRequest,
    BulkDownloadResponse,
    BulkDownloadResponseData
)
from backend.api.v1.schemas.schemas import GenericResponse
from typing import Union

class MediaBulkController:
    @post("/bulk-delete")
    async def bulk_delete_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: BulkDeleteRequest
    ) -> GenericResponse:
        """Xóa hàng loạt tài nguyên."""
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

    @post("/bulk-download")
    async def bulk_download_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: BulkDownloadRequest
    ) -> Union[BulkDownloadResponse, GenericResponse]:
        """Tạo gói ZIP tải xuống hàng loạt."""
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
