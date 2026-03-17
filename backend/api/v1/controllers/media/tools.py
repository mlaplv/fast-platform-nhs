# backend/api/v1/controllers/media/tools.py
import logging
from typing import Union
from litestar import get, post, Request
from litestar.response import Redirect

from backend.database.repositories import MediaRegistryRepository
from backend.services.media.media_service import media_service
from backend.services.media.schemas import (
    QuickEditRequest,
    QuickEditResponse,
    FetchRemoteRequest,
    MediaDetailResponse,
    MediaAssetResponse
)
from backend.api.v1.schemas.schemas import GenericResponse

logger = logging.getLogger("media-api")

class MediaToolsController:
    @get("/{asset_id:str}/thumb")
    async def get_media_thumbnail(
        self,
        asset_id: str,
        request: Request,
        media_repo: MediaRegistryRepository,
        w: int = 300,
        q: int = 75
    ) -> Redirect:
        """Lấy đường dẫn Thumbnail cho ảnh."""
        asset = await media_repo.get(str(asset_id))
        if not asset:
            return Redirect(path="/v65_assets/placeholder.webp")

        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")
        if not asset.is_public and asset.owner_id and asset.owner_id != owner_id:
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
        """Xử lý nhanh ảnh (Xoay/Lật/Crop/Watermark)."""
        logger.info(f"[MediaRouter] Quick edit request for asset: {asset_id}, action: {data.action}")
        user = request.state.get("user", {})
        owner_id = user.get("sub") or user.get("id")

        asset = await media_service.quick_edit(
            media_repo,
            str(asset_id),
            data.action,
            params=data.params,
            owner_id=owner_id,
            source_url=data.source_url
        )

        if asset:
            return QuickEditResponse(
                status="success",
                data=MediaAssetResponse.model_validate(asset)
            )
        else:
            return GenericResponse(status="error", message="Quick edit failed or unauthorized.")

    @post("/fetch-remote")
    async def fetch_remote_media(
        self,
        request: Request,
        media_repo: MediaRegistryRepository,
        data: FetchRemoteRequest
    ) -> Union[MediaDetailResponse, GenericResponse]:
        """Tải ảnh từ URL bên ngoài vào hệ thống."""
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
