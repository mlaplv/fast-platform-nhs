import logging
import os
import zipfile
from datetime import datetime
from typing import Optional, List, Dict
from PIL import Image
from sqlalchemy import select, or_
from backend.database.models import MediaRegistry
from backend.database.repositories import MediaRegistryRepository

logger = logging.getLogger("media-formatters")

class MediaFormattersMixin:
    async def get_thumbnail(self, asset_path: str, width: int = 300, quality: int = 75) -> Optional[str]:
        """Tạo và trả về đường dẫn Thumbnail (Dynamic Resizing)."""
        is_remote = asset_path.startswith("http")
        fname = os.path.basename(asset_path.split("?")[0])
        cache_dir = "frontend/static/v65_assets/cache"; os.makedirs(cache_dir, exist_ok=True)
        c_fname = f"t_{width}_{quality}_{fname if fname.endswith('.webp') else fname + '.webp'}"
        c_path = os.path.join(cache_dir, c_fname)
        if os.path.exists(c_path): return f"/v65_assets/cache/{c_fname}"

        try:
            async def process(source):
                def _sync():
                    from io import BytesIO
                    with Image.open(BytesIO(source)) as img:
                        thumb = img.resize((width, int(img.height * (width / img.width))), Image.Resampling.LANCZOS)
                        thumb.save(c_path, "WEBP", quality=quality, optimize=True)
                    return f"/v65_assets/cache/{c_fname}"
                import asyncio; return await asyncio.to_thread(_sync)

            if is_remote:
                from backend.utils.http_client import SharedHttpClient
                return await process((await (await SharedHttpClient.get_client()).get(asset_path, timeout=10.0)).content)
            else:
                p = os.path.join("frontend/static", asset_path.lstrip("/")); 
                if not os.path.exists(p): return asset_path
                with open(p, "rb") as f: return await process(f.read())
        except Exception as e: logger.error(f"[MediaFormatters] Thumb failed: {e}"); return asset_path

    async def create_bulk_zip(self, repo: MediaRegistryRepository, ids: List[str], owner_id: Optional[str] = None) -> Optional[str]:
        """Tạo file ZIP hàng loạt tài nguyên."""
        stmt = select(MediaRegistry).where(MediaRegistry.id.in_(ids))
        if owner_id: stmt = stmt.where(or_(MediaRegistry.is_public == True, MediaRegistry.owner_id == owner_id))
        else: stmt = stmt.where(MediaRegistry.is_public == True)
        assets = (await repo.session.execute(stmt)).scalars().all()
        if not assets: return None
        
        d_dir = "frontend/static/v65_assets/downloads"; os.makedirs(d_dir, exist_ok=True)
        z_fname = f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"; z_path = os.path.join(d_dir, z_fname)
        def make():
            with zipfile.ZipFile(z_path, 'w') as zf:
                for a in assets:
                    p = os.path.join("frontend/static", a.file_path.lstrip("/"))
                    if os.path.exists(p): zf.write(p, arcname=a.filename)
            return f"/v65_assets/downloads/{z_fname}"
        import asyncio; return await asyncio.to_thread(make)

    async def cleanup_temp_files(self) -> Dict[str, int]:
        """Dọn dẹp file tạm (ZIP > 24h, Cache > 7 ngày)."""
        import time; stats = {"zip": 0, "cache": 0, "trash": 0}; now = time.time()
        for d, t, k in [("frontend/static/v65_assets/downloads", 86400, "zip"), ("frontend/static/v65_assets/cache", 604800, "cache")]:
            if os.path.exists(d):
                for f in os.listdir(d):
                    p = os.path.join(d, f)
                    if os.path.isfile(p) and now - os.path.getmtime(p) > t:
                        try: os.remove(p); stats[k] += 1
                        except: pass
        try:
            from backend.database import alchemy_config
            from datetime import datetime, timezone, timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            async with alchemy_config.create_session_maker()() as session:
                assets = (await session.execute(select(MediaRegistry).where(MediaRegistry.deleted_at != None, MediaRegistry.deleted_at < cutoff))).scalars().all()
                for a in assets:
                    from backend.services.storage.manager import storage
                    await storage.delete(a.file_path); await session.delete(a); stats["trash"] += 1
                if stats["trash"]: await session.commit()
        except Exception as e: logger.error(f"[MediaFormatters] Cleanup failed: {e}")
        return stats
