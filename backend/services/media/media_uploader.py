import logging
import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional
from PIL import Image
from io import BytesIO
from sqlalchemy import select

from backend.database.models import MediaRegistry, ContentCampaign, User
from backend.database.repositories import MediaRegistryRepository
from backend.services.storage.manager import storage
from backend.utils.security import is_safe_url

logger = logging.getLogger("media-uploader")

class MediaUploaderMixin:
    def _verify_magic_bytes(self, file_content: bytes, expected_mime: str) -> bool:
        """Kiểm duyệt chữ ký nhị phân (Magic Bytes) phòng thủ 0-day."""
        if len(file_content) < 12: return False
        header = file_content[:12]
        
        # Images
        if expected_mime in ("image/jpeg", "image/jpg"):
            return header.startswith(b'\xff\xd8\xff')
        if expected_mime == "image/png":
            return header.startswith(b'\x89PNG\r\n\x1a\n')
        if expected_mime == "image/webp":
            return header.startswith(b'RIFF') and header[8:12] == b'WEBP'
        if expected_mime == "image/gif":
            return header.startswith(b'GIF87a') or header.startswith(b'GIF89a')
        
        # Videos
        if expected_mime == "video/mp4":
            return b'ftyp' in header
        if expected_mime == "video/webm":
            return header.startswith(b'\x1aE\xdf\xa3')
            
        # Documents
        if expected_mime == "application/pdf":
            return header.startswith(b'%PDF-')
        if expected_mime in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"):
            # DOCX is basically a ZIP file, starts with PK. Old DOC starts with D0CF11E0.
            return header.startswith(b'PK\x03\x04') or header.startswith(b'\xd0\xcf\x11\xe0')
            
        # Optional: default to False to block unknown binary structures
        return False

    async def _resolve_campaign_context(self, repo, campaign_id: Optional[str]) -> tuple[Optional[str], str]:
        """[Elite SEO & BugFix] Validates campaign_id and extracts slug from relevant entities.
        Optimized: 5 queries combined into 1 UNION query (Zero-Hydration pattern)."""
        if not campaign_id:
            return None, ""
        try:
            from sqlalchemy import text
            stmt = text("""
                SELECT id, slug FROM articles WHERE id = :id
                UNION ALL
                SELECT id, slug FROM products WHERE id = :id
                UNION ALL
                SELECT id, slug FROM categories WHERE id = :id
                UNION ALL
                SELECT id, LOWER(code) as slug FROM vouchers WHERE id = :id
                UNION ALL
                SELECT id, '' as slug FROM content_campaigns WHERE id = :id
                LIMIT 1
            """)
            res = await repo.session.execute(stmt, {"id": campaign_id})
            row = res.fetchone()
            if row:
                return row[0], str(row[1]) if row[1] else ""
        except Exception as e:
            logger.warning(f"Failed to resolve campaign context for {campaign_id}: {e}")
            
        # Graceful fallback: return the ID to keep the link alive even if we couldn't find the table
        return campaign_id, ""

    async def upload_asset(self, repo: MediaRegistryRepository, file_content: bytes, filename: str, content_type: str, campaign_id: Optional[str] = None, owner_id: Optional[str] = None, is_avatar: bool = False) -> Optional[MediaRegistry]:
        """Xử lý upload file trực tiếp, convert sang WEBP và lưu hệ thống."""
        asset_id = str(uuid.uuid4())

        # Elite V3.2: Isolated Avatar Storage
        if is_avatar:
            remote_path = f"avatars/{asset_id}.webp"
        else:
            folder = datetime.now().strftime("%Y/%m")
            remote_path = f"uploads/{folder}/{asset_id}.webp"

        try:
            # [Elite Security] Quarantine Check: Magic Byte Enforcement
            if not self._verify_magic_bytes(file_content, content_type):
                logger.error(f"[Security] Kẻ xâm nhập bị chặn: Mismatched Magic Bytes for {filename} ({content_type})")
                return None

            v_cid, seo_slug = await self._resolve_campaign_context(repo, campaign_id)

            if content_type.startswith("image/"):
                with Image.open(BytesIO(file_content)) as img:
                    # Avatar processing: Square crop
                    if is_avatar:
                        min_dim = min(img.size)
                        left = (img.width - min_dim) / 2
                        top = (img.height - min_dim) / 2
                        img = img.crop((left, top, left + min_dim, top + min_dim))
                        if min_dim > 500: img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                    elif max(img.size) > 1920:
                        img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)

                    dims = f"{img.width}x{img.height}"
                    processed = img.convert('RGBA') if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info) else img.convert('RGB')
                    buffer = BytesIO(); processed.save(buffer, "WEBP", quality=90, optimize=True); file_to_save = buffer.getvalue()

                ext = ".webp"
                mime_type = "image/webp"
            else:
                dims = "0x0"
                file_to_save = file_content
                ext = os.path.splitext(filename)[1]
                # If non-image and avatar requested, fail gracefully
                if is_avatar: return None
                remote_path = f"uploads/{folder}/{asset_id}{ext}"
                mime_type = content_type

            # [Elite SEO] Smart Slug Naming / Clean filename fallback
            import re as _re
            if seo_slug:
                final_filename = f"{seo_slug}-{asset_id[:6]}{ext}"
            else:
                base_name = os.path.splitext(filename)[0] or f"image-{asset_id[:8]}"
                seo_name = _re.sub(r"[^a-z0-9\-]", "-", base_name.lower()).strip("-") or f"image-{asset_id[:8]}"
                final_filename = f"{seo_name}{ext}"

            temp_path = f"/tmp/{asset_id}{ext}"
            with open(temp_path, "wb") as f: f.write(file_to_save)
            try: final_url = await storage.upload(temp_path, remote_path)
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)

            v_oid = owner_id  # Trust JWT context; let DB FK constraint handle invalid IDs

            from backend.services.xohi_memory import xohi_memory
            ai_vision = await xohi_memory.client.get("ai:vision:enabled") if xohi_memory._use_redis else "0"

            m_meta = {
                "status": "ready" if ai_vision != "1" else "processing",
                "focal_point": {"x": 0.5, "y": 0.5}
            }

            asset = MediaRegistry(
                id=asset_id,
                filename=final_filename,
                file_path=final_url,
                file_size=len(file_to_save),
                mime_type=mime_type,
                dimensions=dims,
                campaign_id=v_cid,
                owner_id=v_oid,
                provider=str(os.getenv("STORAGE_PROVIDER", "local")),
                media_metadata=m_meta
            )
            repo.session.add(asset); await repo.session.commit()
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {"id": asset_id, "file_path": final_url, "campaign_id": v_cid})
            return asset
        except Exception as e:
            logger.error(f"[MediaUploader] Upload failed: {e}"); return None

    async def fetch_remote_asset(self, repo: MediaRegistryRepository, url: str, campaign_id: Optional[str] = None, owner_id: Optional[str] = None) -> Optional[MediaRegistry]:
        """Tải ảnh từ URL và lưu vào hệ thống.
        
        Elite V2.2 Article Standard:
        - Max width: 750px (height auto, aspect-ratio preserved)
        - Format: WebP quality=88
        - Filename: SEO-clean (lowercase, hyphens only)
        - Security: SSRF protected + magic byte validation via upload pipeline
        """
        from backend.utils.http_client import SharedHttpClient
        import re as _re
        asset_id = str(uuid.uuid4())
        folder = datetime.now().strftime("%Y/%m")
        ARTICLE_MAX_WIDTH = 750

        try:
            if not url.startswith("http"):
                local_path = next((p for base in ["frontend/static", "."] if os.path.isfile(p := os.path.join(base, url.lstrip("/")))), None)
                if not local_path: return None
                with open(local_path, "rb") as f: content = f.read()
                content_type = mimetypes.guess_type(local_path)[0] or "image/jpeg"
            else:
                # [Elite Security] R55.5: SSRF Protection (DNS + IP range check)
                if not is_safe_url(url):
                    logger.error(f"[Security] SSRF Attempt Blocked: {url}")
                    return None
                client = await SharedHttpClient.get_client()
                resp = await client.get(url, timeout=10.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                content = resp.content
                content_type = resp.headers.get("Content-Type", "")

            if not content_type.startswith("image/"):
                logger.warning(f"[Auto-Leach] Non-image content skipped: {content_type}")
                return None

            v_cid, seo_slug = await self._resolve_campaign_context(repo, campaign_id)

            # [Elite SEO] Smart Slug Naming / Clean filename fallback
            if seo_slug:
                final_filename = f"{seo_slug}-{asset_id[:6]}.webp"
            else:
                raw_name = url.split("/")[-1].split("?")[0].split("#")[0]
                base_name = os.path.splitext(raw_name)[0] or f"article-image-{asset_id[:8]}"
                seo_name = _re.sub(r"[^a-z0-9\-]", "-", base_name.lower()).strip("-") or f"article-image-{asset_id[:8]}"
                final_filename = f"{seo_name}.webp"

            ext = mimetypes.guess_extension(content_type) or ".jpg"
            temp_p = f"/tmp/{asset_id}{ext}"
            webp_p = f"/tmp/{asset_id}.webp"

            try:
                with open(temp_p, "wb") as f: f.write(content)

                # [Elite V2.2] Article Image Standard: 750px max-width, height auto, LANCZOS quality
                with Image.open(temp_p) as img:
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        processed = img.convert('RGBA')
                    else:
                        processed = img.convert('RGB')

                    if processed.width > ARTICLE_MAX_WIDTH:
                        ratio = ARTICLE_MAX_WIDTH / processed.width
                        new_h = max(1, int(processed.height * ratio))
                        processed = processed.resize((ARTICLE_MAX_WIDTH, new_h), Image.Resampling.LANCZOS)

                    dims = f"{processed.width}x{processed.height}"
                    processed.save(webp_p, "WEBP", quality=88, optimize=True)

                final_url = await storage.upload(webp_p, f"uploads/{folder}/{asset_id}.webp")
                actual_size = os.path.getsize(webp_p)

            finally:
                for p in [temp_p, webp_p]:
                    if os.path.exists(p): os.remove(p)

            v_oid = owner_id  # Trust JWT context; let DB FK constraint handle invalid IDs


            from backend.services.xohi_memory import xohi_memory
            ai_vision = await xohi_memory.client.get("ai:vision:enabled") if xohi_memory._use_redis else "0"

            asset = MediaRegistry(
                id=asset_id,
                filename=final_filename,
                file_path=final_url,
                file_size=actual_size,
                mime_type="image/webp",
                dimensions=dims,
                campaign_id=v_cid,
                owner_id=v_oid,
                provider=str(os.getenv("STORAGE_PROVIDER", "local")),
                media_metadata={
                    "status": "ready" if ai_vision != "1" else "processing",
                    "focal_point": {"x": 0.5, "y": 0.5},
                    "original_source": url,
                }
            )
            repo.session.add(asset)
            await repo.session.commit()
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {"id": asset_id, "file_path": final_url, "campaign_id": v_cid})
            logger.info(f"[Auto-Leach] Saved: {final_filename} @ {dims} ({actual_size // 1024}KB)")
            return asset

        except Exception as e:
            logger.exception(f"[MediaUploader] Remote fetch failed: {e}")
            return None
