import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from litestar import Controller, get, post, patch, delete, Request
from litestar.response import Redirect
from litestar.di import Provide

from backend.database.repositories import MediaRegistryRepository, provide_media_repo
from backend.services.media.media_service import media_service
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
    ) -> Dict[str, Any]:
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

        # Chuyển đổi sang format JSON serializable
        return {
            "status": "success",
            "data": {
                "items": [
                    {
                        "id": str(item.id),
                        "filename": item.filename,
                        "file_path": item.file_path,
                        "file_size": item.file_size,
                        "mime_type": item.mime_type,
                        "dimensions": item.dimensions,
                        "blurhash": item.blurhash,
                        "alt_text": item.alt_text,
                        "is_public": item.is_public,
                        "campaign_id": str(item.campaign_id) if item.campaign_id else None,
                        "created_at": item.created_at.isoformat(),
                        "metadata": item.media_metadata
                    }
                    for item in result["items"]
                ],
                "total": result["total"],
                "limit": result["limit"],
                "offset": result["offset"]
            }
        }

    @get("/stats")
    async def get_media_stats(self, request: Request, media_repo: MediaRegistryRepository) -> Dict[str, Any]:
        """Lấy số liệu thống kê kho tài nguyên (V9.0 Analytics)."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")
        stats = await media_service.get_stats(media_repo, owner_id=owner_id)
        return {"status": "success", "data": stats}

    @get("/{asset_id:uuid}")
    async def get_media_detail(self, asset_id: UUID, request: Request, media_repo: MediaRegistryRepository) -> Dict[str, Any]:
        """Lấy thông tin chi tiết một tài nguyên."""
        asset = await media_repo.get(str(asset_id))
        if not asset:
            return {"status": "error", "message": "Asset not found"}

        # RBAC Check (V10.0 Elite)
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")
        if not asset.is_public and asset.owner_id and asset.owner_id != owner_id:
            return {"status": "error", "message": "Access denied"}

        return {
            "status": "success",
            "data": {
                "id": str(asset.id),
                "filename": asset.filename,
                "file_path": asset.file_path,
                "metadata": asset.media_metadata
            }
        }

    @patch("/{asset_id:uuid}")
    async def update_media(self, asset_id: UUID, request: Request, media_repo: MediaRegistryRepository) -> GenericResponse:
        """Cập nhật Metadata (Alt text, Tags) - Đẳng cấp SEO."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        data = await request.json()
        updated = await media_service.update_metadata(media_repo, str(asset_id), data, owner_id=owner_id)

        if not updated:
            return GenericResponse(status="error", message="Asset not found or unauthorized")

        return GenericResponse(status="success", message="Media metadata updated.")

    @delete("/{asset_id:uuid}")
    async def delete_media(
        self,
        asset_id: UUID,
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

    @post("/{asset_id:uuid}/restore")
    async def restore_media(self, asset_id: UUID, request: Request, media_repo: MediaRegistryRepository) -> GenericResponse:
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
        permanent: bool = False
    ) -> GenericResponse:
        """Xóa hàng loạt tài nguyên (Hỗ trợ Soft-delete V10.0)."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        data = await request.json()
        ids = data.get("ids", [])

        if not ids:
            return GenericResponse(status="error", message="No IDs provided")

        success = await media_service.bulk_delete(media_repo, ids, permanent=permanent, owner_id=owner_id)

        if success:
            msg = f"Successfully moved {len(ids)} assets to trash." if not permanent else f"Successfully purged {len(ids)} assets."
            return GenericResponse(status="success", message=msg)
        else:
            return GenericResponse(status="error", message="Bulk delete failed or unauthorized.")

    @get("/{asset_id:uuid}/thumb")
    async def get_media_thumbnail(
        self,
        asset_id: UUID,
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
        return Redirect(path=thumb_path)

    @post("/{asset_id:uuid}/edit")
    async def quick_edit_media(
        self,
        asset_id: UUID,
        request: Request,
        media_repo: MediaRegistryRepository
    ) -> Dict[str, Any]:
        """Xử lý nhanh ảnh (Xoay/Lật/Crop/Watermark) - V10.0 Elite Engine."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        data = await request.json()
        action = data.get("action")
        params = data.get("params")

        if not action:
            return {"status": "error", "message": "No action provided"}

        asset = await media_service.quick_edit(media_repo, str(asset_id), action, params=params, owner_id=owner_id)

        if asset:
            return {
                "status": "success",
                "data": {
                    "id": str(asset.id),
                    "dimensions": asset.dimensions,
                    "file_path": asset.file_path,
                    "metadata": asset.media_metadata
                }
            }
        else:
            return {"status": "error", "message": "Quick edit failed or unauthorized."}

    @post("/bulk-download")
    async def bulk_download_media(self, request: Request, media_repo: MediaRegistryRepository) -> Dict[str, Any]:
        """Tạo gói ZIP tải xuống hàng loạt (V76 Smart Download)."""
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        data = await request.json()
        ids = data.get("ids", [])

        if not ids:
            return {"status": "error", "message": "No IDs provided"}

        zip_url = await media_service.create_bulk_zip(media_repo, ids, owner_id=owner_id)

        if zip_url:
            return {"status": "success", "data": {"zip_url": zip_url}}
        else:
            return {"status": "error", "message": "Failed to generate ZIP or unauthorized."}

    @post("/fetch-remote")
    async def fetch_remote_media(self, request: Request, media_repo: MediaRegistryRepository) -> Dict[str, Any]:
        """Tải ảnh từ URL bên ngoài vào hệ thống (V9.0)."""
        data = await request.json()
        url = data.get("url")
        campaign_id = data.get("campaign_id")
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        if not url:
            return {"status": "error", "message": "No URL provided"}

        asset = await media_service.fetch_remote_asset(
            repo=media_repo,
            url=url,
            campaign_id=campaign_id,
            owner_id=owner_id
        )

        if asset:
            return {
                "status": "success",
                "data": {
                    "id": str(asset.id),
                    "filename": asset.filename,
                    "file_path": asset.file_path
                }
            }
        else:
            return {"status": "error", "message": "Failed to fetch remote asset."}
