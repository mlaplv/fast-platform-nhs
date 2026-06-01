import logging
import os
from typing import List, Optional, cast
from sqlalchemy import select, func, or_
import numpy as np
from backend.database.models import MediaRegistry
from backend.database.repositories import MediaRegistryRepository
from backend.services.media.schemas import (
    MediaListResult,
    MediaStatsResult,
    MediaAssetResponse,
    MediaMetadata,
    MimeTypeBreakdown
)

logger = logging.getLogger("media-listing")

class MediaListingMixin:
    async def list_assets(
        self,
        repo: MediaRegistryRepository,
        campaign_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None,
        include_deleted: bool = False,
        owner_id: Optional[dict] = None,
        is_linked: Optional[bool] = None,
        linked_post_id: Optional[str] = None,
        linked_post_type: Optional[str] = None
    ) -> MediaListResult:
        """Liệt kê và lọc ảnh với hiệu năng cao (Hỗ trợ AI Semantic Search)."""
        from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
        
        stmt = select(MediaRegistry)
        
        # Elite Security: Completely hide client isolated uploads from general admin / listing views
        stmt = stmt.where(~MediaRegistry.file_path.contains("client_uploads/"))
        stmt = stmt.where(~MediaRegistry.file_path.contains("avatars/"))
        
        is_admin = False
        user_id = None
        
        if isinstance(owner_id, dict):
            roles = owner_id.get("roles", [])
            is_admin = any(r in ["ADMIN", "SUPER_ADMIN", "OWNER"] for r in roles)
            user_id = owner_id.get("id") or owner_id.get("sub")

        if not is_admin:
            if user_id:
                stmt = stmt.where(or_(MediaRegistry.is_public == True, MediaRegistry.owner_id == user_id))
            else:
                stmt = stmt.where(MediaRegistry.is_public == True)

        if not include_deleted:
            stmt = stmt.where(MediaRegistry.deleted_at == None)
        else:
            stmt = stmt.where(MediaRegistry.deleted_at != None)

        if campaign_id:
            stmt = stmt.where(MediaRegistry.campaign_id == campaign_id)
        if is_linked is not None:
            stmt = stmt.where(MediaRegistry.is_linked == is_linked)
        if linked_post_id:
            # Legacy filter - only for 1-1 backwards compatibility if needed
            stmt = stmt.where(MediaRegistry.linked_post_id == linked_post_id)
        if linked_post_type:
            stmt = stmt.where(MediaRegistry.linked_post_type == linked_post_type)

        if not search_query:
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = (await repo.session.execute(count_stmt)).scalar_one()
            stmt = stmt.order_by(MediaRegistry.updated_at.desc()).limit(limit).offset(offset)
            orm_assets = (await repo.session.execute(stmt)).scalars().all()
            assets = [MediaAssetResponse.model_validate(a) for a in orm_assets]
        else:
            all_assets = list((await repo.session.execute(stmt)).scalars().all())
            total = len(all_assets)
            encoder = get_shared_encoder()
            if not encoder or not all_assets:
                assets = [a for a in all_assets if search_query.lower() in a.filename.lower() or (a.alt_text and search_query.lower() in a.alt_text.lower())]
                assets = assets[offset : offset + limit]
                assets = [MediaAssetResponse.model_validate(a) for a in assets]
            else:
                query_vec = cast(np.ndarray, list(encoder.embed([search_query]))[0])
                scored_assets = []
                for asset in all_assets:
                    try: meta = MediaMetadata.model_validate(asset.media_metadata or {})
                    except Exception: meta = MediaMetadata()
                    
                    if not meta.embedding:
                        text = f"{asset.filename} {asset.alt_text or ''} {' '.join(meta.ai_tags)} {meta.ai_description or ''}"
                        meta.embedding = cast(np.ndarray, list(encoder.embed([text]))[0]).tolist()
                        asset.media_metadata = meta.model_dump(); repo.session.add(asset)
                    
                    asset_vec = np.array(meta.embedding)
                    score = np.dot(query_vec, asset_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(asset_vec))
                    scored_assets.append((score, asset))
                
                scored_assets.sort(key=lambda x: x[0], reverse=True)
                assets = [MediaAssetResponse.model_validate(a) for score, a in scored_assets if score > 0.3][offset : offset + limit]
                await repo.session.commit()

        return MediaListResult(items=assets, total=total, limit=limit, offset=offset)

    async def get_stats(self, repo: MediaRegistryRepository, owner_id: Optional[dict] = None) -> MediaStatsResult:
        """Thống kê kho tài nguyên (V9.0 Analytics)."""
        user_id = None
        if isinstance(owner_id, dict): user_id = owner_id.get("id") or owner_id.get("sub")

        def apply_rbac(s):
            # Elite Security: Exclude client isolated uploads from stats calculations
            s = s.where(~MediaRegistry.file_path.contains("client_uploads/"))
            s = s.where(~MediaRegistry.file_path.contains("avatars/"))
            if user_id: return s.where(or_(MediaRegistry.is_public == True, MediaRegistry.owner_id == user_id))
            return s.where(MediaRegistry.is_public == True)

        stmt = apply_rbac(select(func.count(MediaRegistry.id), func.sum(MediaRegistry.file_size)).where(MediaRegistry.deleted_at == None))
        row = (await repo.session.execute(stmt)).one()
        
        trash_stmt = apply_rbac(select(func.count(MediaRegistry.id)).where(MediaRegistry.deleted_at != None))
        total_trash = (await repo.session.execute(trash_stmt)).scalar_one()

        mime_stmt = apply_rbac(select(MediaRegistry.mime_type, func.count(MediaRegistry.id), func.sum(MediaRegistry.file_size)).where(MediaRegistry.deleted_at == None).group_by(MediaRegistry.mime_type))
        mime_res = await repo.session.execute(mime_stmt)

        breakdown = [MimeTypeBreakdown(type=str(r[0]).split("/")[-1].upper(), count=int(r[1]), size=int(r[2] or 0)) for r in mime_res.all()]
        return MediaStatsResult(total_count=int(row[0] or 0), total_size=int(row[1] or 0), total_trash_count=int(total_trash or 0), breakdown=breakdown, storage_provider=str(os.getenv("STORAGE_PROVIDER", "local")))
