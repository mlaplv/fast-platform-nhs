import logging
import os
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from backend.database.models import MediaRegistry
from backend.database.repositories import MediaRegistryRepository
from backend.services.storage.manager import storage

logger = logging.getLogger("media-service")

class MediaService:
    """
    AI-Professional Media Service (V65.0)
    Cung cấp logic nghiệp vụ cho FileManager riêng biệt.
    """

    async def list_assets(
        self,
        repo: MediaRegistryRepository,
        campaign_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None,
        include_deleted: bool = False,
        owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Liệt kê và lọc ảnh với hiệu năng cao (Hỗ trợ AI Semantic Search)."""
        from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
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
            total_count = await repo.session.execute(count_stmt)
            total = total_count.scalar_one()

            stmt = stmt.order_by(MediaRegistry.created_at.desc()).limit(limit).offset(offset)
            result = await repo.session.execute(stmt)
            assets = result.scalars().all()
        else:
            # AI Semantic Search Logic (R03 Evolution)
            # 1. Lấy toàn bộ assets của campaign/tenant để so khớp vector
            result = await repo.session.execute(stmt)
            all_assets = result.scalars().all()
            total = len(all_assets)

            encoder = get_shared_encoder()
            if not encoder or not all_assets:
                # Fallback to basic keyword matching if AI not ready
                q = f"%{search_query.lower()}%"
                assets = [a for a in all_assets if search_query.lower() in a.filename.lower() or (a.alt_text and search_query.lower() in a.alt_text.lower())]
                assets = assets[offset : offset + limit]
            else:
                # 2. Encode query
                query_vec = list(encoder.embed([search_query]))[0]

                # 3. Calculate scores
                scored_assets = []
                for asset in all_assets:
                    # Lấy vector đã lưu hoặc tạo mới nếu chưa có
                    asset_vec = asset.media_metadata.get("embedding")

                    if not asset_vec:
                        # Tạo text đại diện: filename + alt + tags
                        meta = asset.media_metadata or {}
                        text = f"{asset.filename} {asset.alt_text or ''} {' '.join(meta.get('ai_tags', []))} {meta.get('ai_description', '')}"
                        asset_vec = list(encoder.embed([text]))[0].tolist()

                        # Cập nhật ngược lại DB để lần sau nhanh hơn (Surgical Background Update)
                        asset.media_metadata = {**asset.media_metadata, "embedding": asset_vec}
                        repo.session.add(asset)

                    # Cosine Similarity
                    score = np.dot(query_vec, asset_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(asset_vec))
                    scored_assets.append((score, asset))

                # 4. Sort by score and paginate
                scored_assets.sort(key=lambda x: x[0], reverse=True)
                # Chỉ lấy các kết quả có độ liên quan > 0.3
                assets = [a for score, a in scored_assets if score > 0.3]
                assets = assets[offset : offset + limit]

                # Commit embeddings nếu có cập nhật
                await repo.session.commit()

        return {
            "items": assets,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    async def update_metadata(
        self,
        repo: MediaRegistryRepository,
        asset_id: str,
        metadata: Dict[str, Any],
        owner_id: Optional[str] = None
    ) -> Optional[MediaRegistry]:
        """Cập nhật metadata (alt_text, AI tags...) cho ảnh."""
        asset = await repo.get(asset_id)
        if not asset:
            return None

        # RBAC Check (V10.0 Elite)
        if owner_id and asset.owner_id and asset.owner_id != owner_id:
            logger.warning(f"[RBAC] Unauthorized metadata update attempt on {asset_id} by {owner_id}")
            return None

        if "alt_text" in metadata:
            asset.alt_text = metadata["alt_text"]

        if "is_public" in metadata:
            asset.is_public = bool(metadata["is_public"])

        if "media_metadata" in metadata:
            current_meta = dict(asset.media_metadata or {})
            current_meta.update(metadata["media_metadata"])
            asset.media_metadata = current_meta

        await repo.update(asset)
        await repo.session.commit()
        return asset

    async def delete_asset(self, repo: MediaRegistryRepository, asset_id: str, permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """
        Xóa tài nguyên.
        Mặc định là Soft-delete (V10.0 Trash Bin).
        Nếu permanent=True sẽ xóa vĩnh viễn file vật lý và DB.
        """
        try:
            asset = await repo.get(asset_id)
            if not asset:
                return False

            # RBAC Check (V10.0 Elite)
            if owner_id and asset.owner_id and asset.owner_id != owner_id:
                logger.warning(f"[RBAC] Unauthorized delete attempt on {asset_id} by {owner_id}")
                return False

            if permanent:
                # Xóa file vật lý qua Storage Provider (Local/S3/R2)
                await storage.delete(asset.file_path)
                await repo.delete(asset_id)
            else:
                # Soft-delete
                from datetime import datetime, timezone
                asset.deleted_at = datetime.now(timezone.utc)
                await repo.update(asset)

            await repo.session.commit()
            return True
        except Exception as e:
            logger.error(f"[MediaService] Failed to delete asset {asset_id}: {e}")
            return False

    async def restore_asset(self, repo: MediaRegistryRepository, asset_id: str, owner_id: Optional[str] = None) -> bool:
        """Khôi phục tài nguyên từ Thùng rác (V10.0)."""
        try:
            asset = await repo.get(asset_id)
            if not asset:
                return False

            # RBAC Check (V10.0 Elite)
            if owner_id and asset.owner_id and asset.owner_id != owner_id:
                logger.warning(f"[RBAC] Unauthorized restore attempt on {asset_id} by {owner_id}")
                return False

            asset.deleted_at = None
            await repo.update(asset)
            await repo.session.commit()
            return True
        except Exception as e:
            logger.error(f"[MediaService] Failed to restore asset {asset_id}: {e}")
            return False

    async def bulk_delete(self, repo: MediaRegistryRepository, ids: List[str], permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """Xóa hàng loạt tài nguyên (Hỗ trợ Soft-delete V10.0)."""
        try:
            from sqlalchemy import and_
            stmt = select(MediaRegistry).where(MediaRegistry.id.in_(ids))

            # RBAC: Chỉ chọn những ảnh mình sở hữu để xóa
            if owner_id:
                stmt = stmt.where(MediaRegistry.owner_id == owner_id)

            result = await repo.session.execute(stmt)
            assets = result.scalars().all()

            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            for asset in assets:
                if permanent:
                    await storage.delete(asset.file_path)
                    await repo.delete(str(asset.id))
                else:
                    asset.deleted_at = now
                    await repo.update(asset)

            await repo.session.commit()
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

    async def create_bulk_zip(self, repo: MediaRegistryRepository, ids: List[str], owner_id: Optional[str] = None) -> Optional[str]:
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

            result = await repo.session.execute(stmt)
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

    async def quick_edit(self, repo: MediaRegistryRepository, asset_id: str, action: str, params: Optional[Dict[str, Any]] = None, owner_id: Optional[str] = None) -> Optional[MediaRegistry]:
        """Thực hiện xử lý nhanh (Xoay/Lật/Crop/Watermark) - V10.0 Elite."""
        import os
        from PIL import Image, ImageEnhance
        import uuid

        asset = await repo.get(asset_id)
        if not asset:
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
                client = SharedHttpClient.get_client()
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
                        # params: {x, y, w, h}
                        x, y, w, h = params.get('x', 0), params.get('y', 0), params.get('w', img.width), params.get('h', img.height)
                        img = img.crop((x, y, x + w, y + h))
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

                    img.save(save_path, "WEBP" if is_remote or source_path.endswith(".webp") else img.format, quality=90)
                    return f"{img.width}x{img.height}"

            import asyncio
            new_dims = await asyncio.to_thread(process)

            # 3. Upload lại nếu là ảnh Cloud
            if is_remote:
                # Trích xuất remote path từ URL cũ
                # Giả định URL có dạng: https://.../uploads/2026/03/id.webp
                remote_path = "/".join(asset.file_path.split("/")[-4:])
                await storage.upload(temp_path, remote_path)

            # 4. Cập nhật DB
            asset.dimensions = new_dims
            await repo.update(asset)
            await repo.session.commit()

            # 5. Xóa cache thumbnail cục bộ
            cache_dir = os.path.join("frontend/static/v65_assets/cache")
            if os.path.exists(cache_dir):
                filename = os.path.basename(asset.file_path.split("?")[0])
                for f in os.listdir(cache_dir):
                    if filename in f:
                        try: os.remove(os.path.join(cache_dir, f))
                        except: pass

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

    async def get_stats(self, repo: MediaRegistryRepository, owner_id: Optional[str] = None) -> Dict[str, Any]:
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

        result = await repo.session.execute(stmt)
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
        mime_result = await repo.session.execute(mime_stmt)

        breakdown = [
            {"type": r.mime_type.split("/")[-1].upper(), "count": r.count, "size": r.size}
            for r in mime_result.all()
        ]

        return {
            "total_count": row.count or 0,
            "total_size": int(row.total_size or 0),
            "breakdown": breakdown,
            "storage_provider": os.getenv("STORAGE_PROVIDER", "local")
        }

    async def fetch_remote_asset(
        self,
        repo: MediaRegistryRepository,
        url: str,
        campaign_id: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Optional[MediaRegistry]:
        """Tải ảnh từ URL và lưu vào hệ thống (V9.0 Remote Fetch)."""
        import httpx
        import uuid
        import mimetypes
        from backend.utils.http_client import SharedHttpClient

        try:
            # 1. Tải file với timeout bảo vệ
            client = SharedHttpClient.get_client()
            response = await client.get(url, timeout=10.0, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                logger.error(f"[MediaService] URL is not an image: {content_type}")
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
            remote_path = f"uploads/{folder}/{asset_id}{ext}"

            # 3. Lưu file tạm và upload qua Storage Provider
            temp_path = f"/tmp/{asset_id}{ext}"
            with open(temp_path, "wb") as f:
                f.write(response.content)

            # Lấy kích thước ảnh ngay tại đây (R01 Scout)
            from PIL import Image
            with Image.open(temp_path) as img:
                dims = f"{img.width}x{img.height}"

            final_url = await storage.upload(temp_path, remote_path)

            # Xóa file tạm ngay (R00 Discipline)
            if os.path.exists(temp_path):
                os.remove(temp_path)

            # 4. Đăng ký vào Database
            asset = MediaRegistry(
                id=asset_id,
                filename=filename,
                file_path=final_url,
                file_size=len(response.content),
                mime_type=content_type,
                dimensions=dims,
                campaign_id=campaign_id,
                owner_id=owner_id,
                provider=os.getenv("STORAGE_PROVIDER", "local")
            )

            await repo.add(asset)
            await repo.session.commit()

            # 5. Trigger AI Analysis (Async)
            # Giả định có task phân tích ảnh sẵn có trong hệ thống
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {
                "id": asset_id,
                "file_path": final_url,
                "campaign_id": campaign_id
            })

            return asset

        except Exception as e:
            logger.error(f"[MediaService] Remote fetch failed: {e}")
            return None

    async def cleanup_temp_files(self) -> Dict[str, int]:
        """Dọn dẹp file tạm (ZIP > 24h, Cache > 7 ngày) - R03 Discipline."""
        import os
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
            from sqlalchemy import select

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
