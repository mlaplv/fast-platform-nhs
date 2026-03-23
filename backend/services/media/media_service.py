import logging
import os
from typing import Optional, Union, Dict
from datetime import datetime, timezone

from backend.database.models import MediaRegistry
from backend.database.repositories import MediaRegistryRepository
from backend.services.storage.manager import storage

# Mixins (CNS V5.5 Modularization)
from backend.services.media.media_listing import MediaListingMixin
from backend.services.media.media_uploader import MediaUploaderMixin
from backend.services.media.media_editor import MediaEditorMixin
from backend.services.media.media_formatters import MediaFormattersMixin

logger = logging.getLogger("media-service")

class MediaService(
    MediaListingMixin, 
    MediaUploaderMixin, 
    MediaEditorMixin, 
    MediaFormattersMixin
):
    """
    AI-Professional Media Service (V66.0 Facade)
    Cung cấp logic nghiệp vụ cho FileManager.
    Modularized to comply with Martial Law (<300 lines).
    """

    async def delete_asset(self, repo: MediaRegistryRepository, asset_id: str, permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """Xóa tài nguyên (Soft-delete mặc định)."""
        try:
            asset = await repo.get_one_or_none(id=asset_id)
            if not asset or (owner_id and asset.owner_id and asset.owner_id != owner_id): return False
            if permanent:
                await storage.delete(asset.file_path); await repo.delete(asset_id)
            else:
                asset.deleted_at = datetime.now(timezone.utc); await repo.update(asset)
            await repo.session.commit(); return True
        except Exception as e:
            logger.error(f"[MediaService] Delete failed: {e}"); return False

    async def restore_asset(self, repo: MediaRegistryRepository, asset_id: str, owner_id: Union[str, Dict, None] = None) -> bool:
        """Khôi phục tài nguyên từ Thùng rác."""
        try:
            asset = await repo.get_one_or_none(id=asset_id)
            if not asset: return False
            is_admin = False; user_id = owner_id
            if isinstance(owner_id, dict):
                is_admin = any(r in ["ADMIN", "SUPER_ADMIN", "OWNER"] for r in owner_id.get("roles", []))
                user_id = owner_id.get("id") or owner_id.get("sub")
            if not is_admin and user_id and asset.owner_id and asset.owner_id != user_id: return False
            from sqlalchemy import func
            asset.deleted_at = None; asset.updated_at = func.now()
            await repo.update(asset); await repo.session.commit(); return True
        except Exception as e:
            logger.error(f"[MediaService] Restore failed: {e}"); return False

    async def bulk_delete(self, repo: MediaRegistryRepository, ids: list[str], permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """Xóa hàng loạt tài nguyên."""
        try:
            from sqlalchemy import select
            stmt = select(MediaRegistry).where(MediaRegistry.id.in_(ids))
            if owner_id: stmt = stmt.where(MediaRegistry.owner_id == owner_id)
            assets = (await repo.session.execute(stmt)).scalars().all()
            now = datetime.now(timezone.utc)
            for a in assets:
                if permanent: await storage.delete(a.file_path); await repo.delete(str(a.id))
                else: a.deleted_at = now; await repo.update(a)
            await repo.session.commit(); return True
        except Exception as e:
            logger.error(f"[MediaService] Bulk delete failed: {e}"); return False

    async def get_ai_vision_status(self) -> bool:
        """Lấy trạng thái AI Vision."""
        from backend.services.xohi_memory import xohi_memory
        return (await xohi_memory.client.get("ai:vision:enabled") if xohi_memory._use_redis else "0") == "1"

    async def toggle_ai_vision(self, enabled: bool) -> bool:
        """Bật/Tắt AI Vision."""
        from backend.services.xohi_memory import xohi_memory
        if not xohi_memory._use_redis: return False
        await xohi_memory.client.set("ai:vision:enabled", "1" if enabled else "0"); return True

media_service = MediaService()
