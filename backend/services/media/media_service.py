import logging
import os
from typing import Optional, Union, Dict, List
from pydantic import JsonValue
from datetime import datetime, timezone

from backend.database.models import MediaRegistry, MediaUsage
from backend.database.repositories import MediaRegistryRepository, MediaUsageRepository
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

    async def restore_asset(self, repo: MediaRegistryRepository, asset_id: str, owner_id: Union[str, Dict[str, JsonValue], None] = None) -> bool:
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

    async def sync_links(self, repo: MediaRegistryRepository, entity_id: str, entity_type: str, current_urls: List[str]) -> None:
        """
        Elite V2.2: Neural Media Linking (Many-to-Many).
        Đồng bộ các liên kết sử dụng tài nguyên thông qua bảng trung gian MediaUsage.
        Hỗ trợ: Product, News, Banner, SystemSettings, ...
        """
        logger.info(f"[MediaService] Syncing {len(current_urls)} URLs for {entity_type}:{entity_id}")
        try:
            from sqlalchemy import delete, select, update, exists, func
            session = repo.session
            
            # 1. Trích xuất Asset IDs hiện có để tối ưu hóa
            old_usage_stmt = select(MediaUsage.asset_id).where(
                (MediaUsage.entity_id == entity_id) & (MediaUsage.entity_type == entity_type)
            )
            old_asset_ids = set((await session.execute(old_usage_stmt)).scalars().all())

            # 2. Xóa các liên kết cũ để làm sạch (Atomic Update)
            await session.execute(delete(MediaUsage).where(
                (MediaUsage.entity_id == entity_id) & (MediaUsage.entity_type == entity_type)
            ))

            # 3. Chuẩn hóa và Tìm Asset IDs mới
            new_asset_ids = set()
            if current_urls:
                from sqlalchemy import or_
                normalized_paths = []
                api_media_ids = []
                for url in current_urls:
                    if not url or not isinstance(url, str): continue
                    
                    if "/api/v1/media/" in url:
                        parts = url.split("/api/v1/media/")
                        if len(parts) > 1:
                            id_part = parts[1].split("/")[0].split("?")[0]
                            if len(id_part) == 36 and '-' in id_part:
                                api_media_ids.append(id_part)
                                continue

                    path = url.split("?")[0]
                    
                    # Elite Normalization: Xử lý URL tuyệt đối
                    if "://" in path:
                         # Bóc tách path sau domain (e.g. /storage/...)
                         parts = path.split("://")[1].split("/", 1)
                         path = "/" + parts[1] if len(parts) > 1 else "/"
                    
                    if not path.startswith("/"):
                        path = "/" + path
                    
                    normalized_paths.append(path)
                    normalized_paths.append(path.lstrip("/")) # Hỗ trợ cả hai định dạng đầu /
                
                if normalized_paths or api_media_ids:
                    import uuid
                    from sqlalchemy import or_
                    conditions = []
                    if normalized_paths:
                        conditions.append(MediaRegistry.file_path.in_(normalized_paths))
                    if api_media_ids:
                        valid_uuids = []
                        for id_str in api_media_ids:
                            try:
                                valid_uuids.append(uuid.UUID(id_str))
                            except ValueError: continue
                        if valid_uuids:
                            conditions.append(MediaRegistry.id.in_(valid_uuids))

                    if not conditions:
                         logger.warning(f"[MediaService] No valid conditions for {entity_type}:{entity_id}")
                    else:
                        stmt_assets = select(MediaRegistry.id).where(or_(*conditions))
                        new_asset_ids = set((await session.execute(stmt_assets)).scalars().all())

                        # Batch Insert usages (Đảm bảo tính nhất quán Many-to-Many)
                        for aid in new_asset_ids:
                            session.add(MediaUsage(
                                asset_id=aid,
                                entity_id=entity_id,
                                entity_type=entity_type
                            ))

            await session.flush() # Đẩy dữ liệu xuống DB trước khi cập nhật flag

            # 4. Cập nhật flag is_linked cho tập hợp các Asset bị thay đổi hiệu năng cao
            affected_ids = old_asset_ids.union(new_asset_ids)
            if affected_ids:
                for aid in affected_ids:
                    # Kiểm tra xem còn ai dùng asset này nữa không
                    usage_exists = await session.scalar(
                        select(func.count(MediaUsage.id)).where(MediaUsage.asset_id == aid)
                    )
                    await session.execute(
                        update(MediaRegistry)
                        .where(MediaRegistry.id == aid)
                        .values(is_linked=(usage_exists > 0))
                    )

            await session.commit() # [CRITICAL] Lưu vĩnh viễn thay đổi
            logger.info(f"[MediaService] Neural Sync: {entity_type}:{entity_id} linked with {len(new_asset_ids)} assets.")
        except Exception as e:
            await session.rollback() # [CRITICAL] Rollback nếu lỗi
            logger.error(f"[MediaService] Neural Sync Failed for {entity_id}: {e}")
            raise e

    async def cleanup_orphaned_assets(self, repo: MediaRegistryRepository, threshold_hours: int = 24) -> int:
        """
        Elite V2.2 Neural GC: Xóa vĩnh viễn các tài nguyên không còn bất kỳ liên kết sử dụng nào.
        Sử dụng LEFT JOIN để đảm bảo tính an toàn (Single Flow Integrity).
        """
        try:
            from sqlalchemy import select, outerjoin
            from datetime import timedelta
            
            cutoff = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
            
            # Tìm các Asset mà: 
            # 1. Không có bản ghi usage nào (Mồ côi hoàn toàn)
            # 2. Được tạo cách đây > threshold_hours
            # 3. Chưa bị xóa cứng
            # 4. TRÁNH XÓA các tệp client đã cô lập (client_uploads/ & avatars/)
            stmt = (
                select(MediaRegistry)
                .select_from(outerjoin(MediaRegistry, MediaUsage, MediaRegistry.id == MediaUsage.asset_id))
                .where(
                    MediaUsage.id == None,
                    MediaRegistry.deleted_at == None,
                    MediaRegistry.created_at < cutoff,
                    ~MediaRegistry.file_path.contains("client_uploads/"),
                    ~MediaRegistry.file_path.contains("avatars/"),
                    ~MediaRegistry.file_path.contains("uploads/img/"),
                    ~MediaRegistry.file_path.contains("uploads/video/")
                )
            )
            
            result = await repo.session.execute(stmt)
            orphans = result.scalars().all()
            
            count = 0
            for asset in orphans:
                # Elite Rule: Log trước khi xóa vĩnh viễn tài nguyên vật lý
                logger.warning(f"[GC] Purging orphaned asset: {asset.file_path} (ID: {asset.id})")
                success = await self.delete_asset(repo, str(asset.id), permanent=True)
                if success: count += 1
            
            if count > 0:
                logger.info(f"[MediaService] Neural GC: Permanently removed {count} orphaned assets.")
            return count
        except Exception as e:
            logger.error(f"[MediaService] Neural GC failed: {e}")
            return 0

    async def link_to_post(self, repo: MediaRegistryRepository, asset_ids: list[str], post_id: str, post_type: str, owner_id: Optional[str] = None) -> int:
        """
        Elite V2.2: Liên kết thủ công ảnh vào thực thể (Manual Linking).
        Hỗ trợ gán nhanh từ Toolbar trong FileManager.
        """
        try:
            session = repo.session
            count = 0
            for aid in asset_ids:
                # 1. Kiểm tra tồn tại
                asset = await repo.get_one_or_none(id=aid) if hasattr(repo, 'get_one_or_none') else await repo.get(aid)
                if not asset: continue
                if owner_id and asset.owner_id and asset.owner_id != owner_id: continue
                
                # 2. Thêm usage mới (nếu chưa có - Many-to-Many cho phép dùng nhiều nơi)
                from sqlalchemy import select
                stmt_exist = select(MediaUsage).where(
                    MediaUsage.asset_id == aid,
                    MediaUsage.entity_id == post_id,
                    MediaUsage.entity_type == post_type
                )
                existing = (await session.execute(stmt_exist)).scalar_one_or_none()
                
                if not existing:
                    session.add(MediaUsage(
                        asset_id=aid,
                        entity_id=post_id,
                        entity_type=post_type
                    ))
                    # 3. Cập nhật flag is_linked
                    asset.is_linked = True
                    count += 1
            
            await session.commit()
            return count
        except Exception as e:
            logger.error(f"[MediaService] Manual link failed: {e}")
            await session.rollback()
            return 0

media_service = MediaService()
