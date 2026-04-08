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

logger = logging.getLogger("media-uploader")

class MediaUploaderMixin:
    async def upload_asset(self, repo: MediaRegistryRepository, file_content: bytes, filename: str, content_type: str, campaign_id: Optional[str] = None, owner_id: Optional[str] = None) -> Optional[MediaRegistry]:
        """Xử lý upload file trực tiếp, convert sang WEBP và lưu hệ thống."""
        asset_id = str(uuid.uuid4())
        folder = datetime.now().strftime("%Y/%m")
        try:
            if content_type.startswith("image/"):
                with Image.open(BytesIO(file_content)) as img:
                    if max(img.size) > 1920: img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                    dims = f"{img.width}x{img.height}"
                    processed = img.convert('RGBA') if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info) else img.convert('RGB')
                    buffer = BytesIO(); processed.save(buffer, "WEBP", quality=90, optimize=True); file_to_save = buffer.getvalue()

                final_filename = os.path.splitext(filename)[0] + ".webp"
                remote_path = f"uploads/{folder}/{asset_id}.webp"
                mime_type = "image/webp"
            else:
                dims = "0x0"
                file_to_save = file_content
                final_filename = filename
                remote_path = f"uploads/{folder}/{asset_id}{os.path.splitext(filename)[1]}"
                mime_type = content_type

            temp_path = f"/tmp/{asset_id}{os.path.splitext(final_filename)[1]}"
            with open(temp_path, "wb") as f: f.write(file_to_save)
            try: final_url = await storage.upload(temp_path, remote_path)
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)

            v_cid = campaign_id if campaign_id and (await repo.session.execute(select(ContentCampaign.id).where(ContentCampaign.id == campaign_id))).scalar() else None
            v_oid = owner_id if owner_id and (await repo.session.execute(select(User.id).where(User.id == owner_id))).scalar() else None

            from backend.services.xohi_memory import xohi_memory
            ai_vision = await xohi_memory.client.get("ai:vision:enabled") if xohi_memory._use_redis else "0"

            # Metadata standard (V66): Always include focal_point and sync status
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
        """Tải ảnh từ URL và lưu vào hệ thống."""
        from backend.utils.http_client import SharedHttpClient
        asset_id = str(uuid.uuid4()); folder = datetime.now().strftime("%Y/%m")
        try:
            if not url.startswith("http"):
                local_path = next((p for base in ["frontend/static", "."] if os.path.isfile(p := os.path.join(base, url.lstrip("/")))), None)
                if not local_path: return None
                with open(local_path, "rb") as f: content = f.read()
                content_type = mimetypes.guess_type(local_path)[0] or "image/jpeg"
            else:
                client = await SharedHttpClient.get_client()
                resp = await client.get(url, timeout=10.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status(); content = resp.content; content_type = resp.headers.get("Content-Type", "")

            if not content_type.startswith("image/"): return None
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            temp_p, webp_p = f"/tmp/{asset_id}{ext}", f"/tmp/{asset_id}.webp"
            with open(temp_p, "wb") as f: f.write(content)
            
            with Image.open(temp_p) as img:
                dims = f"{img.width}x{img.height}"
                processed = img.convert('RGBA') if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info) else img.convert('RGB')
                processed.save(webp_p, "WEBP", quality=90, optimize=True)
            
            final_url = await storage.upload(webp_p, f"uploads/{folder}/{asset_id}.webp")
            actual_size = os.path.getsize(webp_p)
            for p in [temp_p, webp_p]: 
                if os.path.exists(p): os.remove(p)

            v_cid = campaign_id if campaign_id and (await repo.session.execute(select(ContentCampaign.id).where(ContentCampaign.id == campaign_id))).scalar() else None
            v_oid = owner_id if owner_id and (await repo.session.execute(select(User.id).where(User.id == owner_id))).scalar() else None

            from backend.services.xohi_memory import xohi_memory
            ai_vision = await xohi_memory.client.get("ai:vision:enabled") if xohi_memory._use_redis else "0"
            asset = MediaRegistry(id=asset_id, filename=(url.split("/")[-1].split("?")[0] or f"remote_{asset_id[:8]}").split(".")[0] + ".webp", file_path=final_url, file_size=actual_size, mime_type="image/webp", dimensions=dims, campaign_id=v_cid, owner_id=v_oid, provider=str(os.getenv("STORAGE_PROVIDER", "local")), media_metadata={"status": "ready" if ai_vision != "1" else "processing", "focal_point": {"x": 0.5, "y": 0.5}} if ai_vision != "1" else {})
            repo.session.add(asset); await repo.session.commit()
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {"id": asset_id, "file_path": final_url, "campaign_id": v_cid})
            return asset
        except Exception as e:
            logger.exception(f"[MediaUploader] Remote fetch failed: {e}"); return None
