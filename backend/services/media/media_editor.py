import logging
import os
import uuid
from typing import Optional
from PIL import Image
from backend.database.models import MediaRegistry
from backend.database.repositories import MediaRegistryRepository
from backend.services.media.schemas import MediaUpdateMetadata, QuickEditParams, MediaMetadata
from backend.services.media.utils import calculate_smart_crop
from backend.services.media.constants import AspectRatio, DEFAULT_QUALITY
from backend.services.storage.manager import storage

logger = logging.getLogger("media-editor")

class MediaEditorMixin:
    async def update_metadata(self, repo: MediaRegistryRepository, asset_id: str, metadata: MediaUpdateMetadata, owner_id: Optional[str] = None) -> Optional[MediaRegistry]:
        """Cập nhật metadata (alt_text, AI tags...) cho ảnh."""
        asset = await repo.get_one_or_none(id=asset_id)
        if not asset or (owner_id and asset.owner_id and asset.owner_id != owner_id): return None
        if metadata.alt_text is not None: asset.alt_text = metadata.alt_text
        if metadata.is_public is not None: asset.is_public = metadata.is_public
        if metadata.media_metadata is not None:
            from backend.services.media.schemas import MediaMetadata
            curr = MediaMetadata.model_validate(asset.media_metadata or {})
            asset.media_metadata = {**curr.model_dump(), **metadata.media_metadata.model_dump(exclude_unset=True)}
        await repo.update(asset); await repo.session.commit(); return asset

    async def bulk_update(self, repo: MediaRegistryRepository, data: "BulkUpdateRequest", owner_id: Optional[str] = None) -> bool:
        """Cập nhật metadata hàng loạt tài nguyên."""
        try:
            from backend.services.media.schemas import MediaMetadata
            for item in data.updates:
                asset = await repo.get_one_or_none(id=item.id)
                if not asset or (owner_id and asset.owner_id and asset.owner_id != owner_id): continue
                if item.metadata.alt_text is not None: asset.alt_text = item.metadata.alt_text
                if item.metadata.is_public is not None: asset.is_public = item.metadata.is_public
                if item.metadata.media_metadata is not None:
                    curr = MediaMetadata.model_validate(asset.media_metadata or {})
                    asset.media_metadata = {**curr.model_dump(), **item.metadata.media_metadata.model_dump(exclude_unset=True)}
                repo.session.add(asset)
            await repo.session.commit(); return True
        except Exception as e:
            logger.error(f"[MediaEditor] Bulk update failed: {e}")
            await repo.session.rollback(); return False

    async def link_to_post(self, repo: MediaRegistryRepository, asset_ids: list[str], post_id: str, post_type: str, owner_id: Optional[str] = None) -> int:
        """Gắn nhãn bài viết/sản phẩm cho danh sách ảnh."""
        from sqlalchemy import select
        stmt = select(MediaRegistry).where(MediaRegistry.id.in_(asset_ids))
        if owner_id: stmt = stmt.where(MediaRegistry.owner_id == owner_id)
        assets = (await repo.session.execute(stmt)).scalars().all()
        for a in assets: a.linked_post_id, a.linked_post_type = post_id, post_type; repo.session.add(a)
        await repo.session.commit(); return len(assets)

    async def quick_edit(self, repo: MediaRegistryRepository, asset_id: str, action: str, params: Optional[QuickEditParams] = None, owner_id: Optional[str] = None, source_url: Optional[str] = None, campaign_id: Optional[str] = None) -> Optional[MediaRegistry]:
        """Thực hiện xử lý nhanh (Xoay/Lật/Crop/Watermark/SEO)."""
        asset = await repo.get_one_or_none(id=asset_id)
        if not asset and source_url: asset = await self.fetch_remote_asset(repo, source_url, owner_id=owner_id, campaign_id=campaign_id)
        if not asset or (owner_id and asset.owner_id and asset.owner_id != owner_id): return None
        
        # Elite V2.2: Neural SEO Sync Action
        if action == "optimize-seo":
            from backend.services.xohi.creative_studio.operatives.media_analyst import MediaAnalyst
            import asyncio
            from backend.services.xohi_memory import xohi_memory
            
            analyst = MediaAnalyst()
            flag = await xohi_memory.client.get("ai:vision:enabled") if xohi_memory._use_redis else b"0"
            # Redis returns bytes or string depending on client, usually bytes here
            ai_vision = flag.decode() if isinstance(flag, bytes) else str(flag)
            
            if ai_vision == "1":
                asyncio.create_task(analyst.process_registry_entry(str(asset.id)))
            else:
                asyncio.create_task(analyst.heuristic_analysis(str(asset.id)))
            return asset

        is_remote = asset.file_path.startswith("http")
        t_p = f"/tmp/edit_{uuid.uuid4()}"
        try:
            if is_remote:
                from backend.utils.http_client import SharedHttpClient
                with open(t_p, "wb") as f: f.write((await (await SharedHttpClient.get_client()).get(asset.file_path, timeout=20.0)).content)
                src_p = t_p
            else: src_p = os.path.join("frontend/static", asset.file_path.lstrip("/"))
            if not os.path.exists(src_p): return None

            def process():
                with Image.open(src_p) as img:
                    img = img.convert('RGBA')
                    if action == "rotate_left": img = img.rotate(90, expand=True)
                    elif action == "rotate_right": img = img.rotate(-90, expand=True)
                    elif action == "flip_h": img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    elif action == "flip_v": img = img.transpose(Image.FLIP_TOP_BOTTOM)
                    elif action in ["crop", "smart_crop"] and params:
                        ratio = AspectRatio[params.preset.upper()].value if params.preset and params.preset.upper() in AspectRatio.__members__ else AspectRatio.SQUARE.value
                        if action == "smart_crop" or params.preset:
                            try: m = MediaMetadata.model_validate(asset.media_metadata or {}); fx, fy = m.focal_point.x, m.focal_point.y
                            except: fx, fy = 0.5, 0.5
                            img = img.crop(calculate_smart_crop(img.width, img.height, fx, fy, ratio))
                        else:
                            d = params.model_dump(); x, y, w, h = d.get('x', 0), d.get('y', 0), d.get('w', img.width), d.get('h', img.height)
                            img = img.crop((x, y, x + (w or img.width), y + (h or img.height)))
                    elif action == "watermark":
                        logo_p = "frontend/static/uploads/img/logo_transparent.webp"
                        if os.path.exists(logo_p):
                            with Image.open(logo_p) as logo:
                                # Professional scaling: 12% of image width
                                lw = int(img.width * 0.12)
                                lh = int(logo.height * (lw / logo.width))
                                logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
                                # Position at bottom-right with 2.5% padding
                                padding = int(img.width * 0.025)
                                img.paste(logo, (img.width - lw - padding, img.height - lh - padding), logo if logo.mode == 'RGBA' else None)
                    
                    s_p = t_p if is_remote else src_p
                    img.save(s_p, "WEBP", quality=DEFAULT_QUALITY, optimize=True); return f"{img.width}x{img.height}"

            import asyncio
            asset.dimensions = await asyncio.to_thread(process)
            old_p, new_p = asset.file_path, asset.file_path if asset.file_path.endswith(".webp") else os.path.splitext(asset.file_path)[0] + ".webp"
            if is_remote: await storage.upload(t_p, "/".join(new_p.split("/")[-4:]))
            elif old_p != new_p: os.rename(os.path.join("frontend/static", old_p.lstrip("/")), os.path.join("frontend/static", new_p.lstrip("/")))
            
            asset.file_path, asset.filename, asset.mime_type = new_p, os.path.basename(new_p), "image/webp"
            asset.file_size = os.path.getsize(t_p if is_remote else os.path.join("frontend/static", new_p.lstrip("/")))
            await repo.update(asset); await repo.session.commit()
            return asset
        except Exception as e: logger.error(f"[MediaEditor] Quick edit failed: {e}"); return None
        finally: 
            if os.path.exists(t_p): os.remove(t_p)
