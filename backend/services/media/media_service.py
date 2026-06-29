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

    def __init__(self) -> None:
        import asyncio
        self._background_tasks: set[asyncio.Task[object]] = set()

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

    async def generate_preview_image(
        self,
        repo: MediaRegistryRepository,
        prompt: str,
        aspect_ratio: str = "16:9",
        previous_preview_path: Optional[str] = None
    ) -> Optional[str]:
        """Tạo ảnh nháp WebP bằng AI sử dụng Google Gemini Nano Banana model thông qua Key Rotator.
        
        Không tạo bản ghi trong DB, chỉ lưu vật lý trên storage và tự động dọn dẹp ảnh nháp cũ.
        """
        try:
            # 1. Dọn dẹp ảnh nháp cũ nếu được truyền vào
            if previous_preview_path:
                clean_path = previous_preview_path.strip().lstrip("/")
                if clean_path.startswith("uploads/") and not ".." in clean_path:
                    logger.info(f"[MediaService] Cleaning up old preview: {clean_path}")
                    await storage.delete(clean_path)

            if not prompt or not prompt.strip():
                return "cleanup_success"

            from backend.services.ai_engine.core.key_rotator import key_rotator
            from google import genai
            from google.genai import types
            import asyncio
            import uuid

            # 2. Map aspect ratio
            ratio_map = {
                "1:1": "1:1",
                "16:9": "16:9",
                "4:3": "4:3",
                "3:2": "3:2",
            }
            api_ratio = ratio_map.get(aspect_ratio, "16:9")

            logger.info(f"[MediaService] Generating AI Preview: prompt='{prompt}', aspect={api_ratio}")

            # Danh sách các mô hình sinh ảnh hỗ trợ xoay vòng / fallback (Thứ tự ưu tiên từ cao xuống thấp)
            image_models = [
                "imagen-3.0-generate-002",  # Bản tiêu chuẩn chất lượng cao
                "imagen-3.0-fast-002"       # Bản tối ưu tốc độ, độ trễ thấp
            ]

            response = None
            last_error = None
            used_model = None

            for model_name in image_models:
                try:
                    # Lấy API key tương ứng cho model cụ thể này từ rotator
                    api_key = await key_rotator.get_key(model_name=model_name)
                    if not api_key:
                        logger.warning(f"[MediaService] No API key available for model: {model_name}")
                        continue

                    client = genai.Client(api_key=api_key)
                    logger.info(f"[MediaService] Attempting to generate AI image using model='{model_name}'")

                    # Gọi Gemini API trong thread executor
                    def call_gemini():
                        return client.models.generate_images(
                            model=model_name,
                            prompt=prompt,
                            config=types.GenerateImagesConfig(
                                number_of_images=1,
                                output_mime_type="image/jpeg",
                                aspect_ratio=api_ratio,
                            )
                        )

                    res = await asyncio.to_thread(call_gemini)
                    if res and res.generated_images:
                        response = res
                        used_model = model_name
                        break
                except Exception as e:
                    last_error = e
                    logger.warning(f"[MediaService] Image generation failed with model '{model_name}': {e}. Trying fallback...")

            if not response:
                raise ValueError(f"Tất cả các mô hình sinh ảnh đều thất bại. Lỗi cuối cùng: {last_error}")

            logger.info(f"[MediaService] Successfully generated image using model: {used_model}")
            image_bytes = response.generated_images[0].image.image_bytes

            # 4. Xử lý cắt cúp & resize an toàn chống OOM
            def process_bytes():
                import gc
                from PIL import Image
                from io import BytesIO
                
                if len(image_bytes) > 5 * 1024 * 1024:
                    raise ValueError("Tệp ảnh từ API quá lớn, từ chối xử lý.")
                
                with Image.open(BytesIO(image_bytes)) as img:
                    target_width, target_height = 750, 400
                    target_ratio = target_width / target_height
                    current_ratio = img.width / img.height
                    
                    if current_ratio > target_ratio:
                        new_height = target_height
                        new_width = int(img.width * (target_height / img.height))
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        left = (new_width - target_width) // 2
                        cropped_img = resized_img.crop((left, 0, left + target_width, target_height))
                    else:
                        new_width = target_width
                        new_height = int(img.height * (target_width / img.width))
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        top = (new_height - target_height) // 2
                        cropped_img = resized_img.crop((0, top, target_width, top + target_height))
                    
                    processed = cropped_img.convert('RGB')
                    output = BytesIO()
                    processed.save(output, format="WEBP", quality=90, optimize=True)
                    webp_data = output.getvalue()
                    output.close()
                    
                    if resized_img is not img:
                        resized_img.close()
                    if cropped_img is not processed:
                        cropped_img.close()
                    processed.close()
                    
                    gc.collect()
                    return webp_data

            processed_webp_bytes = await asyncio.to_thread(process_bytes)

            # 5. Lưu vật lý lên storage
            asset_id = str(uuid.uuid4())
            folder = datetime.now().strftime("%Y/%m")
            remote_path = f"uploads/{folder}/{asset_id}.webp"
            temp_path = f"/tmp/{asset_id}.webp"

            with open(temp_path, "wb") as f:
                f.write(processed_webp_bytes)

            try:
                final_url = await storage.upload(temp_path, remote_path)
                return final_url
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"[MediaService] generate_preview_image failed: {e}", exc_info=True)
            return None

    async def save_preview_image(
        self,
        repo: MediaRegistryRepository,
        file_path: str,
        prompt: str,
        campaign_id: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Optional[MediaRegistry]:
        """Đăng ký tệp ảnh WebP nháp sẵn có vào bảng MediaRegistry để quản lý trong FileManager."""
        try:
            import uuid
            # 1. Kiểm tra file tồn tại trên storage
            clean_path = file_path.strip().lstrip("/")
            file_name = clean_path.split("/")[-1]
            
            exists_on_storage = await storage.exists(clean_path)
            if not exists_on_storage:
                raise FileNotFoundError(f"Không tìm thấy file nháp tại: {clean_path}")

            # Đọc kích thước file từ disk (nếu là local storage)
            file_size = 0
            if os.getenv("STORAGE_PROVIDER", "local").lower() == "local":
                full_path = os.path.join("frontend/static", clean_path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
            
            if file_size == 0:
                file_size = 45000  # Fallback size

            asset_id = file_name.split(".")[0]
            if len(asset_id) != 36 or "-" not in asset_id:
                asset_id = str(uuid.uuid4())

            # Chuẩn hóa campaign context
            v_cid, seo_slug = await self._resolve_campaign_context(repo, campaign_id)

            # Cấu hình metadata chuẩn
            m_meta = {
                "status": "ready",
                "focal_point": {"x": 0.5, "y": 0.5},
                "original_source": "Gemini Nano Banana",
                "ai_description": prompt
            }

            # 2. Tạo đối tượng MediaRegistry
            asset = MediaRegistry(
                id=asset_id,
                filename=file_name,
                file_path=file_path,
                file_size=file_size,
                mime_type="image/webp",
                dimensions="750x400",
                campaign_id=v_cid,
                owner_id=owner_id,
                provider=str(os.getenv("STORAGE_PROVIDER", "local")),
                media_metadata=m_meta,
                is_public=True,
                alt_text=prompt
            )

            repo.session.add(asset)
            await repo.session.commit()

            # 3. Phát sự kiện EventBus cho SSE đồng bộ thời gian thực
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {"id": asset_id, "file_path": file_path, "campaign_id": v_cid})

            logger.info(f"[MediaService] Successfully registered preview in MediaRegistry: {file_path}")
            return asset

        except Exception as e:
            logger.error(f"[MediaService] save_preview_image failed: {e}", exc_info=True)
            return None

media_service = MediaService()

