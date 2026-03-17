import logging
import os
from typing import List, Optional, Dict, Union, cast
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import MediaRegistry
from backend.services.storage.manager import storage
from backend.services.media.schemas import (
    MediaUpdateMetadata,
    MimeTypeBreakdown,
    QuickEditParams,
    MediaListResult,
    MediaStatsResult,
    MediaAssetResponse
)

logger = logging.getLogger("media-service")

class MediaService:
    """
    AI-Professional Media Service (V65.0)
    Cung cấp logic nghiệp vụ cho FileManager riêng biệt.
    """

    async def list_assets(
        self,
        session: AsyncSession,
        campaign_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None,
        include_deleted: bool = False,
        owner_id: Optional[str] = None
    ) -> MediaListResult:
        """Liệt kê và lọc ảnh với hiệu năng cao (Hỗ trợ AI Semantic Search)."""
        from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
        from backend.services.media.schemas import MediaMetadata
        import numpy as np
        from sqlalchemy import or_

        stmt = select(MediaRegistry)

        # 1. RBAC Logic (V10.0 Elite Safety)
        # Chỉ thấy ảnh công khai HOẶC ảnh do chính mình sở hữu
        if owner_id:
            stmt = stmt.where(or_(MediaRegistry.is_public == True, MediaRegistry.owner_id == owner_id))
        else:
            # Nếu không có context user (với các task hệ thống), chỉ lấy ảnh công khai
            stmt = stmt.where(MediaRegistry.is_public == True)

        # 2. Trash Logic
        if not include_deleted:
            stmt = stmt.where(MediaRegistry.deleted_at == None)
        else:
            stmt = stmt.where(MediaRegistry.deleted_at != None)

        if campaign_id:
            stmt = stmt.where(MediaRegistry.campaign_id == campaign_id)

        # Nếu không có search_query, dùng SQL query chuẩn cho nhanh
        if not search_query:
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_count = await session.execute(count_stmt)
            total = total_count.scalar_one()

            stmt = stmt.order_by(MediaRegistry.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            orm_assets = result.scalars().all()
            assets = [MediaAssetResponse.from_orm_model(a) for a in orm_assets]
        else:
            # AI Semantic Search Logic (R03 Evolution)
            # 1. Lấy toàn bộ assets của campaign/tenant để so khớp vector
            result = await session.execute(stmt)
            all_assets = list(result.scalars().all())
            total = len(all_assets)

            encoder = get_shared_encoder()
            if not encoder or not all_assets:
                # Fallback to basic keyword matching if AI not ready
                assets = [a for a in all_assets if search_query.lower() in a.filename.lower() or (a.alt_text and search_query.lower() in a.alt_text.lower())]
                assets = assets[offset : offset + limit]
            else:
                # 2. Encode query
                query_vec = cast(np.ndarray, list(encoder.embed([search_query]))[0])

                # 3. Calculate scores
                scored_assets = []
                for asset in all_assets:
                    # Lấy vector đã lưu hoặc tạo mới nếu chưa có
                    asset_meta_dict = asset.media_metadata or {}
                    # R105: Validating metadata structure
                    try:
                        asset_meta = MediaMetadata.model_validate(asset_meta_dict)
                    except Exception:
                        asset_meta = MediaMetadata()

                    asset_vec_data = asset_meta.embedding

                    if not asset_vec_data:
                        # Tạo text đại diện: filename + alt + tags
                        ai_tags = asset_meta.ai_tags
                        ai_desc = asset_meta.ai_description or ""
                        text = f"{asset.filename} {asset.alt_text or ''} {' '.join(ai_tags)} {ai_desc}"
                        asset_vec = cast(np.ndarray, list(encoder.embed([text]))[0])
                        asset_vec_list = asset_vec.tolist()

                        # Cập nhật ngược lại DB để lần sau nhanh hơn (Surgical Background Update)
                        asset_meta.embedding = asset_vec_list
                        asset.media_metadata = asset_meta.model_dump()
                        session.add(asset)
                    else:
                        asset_vec = np.array(asset_vec_data)

                    # Cosine Similarity
                    score = np.dot(query_vec, asset_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(asset_vec))
                    scored_assets.append((score, asset))

                # 4. Sort by score and paginate
                scored_assets.sort(key=lambda x: x[0], reverse=True)
                # Chỉ lấy các kết quả có độ liên quan > 0.3
                relevant_assets = [a for score, a in scored_assets if score > 0.3]
                assets = relevant_assets[offset : offset + limit]
                
                assets = [MediaAssetResponse.from_orm_model(a) for a in assets]

                # Commit embeddings nếu có cập nhật
                await session.commit()

        return MediaListResult(
            items=list(assets),
            total=total,
            limit=limit,
            offset=offset
        )


    async def update_metadata(
        self,
        session: AsyncSession,
        asset_id: str,
        metadata: MediaUpdateMetadata,
        owner_id: Optional[str] = None
    ) -> Optional[MediaRegistry]:
        """Cập nhật metadata (alt_text, AI tags...) cho ảnh."""
        from backend.services.media.schemas import MediaMetadata
        asset = await session.get(MediaRegistry, asset_id)
        if not asset:
            return None

        # RBAC Check (V10.0 Elite)
        if owner_id and asset.owner_id and asset.owner_id != owner_id:
            logger.warning(f"[RBAC] Unauthorized metadata update attempt on {asset_id} by {owner_id}")
            return None

        if metadata.alt_text is not None:
            asset.alt_text = metadata.alt_text

        if metadata.is_public is not None:
            asset.is_public = metadata.is_public

        if metadata.media_metadata is not None:
            # R105: Merge Pydantic models
            current_meta_dict = asset.media_metadata or {}
            try:
                current_meta = MediaMetadata.model_validate(current_meta_dict)
            except Exception:
                current_meta = MediaMetadata()

            # Update fields from the provided metadata
            update_dict = metadata.media_metadata.model_dump(exclude_unset=True)
            new_meta_dict = {**current_meta.model_dump(), **update_dict}
            asset.media_metadata = new_meta_dict

        await session.commit()
        return asset

    async def delete_asset(self, session: AsyncSession, asset_id: str, permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """
        Xóa tài nguyên.
        Mặc định là Soft-delete (V10.0 Trash Bin).
        Nếu permanent=True sẽ xóa vĩnh viễn file vật lý và DB.
        """
        try:
            asset = await session.get(MediaRegistry, asset_id)
            if not asset:
                return False

            # RBAC Check (V10.0 Elite)
            if owner_id and asset.owner_id and asset.owner_id != owner_id:
                logger.warning(f"[RBAC] Unauthorized delete attempt on {asset_id} by {owner_id}")
                return False

            if permanent:
                # Xóa file vật lý qua Storage Provider (Local/S3/R2)
                await storage.delete(asset.file_path)
                await session.delete(asset)
            else:
                # Soft-delete
                from datetime import datetime, timezone
                asset.deleted_at = datetime.now(timezone.utc)

            await session.commit()
            return True
        except Exception as e:
            logger.error(f"[MediaService] Failed to delete asset {asset_id}: {e}")
            return False

    async def restore_asset(self, session: AsyncSession, asset_id: str, owner_id: Optional[str] = None) -> bool:
        """Khôi phục tài nguyên từ Thùng rác (V10.0)."""
        try:
            asset = await session.get(MediaRegistry, asset_id)
            if not asset:
                return False

            # RBAC Check (V10.0 Elite)
            if owner_id and asset.owner_id and asset.owner_id != owner_id:
                logger.warning(f"[RBAC] Unauthorized restore attempt on {asset_id} by {owner_id}")
                return False

            asset.deleted_at = None
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"[MediaService] Failed to restore asset {asset_id}: {e}")
            return False

    async def bulk_delete(self, session: AsyncSession, ids: List[str], permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """Xóa hàng loạt tài nguyên (Hỗ trợ Soft-delete V10.0)."""
        try:
            from sqlalchemy import and_
            stmt = select(MediaRegistry).where(MediaRegistry.id.in_(ids))

            # RBAC: Chỉ chọn những ảnh mình sở hữu để xóa
            if owner_id:
                stmt = stmt.where(MediaRegistry.owner_id == owner_id)

            result = await session.execute(stmt)
            assets = result.scalars().all()

            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            for asset in assets:
                if permanent:
                    await storage.delete(asset.file_path)
                    await session.delete(asset)
                else:
                    asset.deleted_at = now

            await session.commit()
            return True
        except Exception as e:
            logger.error(f"[MediaService] Bulk delete failed: {e}")
            return False

    async def get_thumbnail(self, asset_path: str, width: int = 300, quality: int = 75) -> Optional[str]:
        """
        Tạo và trả về đường dẫn Thumbnail (Dynamic Resizing).
        Hỗ trợ cả Local và Cloud Assets (V9.0).
        """
        import os
        from PIL import Image
        import httpx

        # 1. Xác định đường dẫn thực tế
        is_remote = asset_path.startswith("http")
        filename = os.path.basename(asset_path.split("?")[0])

        # 2. Tạo cache directory
        cache_dir = os.path.join("frontend/static/v65_assets/cache")
        os.makedirs(cache_dir, exist_ok=True)

        # 3. Tạo filename cho cache dựa trên thông số
        cache_filename = f"t_{width}_{quality}_{filename}"
        if not cache_filename.endswith(".webp"):
            cache_filename += ".webp"
        cache_path = os.path.join(cache_dir, cache_filename)

        # 4. Kiểm tra Cache (Hit)
        if os.path.exists(cache_path):
            return f"/v65_assets/cache/{cache_filename}"

        # 5. Xử lý ảnh (Miss)
        try:
            async def process_image(source_bytes):
                def _sync_process():
                    from io import BytesIO
                    with Image.open(BytesIO(source_bytes)) as img:
                        ratio = width / float(img.size[0])
                        height = int((float(img.size[1]) * float(ratio)))
                        thumb = img.resize((width, height), Image.Resampling.LANCZOS)
                        thumb.save(cache_path, "WEBP", quality=quality, optimize=True)
                    return f"/v65_assets/cache/{cache_filename}"

                import asyncio
                return await asyncio.to_thread(_sync_process)

            if is_remote:
                # Tải từ Cloud về để xử lý
                from backend.utils.http_client import SharedHttpClient
                client = SharedHttpClient.get_client()
                resp = await client.get(asset_path, timeout=10.0)
                resp.raise_for_status()
                return await process_image(resp.content)
            else:
                # Xử lý file local
                rel_path = asset_path.lstrip("/")
                full_original_path = os.path.join("frontend/static", rel_path)
                if not os.path.exists(full_original_path):
                    return asset_path

                with open(full_original_path, "rb") as f:
                    return await process_image(f.read())

        except Exception as e:
            logger.error(f"[MediaService] Thumbnail generation failed: {e}")
            return asset_path

    async def create_bulk_zip(self, session: AsyncSession, ids: List[str], owner_id: Optional[str] = None) -> Optional[str]:
        """Tạo file ZIP hàng loạt tài nguyên - Phục vụ tải xuống thông minh."""
        import os
        import zipfile
        from datetime import datetime
        from sqlalchemy import or_

        try:
            stmt = select(MediaRegistry).where(MediaRegistry.id.in_(ids))

            # RBAC Check (V10.0 Elite)
            # Chỉ cho phép tải ảnh công khai HOẶC ảnh do chính mình sở hữu
            if owner_id:
                stmt = stmt.where(or_(MediaRegistry.is_public == True, MediaRegistry.owner_id == owner_id))
            else:
                stmt = stmt.where(MediaRegistry.is_public == True)

            result = await session.execute(stmt)
            assets = result.scalars().all()

            if not assets:
                return None

            # Tạo thư mục download tạm
            download_dir = os.path.join("frontend/static/v65_assets/downloads")
            os.makedirs(download_dir, exist_ok=True)

            zip_filename = f"bulk_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join(download_dir, zip_filename)

            def make_zip():
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for asset in assets:
                        rel_path = asset.file_path.lstrip("/")
                        full_path = os.path.join("frontend/static", rel_path)
                        if os.path.exists(full_path):
                            # Thêm vào zip với tên gốc
                            zipf.write(full_path, arcname=asset.filename)
                return f"/v65_assets/downloads/{zip_filename}"

            import asyncio
            return await asyncio.to_thread(make_zip)
        except Exception as e:
            logger.error(f"[MediaService] ZIP generation failed: {e}")
            return None

    async def quick_edit(
        self,
        session: AsyncSession,
        asset_id: str,
        action: str,
        params: Optional[QuickEditParams] = None,
        owner_id: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Optional[MediaRegistry]:
        """Thực hiện xử lý nhanh (Xoay/Lật/Crop/Watermark) - V10.0 Elite."""
        import os
        from PIL import Image, ImageEnhance
        import uuid
        from backend.services.media.utils import calculate_smart_crop
        from backend.services.media.constants import AspectRatio, DEFAULT_QUALITY

        asset = await session.get(MediaRegistry, asset_id)
        if not asset:
            # V75: If not found, try to register on the fly if source_url is provided
            if source_url:
                logger.info(f"[QuickEdit] Asset {asset_id} not found, registering from source_url: {source_url}")
                asset = await self.fetch_remote_asset(session, source_url, owner_id=owner_id)
                if not asset:
                    logger.error(f"[QuickEdit] Failed to register asset on the fly from {source_url}")
                    return None
            else:
                return None

        # RBAC Check (V10.0 Elite)
        if owner_id and asset.owner_id and asset.owner_id != owner_id:
            logger.warning(f"[RBAC] Unauthorized quick-edit attempt on {asset_id} by {owner_id}")
            return None

        is_remote = asset.file_path.startswith("http")
        temp_path = f"/tmp/edit_{uuid.uuid4()}"

        try:
            # 1. Chuẩn bị file để xử lý
            if is_remote:
                from backend.utils.http_client import SharedHttpClient
                client = await SharedHttpClient.get_client()
                resp = await client.get(asset.file_path, timeout=20.0)
                resp.raise_for_status()
                with open(temp_path, "wb") as f:
                    f.write(resp.content)
                source_path = temp_path
            else:
                rel_path = asset.file_path.lstrip("/")
                source_path = os.path.join("frontend/static", rel_path)
                if not os.path.exists(source_path):
                    return None

            # 2. Xử lý ảnh (Async Thread)
            def process():
                with Image.open(source_path) as img:
                    # Convert to RGBA for watermark/transparency support
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')

                    if action == "rotate_left":
                        img = img.rotate(90, expand=True)
                    elif action == "rotate_right":
                        img = img.rotate(-90, expand=True)
                    elif action == "flip_h":
                        img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    elif action == "flip_v":
                        img = img.transpose(Image.FLIP_TOP_BOTTOM)
                    elif action == "crop" and params:
                        # CNS V76: Support both Direct Crop (x,y,w,h) and Center Crop (preset)
                        if params.preset:
                            preset_name = params.preset.upper()
                            target_ratio = AspectRatio[preset_name].value if preset_name in AspectRatio.__members__ else AspectRatio.SQUARE.value
                            # Center Crop uses (0.5, 0.5) as focal point
                            box = calculate_smart_crop(img.width, img.height, 0.5, 0.5, target_ratio)
                            img = img.crop(box)
                        else:
                            p_dict = params.model_dump()
                            x, y, w, h = p_dict.get('x', 0), p_dict.get('y', 0), p_dict.get('w', img.width), p_dict.get('h', img.height)
                            if w is None: w = img.width
                            if h is None: h = img.height
                            img = img.crop((x, y, x + w, y + h))
                    elif action == "smart_crop" and params:
                        # Smart Crop dựa trên Focal Point và Preset Ratio
                        preset_name = (params.preset or 'square').upper()
                        target_ratio = AspectRatio[preset_name].value if preset_name in AspectRatio.__members__ else AspectRatio.SQUARE.value

                        # Lấy focal point từ metadata, mặc định là tâm (0.5, 0.5)
                        meta_dict = asset.media_metadata or {}
                        try:
                            from backend.services.media.schemas import MediaMetadata
                            meta = MediaMetadata.model_validate(meta_dict)
                            f_x, f_y = meta.focal_point.x, meta.focal_point.y
                        except Exception:
                            f_x, f_y = 0.5, 0.5

                        box = calculate_smart_crop(img.width, img.height, f_x, f_y, target_ratio)
                        img = img.crop(box)
                    elif action == "watermark":
                        # Dynamic Watermarking (V10.0)
                        # Ưu tiên logo PNG, nếu không có sẽ fallback sang Text (Elite R03)
                        logo_path = "frontend/static/logo_watermark.png"
                        if os.path.exists(logo_path):
                            with Image.open(logo_path) as logo:
                                # Resize logo to 15% of image width
                                logo_w = int(img.width * 0.15)
                                logo_h = int(logo.height * (logo_w / logo.width))
                                logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

                                # Position: Bottom-Right with 20px padding
                                position = (img.width - logo_w - 20, img.height - logo_h - 20)

                                # Paste with alpha channel
                                img.paste(logo, position, logo if logo.mode == 'RGBA' else None)
                        else:
                            # Fallback: Smart Text Watermark
                            from PIL import ImageDraw, ImageFont
                            draw = ImageDraw.Draw(img)
                            text = "FAST-PLATFORM AI"

                            # Tính toán font size (5% chiều cao ảnh)
                            f_size = max(20, int(img.height * 0.04))
                            try:
                                # Thử load font hệ thống phổ biến trên Linux
                                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", f_size)
                            except:
                                font = ImageFont.load_default()

                            # Tính toán vị trí góc phải dưới
                            bbox = draw.textbbox((0, 0), text, font=font)
                            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                            pos = (img.width - tw - 30, img.height - th - 30)

                            # Vẽ shadow (để nổi bật trên mọi nền)
                            draw.text((pos[0]+2, pos[1]+2), text, font=font, fill=(0,0,0,100))
                            # Vẽ text chính (trắng mờ)
                            draw.text(pos, text, font=font, fill=(255,255,255,160))

                    # Save back
                    save_path = temp_path if is_remote else source_path
                    # Convert back to RGB if not webp/png to save space
                    if not (is_remote or source_path.endswith((".webp", ".png"))):
                        img = img.convert('RGB')

                    img.save(save_path, "WEBP", quality=DEFAULT_QUALITY, optimize=True)
                    return f"{img.width}x{img.height}"

            import asyncio
            new_dims = await asyncio.to_thread(process)

            # 3. Xác định đường dẫn mới và định dạng (Chuyển đổi sang WebP triệt để)
            old_file_path = asset.file_path
            new_file_path = old_file_path
            new_filename = asset.filename

            if not old_file_path.endswith(".webp"):
                new_file_path = os.path.splitext(old_file_path)[0] + ".webp"
                new_filename = os.path.splitext(asset.filename)[0] + ".webp"

            # 4. Upload / Rename file vật lý
            if is_remote:
                # Upload lên đường dẫn mới (hoặc cũ nếu không đổi extension)
                remote_path = "/".join(new_file_path.split("/")[-4:])
                await storage.upload(temp_path, remote_path)

                # Nếu đổi extension, xóa file cũ trên Cloud
                if new_file_path != old_file_path:
                    try:
                        old_remote_path = "/".join(old_file_path.split("/")[-4:])
                        await storage.delete(old_remote_path)
                    except Exception as e:
                        logger.debug(f"[MediaService] Failed to delete old remote asset {old_remote_path}: {e}")
            else:
                # Xử lý local
                if new_file_path != old_file_path:
                    rel_old = old_file_path.lstrip("/")
                    rel_new = new_file_path.lstrip("/")
                    full_old = os.path.join("frontend/static", rel_old)
                    full_new = os.path.join("frontend/static", rel_new)

                    if os.path.exists(full_old):
                        if os.path.exists(full_new) and full_old != full_new:
                            os.remove(full_new)
                        os.rename(full_old, full_new)

            # 5. Cập nhật DB
            asset.dimensions = new_dims
            asset.file_path = new_file_path
            asset.filename = new_filename
            asset.mime_type = "image/webp"
            asset.file_size = os.path.getsize(temp_path) if is_remote else os.path.getsize(os.path.join("frontend/static", new_file_path.lstrip("/")))

            await session.commit()

            # 5. Xóa cache thumbnail cục bộ
            cache_dir = os.path.join("frontend/static/v65_assets/cache")
            if os.path.exists(cache_dir):
                filename = os.path.basename(asset.file_path.split("?")[0])
                for f in os.listdir(cache_dir):
                    if filename in f:
                        try: os.remove(os.path.join(cache_dir, f))
                        except Exception as e:
                            logger.debug(f"[MediaService] Failed to remove cache file {f}: {e}")

            # 6. CDN Invalidation (Optional: Cloudflare)
            if is_remote and os.getenv("CF_API_TOKEN") and os.getenv("CF_ZONE_ID"):
                await self._purge_cdn_cache(asset.file_path)

            return asset
        except Exception as e:
            logger.error(f"[MediaService] Quick edit failed: {e}")
            return None
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def _purge_cdn_cache(self, url: str):
        """Xóa cache CDN Cloudflare (R03 Evolution)."""
        import httpx
        zone_id = os.getenv("CF_ZONE_ID")
        token = os.getenv("CF_API_TOKEN")
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"files": [url]}
                )
                logger.info(f"[CDN] Cache purged for: {url}")
        except Exception as e:
            logger.warning(f"[CDN] Invalidation failed: {e}")

    async def get_stats(self, session: AsyncSession, owner_id: Optional[str] = None) -> MediaStatsResult:
        """Thống kê kho tài nguyên (V9.0 Analytics)."""
        from sqlalchemy import func, or_

        # 1. Tổng quan
        stmt = select(
            func.count(MediaRegistry.id).label("count"),
            func.sum(MediaRegistry.file_size).label("total_size")
        )
        if owner_id:
            stmt = stmt.where(or_(MediaRegistry.is_public == True, MediaRegistry.owner_id == owner_id))
        else:
            stmt = stmt.where(MediaRegistry.is_public == True)

        result = await session.execute(stmt)
        row = result.one()

        # 2. Phân loại theo MIME type
        mime_stmt = select(
            MediaRegistry.mime_type,
            func.count(MediaRegistry.id).label("count"),
            func.sum(MediaRegistry.file_size).label("size")
        )
        if owner_id:
            mime_stmt = mime_stmt.where(or_(MediaRegistry.is_public == True, MediaRegistry.owner_id == owner_id))
        else:
            mime_stmt = mime_stmt.where(MediaRegistry.is_public == True)

        mime_stmt = mime_stmt.group_by(MediaRegistry.mime_type)
        mime_result = await session.execute(mime_stmt)

        breakdown: List[MimeTypeBreakdown] = [
            MimeTypeBreakdown(
                type=str(r.mime_type).split("/")[-1].upper(),
                count=int(r.count),
                size=int(r.size or 0)
            )
            for r in mime_result.all()
        ]

        return MediaStatsResult(
            total_count=int(row.count or 0),
            total_size=int(row.total_size or 0),
            breakdown=breakdown,
            storage_provider=str(os.getenv("STORAGE_PROVIDER", "local"))
        )

    async def upload_asset(
        self,
        session: AsyncSession,
        file_content: bytes,
        filename: str,
        content_type: str,
        campaign_id: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Optional[MediaRegistry]:
        """Xử lý upload file trực tiếp, convert sang WEBP và lưu hệ thống (V65.0 Upload)."""
        import uuid
        import os
        from PIL import Image
        from io import BytesIO
        from datetime import datetime

        try:
            asset_id = str(uuid.uuid4())
            folder = datetime.now().strftime("%Y/%m")

            # 1. Xử lý ảnh (Convert sang WEBP và lấy dimensions)
            def process_image() -> tuple[bytes, str]:
                with Image.open(BytesIO(file_content)) as img:
                    dims = f"{img.width}x{img.height}"
                    buffer = BytesIO()
                    # R105: Downscale for performance (max 1920px) - Consistent with MediaCompressor
                    if max(img.size) > 1920:
                        img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                        dims = f"{img.width}x{img.height}"

                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        processed_img = img.convert('RGBA')
                    else:
                        processed_img = img.convert('RGB')

                    processed_img.save(buffer, "WEBP", quality=90, optimize=True)
                    return buffer.getvalue(), dims

            import asyncio
            webp_content, dims = await asyncio.to_thread(process_image)

            # 2. Upload lên Storage
            final_filename = os.path.splitext(filename)[0] + ".webp"
            remote_path = f"uploads/{folder}/{asset_id}.webp"

            # Ghi file tạm để upload qua storage manager (nếu nó yêu cầu path)
            temp_path = f"/tmp/{asset_id}.webp"
            with open(temp_path, "wb") as f:
                f.write(webp_content)

            try:
                final_url = await storage.upload(temp_path, remote_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            # 3. Đăng ký vào Database
            asset = MediaRegistry(
                id=asset_id,
                filename=final_filename,
                file_path=final_url,
                file_size=len(webp_content),
                mime_type="image/webp",
                dimensions=dims,
                campaign_id=campaign_id,
                owner_id=owner_id,
                provider=str(os.getenv("STORAGE_PROVIDER", "local"))
            )

            session.add(asset)
            await session.commit()

            # 4. Trigger AI Analysis (Async)
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {
                "id": asset_id,
                "file_path": final_url,
                "campaign_id": campaign_id
            })

            return asset

        except Exception as e:
            logger.error(f"[MediaService] Direct upload failed: {e}")
            return None

    async def fetch_remote_asset(
        self,
        session: AsyncSession,
        url: str,
        campaign_id: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Optional[MediaRegistry]:
        """Tải ảnh từ URL và lưu vào hệ thống (V9.0 Remote Fetch)."""
        import uuid
        import mimetypes
        from backend.utils.http_client import SharedHttpClient

        try:
            # V75: Support local paths in fetch_remote_asset for 'on-the-fly' registration
            if not url.startswith("http"):
                rel_path = url.lstrip("/")
                # Try common static locations
                local_path = None
                for base in ["frontend/static", "."]:
                    p = os.path.join(base, rel_path)
                    if os.path.exists(p) and os.path.isfile(p):
                        local_path = p
                        break

                if local_path:
                    logger.info(f"[MediaService] Registering local ghost asset: {local_path}")
                    with open(local_path, "rb") as f:
                        content = f.read()

                    class MockResponse:
                        def __init__(self, content, ctHit):
                            self.content = content
                            self.headers = {"Content-Type": ctHit}
                        def raise_for_status(self): pass

                    response = MockResponse(content, mimetypes.guess_type(local_path)[0] or "image/jpeg")
                else:
                    logger.error(f"[MediaService] Local file not found for registration: {url}")
                    return None
            else:
                # 1. Tải file với timeout bảo vệ
                client = await SharedHttpClient.get_client()
                response = await client.get(url, timeout=10.0, follow_redirects=True)
                response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if not content_type or not content_type.startswith("image/"):
                logger.error(f"[MediaService] Source is not an image: {content_type}")
                return None

            # 2. Tạo định danh và đường dẫn
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            asset_id = str(uuid.uuid4())
            filename = url.split("/")[-1].split("?")[0] or f"remote_{asset_id[:8]}"
            if not filename.endswith(ext):
                filename += ext

            # Lưu vào thư mục theo tháng để dễ quản lý
            from datetime import datetime
            folder = datetime.now().strftime("%Y/%m")
            # remote_path = f"uploads/{folder}/{asset_id}{ext}" # Không dùng nữa vì convert sang webp

            # 3. Lưu file tạm, xử lý convert sang WEBP và upload
            temp_path = f"/tmp/{asset_id}{ext}"
            webp_path = f"/tmp/{asset_id}.webp"
            with open(temp_path, "wb") as f:
                f.write(response.content)

            # Lấy kích thước ảnh và convert sang WEBP (R103)
            from PIL import Image
            def process_initial() -> str:
                with Image.open(temp_path) as img:
                    dims = f"{img.width}x{img.height}"
                    # Convert to RGB/RGBA if needed and save as WEBP
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        processed_img = img.convert('RGBA')
                    else:
                        processed_img = img.convert('RGB')
                    processed_img.save(webp_path, "WEBP", quality=90, optimize=True)
                return dims

            import asyncio
            dims = await asyncio.to_thread(process_initial)

            # Cập nhật đường dẫn remote sang .webp
            remote_path = f"uploads/{folder}/{asset_id}.webp"
            final_url = await storage.upload(webp_path, remote_path)

            # Lấy dung lượng file thật sau khi nén (R01 Scout)
            actual_size = os.path.getsize(webp_path)

            # Xóa files tạm ngay (R00 Discipline)
            for p in [temp_path, webp_path]:
                if os.path.exists(p):
                    os.remove(p)

            # 4. Đăng ký vào Database
            # R21: Verify campaign & owner FK existence before commit to avoid IntegrityError
            valid_campaign_id = None
            if campaign_id:
                from backend.database.models import ContentCampaign
                from sqlalchemy import select
                stmt = select(ContentCampaign.id).where(ContentCampaign.id == campaign_id)
                res = await session.execute(stmt)
                if res.scalar():
                    valid_campaign_id = campaign_id
                else:
                    logger.warning(f"[MediaService] Orphaned fetch: Campaign {campaign_id} not found.")

            valid_owner_id = None
            if owner_id:
                from backend.database.models import User
                from sqlalchemy import select
                stmt = select(User.id).where(User.id == owner_id)
                res = await session.execute(stmt)
                if res.scalar():
                    valid_owner_id = owner_id
                else:
                    logger.warning(f"[MediaService] Orphaned fetch: Owner {owner_id} not found.")

            asset = MediaRegistry(
                id=asset_id,
                filename=filename if filename.endswith(".webp") else filename + ".webp",
                file_path=final_url,
                file_size=actual_size,
                mime_type="image/webp",
                dimensions=dims,
                campaign_id=valid_campaign_id,
                owner_id=valid_owner_id,
                provider=str(os.getenv("STORAGE_PROVIDER", "local"))
            )

            session.add(asset)
            await session.commit()

            # 5. Trigger AI Analysis (Async)
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {
                "id": asset_id,
                "file_path": final_url,
                "campaign_id": valid_campaign_id
            })

            return asset

        except Exception as e:
            logger.exception(f"[MediaService] Remote fetch failed: {e}")
            return None

    async def cleanup_temp_files(self) -> Dict[str, int]:
        """Dọn dẹp file tạm (ZIP > 24h, Cache > 7 ngày) - R03 Discipline."""
        import time

        stats = {"zip_deleted": 0, "cache_deleted": 0, "trash_purged": 0}
        now = time.time()

        # 1. Dọn dẹp ZIP (24h)
        zip_dir = "frontend/static/v65_assets/downloads"
        if os.path.exists(zip_dir):
            for f in os.listdir(zip_dir):
                f_path = os.path.join(zip_dir, f)
                if os.path.isfile(f_path) and now - os.path.getmtime(f_path) > 86400:
                    try:
                        os.remove(f_path)
                        stats["zip_deleted"] += 1
                    except Exception as e:
                        logger.error(f"[MediaService] Failed to delete ZIP {f}: {e}")

        # 2. Dọn dẹp Cache (7 ngày)
        cache_dir = "frontend/static/v65_assets/cache"
        if os.path.exists(cache_dir):
            for f in os.listdir(cache_dir):
                f_path = os.path.join(cache_dir, f)
                if os.path.isfile(f_path) and now - os.path.getmtime(f_path) > 604800:
                    try:
                        os.remove(f_path)
                        stats["cache_deleted"] += 1
                    except Exception as e:
                        logger.error(f"[MediaService] Failed to delete Cache {f}: {e}")

        # 3. Dọn dẹp Trash Bin (V10.0: Xóa vĩnh viễn sau 30 ngày)
        try:
            from backend.database import alchemy_config
            from datetime import datetime, timezone, timedelta

            cutoff = datetime.now(timezone.utc) - timedelta(days=30)

            async with alchemy_config.create_session_maker()() as session:
                stmt = select(MediaRegistry).where(
                    MediaRegistry.deleted_at != None,
                    MediaRegistry.deleted_at < cutoff
                )
                result = await session.execute(stmt)
                expired_assets = result.scalars().all()

                for asset in expired_assets:
                    # Xóa file vật lý
                    await storage.delete(asset.file_path)
                    # Xóa DB record
                    await session.delete(asset)
                    stats["trash_purged"] += 1

                if stats["trash_purged"] > 0:
                    await session.commit()
        except Exception as e:
            logger.error(f"[MediaService] Trash purge failed: {e}")

        if stats["zip_deleted"] > 0 or stats["cache_deleted"] > 0 or stats["trash_purged"] > 0:
            logger.info(f"[MediaService] Cleanup complete: {stats}")

        return stats


media_service = MediaService()
