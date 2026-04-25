import logging
from typing import List, Optional, Union
from litestar import Controller, get, post, patch, delete, Request
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Redirect
from litestar.exceptions import HTTPException
from litestar.di import Provide
from backend.database.repositories import MediaRegistryRepository, provide_media_repo
from backend.services.media.media_service import media_service
from backend.services.media.schemas import *
from backend.models.schemas import GenericResponse
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("media-api")

class MediaController(Controller):
    path = "/api/v1/media"
    guards = [PermissionGuard(PermissionEnum.MEDIA_READ)]
    dependencies = {"media_repo": Provide(provide_media_repo)}

    @get("/")
    async def list_media(self, request: Request, media_repo: MediaRegistryRepository, campaign_id: Optional[str] = None, q: Optional[str] = None, limit: int = 50, offset: int = 0, trash: bool = False, is_linked: Optional[bool] = None, linked_post_id: Optional[str] = None, linked_post_type: Optional[str] = None) -> MediaListResponse:
        """FileManager: Liệt kê tài nguyên (AI Search & Trash hỗ trợ)."""
        res = await media_service.list_assets(repo=media_repo, campaign_id=campaign_id, search_query=q, limit=limit, offset=offset, include_deleted=trash, owner_id=request.state.get("user"), is_linked=is_linked, linked_post_id=linked_post_id, linked_post_type=linked_post_type)
        return MediaListResponse(status="success", data=MediaListResponseData(items=res.items, total=res.total, limit=res.limit, offset=res.offset))

    @get("/settings/ai-vision")
    async def get_ai_vision_status(self) -> dict:
        return {"enabled": await media_service.get_ai_vision_status()}

    @patch("/settings/ai-vision")
    async def toggle_ai_vision(self, data: AIVisionStatusRequest) -> GenericResponse:
        ok = await media_service.toggle_ai_vision(data.enabled)
        return GenericResponse(status="success" if ok else "error", message="AI Vision state updated" if ok else "Redis error")

    @post("/", status_code=201, guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def upload_media(self, request: Request, media_repo: MediaRegistryRepository, data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART), campaign_id: Optional[str] = None) -> MediaDetailResponse:
        asset = await media_service.upload_asset(repo=media_repo, file_content=await data.read(), filename=data.filename, content_type=data.content_type, campaign_id=campaign_id, owner_id=request.state.get("user", {}).get("sub"))
        if not asset: raise HTTPException(status_code=500, detail="Upload failed")
        return MediaDetailResponse(status="success", data=MediaAssetResponse.model_validate(asset))

    @get("/stats")
    async def get_media_stats(self, request: Request, media_repo: MediaRegistryRepository) -> MediaStatsResponse:
        s = await media_service.get_stats(media_repo, owner_id=request.state.get("user"))
        return MediaStatsResponse(status="success", data=MediaStatsResponseData(total_count=s.total_count, total_size=s.total_size, total_trash_count=s.total_trash_count, breakdown=s.breakdown, storage_provider=s.storage_provider))

    @get("/{asset_id:str}")
    async def get_media_detail(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository) -> MediaDetailResponse:
        asset = await media_repo.get(str(asset_id))
        user = request.state.get("user", {})
        if not asset or (not asset.is_public and asset.owner_id and asset.owner_id != user.get("sub", user.get("id"))):
            raise HTTPException(status_code=404, detail="Asset not found or access denied")
        return MediaDetailResponse(status="success", data=MediaAssetResponse.model_validate(asset))

    @patch("/{asset_id:str}", guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def update_media(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository, data: MediaUpdateMetadata) -> GenericResponse:
        ok = await media_service.update_metadata(media_repo, str(asset_id), data, owner_id=request.state.get("user", {}).get("sub"))
        return GenericResponse(status="success" if ok else "error", message="Metadata updated" if ok else "Unauthorized/Not Found")

    @delete("/{asset_id:str}", status_code=200, guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def delete_media(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository, permanent: bool = False) -> GenericResponse:
        ok = await media_service.delete_asset(media_repo, str(asset_id), permanent=permanent, owner_id=request.state.get("user", {}).get("sub"))
        return GenericResponse(status="success" if ok else "error", message="Deleted" if ok else "Failed")

    @post("/{asset_id:str}/restore", guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def restore_media(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository) -> GenericResponse:
        ok = await media_service.restore_asset(media_repo, str(asset_id), owner_id=request.state.get("user"))
        return GenericResponse(status="success" if ok else "error", message="Restored" if ok else "Failed")

    @post("/bulk-delete", guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def bulk_delete_media(self, request: Request, media_repo: MediaRegistryRepository, data: BulkDeleteRequest) -> GenericResponse:
        ok = await media_service.bulk_delete(media_repo, data.ids, permanent=data.permanent, owner_id=request.state.get("user", {}).get("sub"))
        return GenericResponse(status="success" if ok else "error", message=f"Processed {len(data.ids)} assets")

    @patch("/bulk-update", guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def bulk_update_media(self, request: Request, media_repo: MediaRegistryRepository, data: BulkUpdateRequest) -> GenericResponse:
        ok = await media_service.bulk_update(media_repo, data, owner_id=request.state.get("user", {}).get("sub"))
        return GenericResponse(status="success" if ok else "error", message=f"Processed {len(data.updates)} metadata updates")

    @get("/{asset_id:str}/thumb")
    async def get_media_thumbnail(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository, w: int = 300, q: int = 75) -> Redirect:
        asset = await media_repo.get(str(asset_id))
        if not asset: return Redirect(path="/v65_assets/placeholder.webp")
        path = await media_service.get_thumbnail(asset.file_path, width=w, quality=q)
        return Redirect(path=path or "/v65_assets/placeholder.webp")

    @post("/{asset_id:str}/edit", guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def quick_edit_media(self, asset_id: str, request: Request, media_repo: MediaRegistryRepository, data: QuickEditRequest) -> QuickEditResponse:
        asset = await media_service.quick_edit(media_repo, str(asset_id), data.action, params=data.params, owner_id=request.state.get("user", {}).get("sub"), source_url=data.source_url, campaign_id=data.campaign_id)
        if not asset: raise HTTPException(status_code=500, detail="Edit failed")
        return QuickEditResponse(status="success", data=MediaAssetResponse.model_validate(asset))

    @post("/bulk-download")
    async def bulk_download_media(self, request: Request, media_repo: MediaRegistryRepository, data: BulkDownloadRequest) -> BulkDownloadResponse:
        url = await media_service.create_bulk_zip(media_repo, data.ids, owner_id=request.state.get("user", {}).get("sub"))
        if not url: raise HTTPException(status_code=500, detail="ZIP creation failed")
        return BulkDownloadResponse(status="success", data=BulkDownloadResponseData(zip_url=url))

    @post("/fetch-remote", guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def fetch_remote_media(self, request: Request, media_repo: MediaRegistryRepository, data: FetchRemoteRequest) -> MediaDetailResponse:
        asset = await media_service.fetch_remote_asset(repo=media_repo, url=data.url, campaign_id=data.campaign_id, owner_id=request.state.get("user", {}).get("sub"))
        if not asset: raise HTTPException(status_code=500, detail="Remote fetch failed")
        return MediaDetailResponse(status="success", data=MediaAssetResponse.model_validate(asset))

    @post("/link-to-post", guards=[PermissionGuard(PermissionEnum.MEDIA_WRITE)])
    async def link_media_to_post(self, request: Request, media_repo: MediaRegistryRepository, data: MediaLinkToPostRequest) -> GenericResponse:
        c = await media_service.link_to_post(repo=media_repo, asset_ids=data.asset_ids, post_id=data.post_id, post_type=data.post_type, owner_id=request.state.get("user", {}).get("sub"))
        return GenericResponse(status="success", message=f"Linked {c} assets")
