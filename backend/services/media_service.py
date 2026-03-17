import logging
import os
import json
import re
from enum import Enum
from typing import List, Optional, Dict, Union, cast, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.storage_service import storage
from backend.schemas.media import (
    MediaUpdateMetadata,
    MimeTypeBreakdown,
    QuickEditParams,
    MediaListResult,
    MediaStatsResult,
    MediaAssetResponse
)

logger = logging.getLogger("media-service")

# --- Media Processing Constants & Helpers ---
class AspectRatio(float, Enum):
    SQUARE = 1.0          # 1:1
    BANNER = 16 / 9       # 16:9
    STORY = 9 / 16        # 9:16
    FEED = 4 / 5          # 4:5

PRESET_WIDTHS = 1080
DEFAULT_QUALITY = 90

def calculate_smart_crop(
    src_w: int,
    src_h: int,
    focal_x: float,
    focal_y: float,
    target_ratio: float
) -> Tuple[int, int, int, int]:
    """
    Tính toán toạ độ crop (left, top, right, bottom) dựa trên điểm tụ (focal point).
    focal_x, focal_y: giá trị chuẩn hoá từ 0.0 đến 1.0.
    """
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        crop_h = src_h
        crop_w = int(src_h * target_ratio)
    else:
        crop_w = src_w
        crop_h = int(src_w / target_ratio)

    center_x = focal_x * src_w
    center_y = focal_y * src_h

    left = center_x - crop_w / 2
    top = center_y - crop_h / 2
    right = left + crop_w
    bottom = top + crop_h

    if left < 0:
        shift_x = -left
        left += shift_x
        right += shift_x
    elif right > src_w:
        shift_x = right - src_w
        left -= shift_x
        right -= shift_x

    if top < 0:
        shift_y = -top
        top += shift_y
        bottom += shift_y
    elif bottom > src_h:
        shift_y = bottom - src_h
        top -= shift_y
        bottom -= shift_y

    return (int(left), int(top), int(right), int(bottom))
# --------------------------------------------

class MediaService:
    """
    AI-Professional Media Service (V65.0)
    Cung cấp logic nghiệp vụ cho FileManager riêng biệt. (Elite V2.2 Zero-Hydration)
    """

    async def list_assets(
        self,
        session: AsyncSession,
        campaign_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None,
        include_deleted: bool = False,
        owner_id: Optional[str] = None,
        tenant_id: str = "default"
    ) -> MediaListResult:
        """Liệt kê và lọc ảnh với hiệu năng cao (Zero-Hydration)."""
        from backend.services.ai_engine.encoder_singleton import get_shared_encoder
        from backend.schemas.media import MediaMetadata
        import numpy as np

        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

        # 1. RBAC Logic (V10.0 Elite Safety)
        if owner_id:
            conditions.append("(is_public = TRUE OR owner_id = :owner_id)")
            params["owner_id"] = owner_id
        else:
            conditions.append("is_public = TRUE")

        # 2. Trash Logic
        if not include_deleted:
            conditions.append("deleted_at IS NULL")
        else:
            conditions.append("deleted_at IS NOT NULL")

        if campaign_id:
            conditions.append("campaign_id = :campaign_id")
            params["campaign_id"] = campaign_id

        where_clause = " AND ".join(conditions)

        # 3. Execution
        if not search_query:
            # COUNT
            count_sql = text(f"SELECT COUNT(*) FROM media_registry WHERE {where_clause}")
            total = await session.scalar(count_sql, params) or 0

            # FETCH
            sql = text(f"""
                SELECT id, filename, file_path, file_size, mime_type, dimensions, blurhash,
                       alt_text, is_public, campaign_id, owner_id, created_at, media_metadata
                FROM media_registry
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            result = await session.execute(sql, params)
            rows = result.all()

            assets = [
                MediaAssetResponse(
                    id=str(r[0]),
                    filename=r[1],
                    file_path=r[2],
                    file_size=r[3],
                    mime_type=r[4],
                    dimensions=r[5],
                    blurhash=r[6],
                    alt_text=r[7],
                    is_public=bool(r[8]),
                    campaign_id=str(r[9]) if r[9] else None,
                    owner_id=str(r[10]) if r[10] else None,
                    created_at=r[11].isoformat() if r[11] else None,
                    media_metadata=MediaMetadata.model_validate(r[12] if isinstance(r[12], dict) else json.loads(r[12] or "{}"))
                )
                for r in rows
            ]
        else:
            # AI Semantic Search Logic (R03 Evolution) - Refactored for Zero-Hydration
            sql = text(f"""
                SELECT id, filename, file_path, file_size, mime_type, dimensions, blurhash,
                       alt_text, is_public, campaign_id, owner_id, created_at, media_metadata
                FROM media_registry
                WHERE {where_clause}
            """)
            result = await session.execute(sql, params)
            rows = result.all()
            total = len(rows)

            encoder = get_shared_encoder()
            if not encoder or not rows:
                # Fallback to basic keyword matching
                filtered_rows = [
                    r for r in rows
                    if search_query.lower() in r[1].lower() or (r[7] and search_query.lower() in r[7].lower())
                ]
                total = len(filtered_rows)
                rows_to_process = filtered_rows[offset : offset + limit]
            else:
                # 2. Encode query
                query_vec = cast(np.ndarray, list(encoder.embed([search_query]))[0])

                # 3. Calculate scores
                scored_rows = []
                for r in rows:
                    meta_raw = r[12]
                    meta_dict = meta_raw if isinstance(meta_raw, dict) else json.loads(meta_raw or "{}")
                    try:
                        asset_meta = MediaMetadata.model_validate(meta_dict)
                    except Exception:
                        asset_meta = MediaMetadata()

                    asset_vec_data = asset_meta.embedding

                    if not asset_vec_data:
                        # Elite V2.2: Generate text representation for embedding
                        ai_tags = asset_meta.ai_tags
                        ai_desc = asset_meta.ai_description or ""
                        text_to_embed = f"{r[1]} {r[7] or ''} {' '.join(ai_tags)} {ai_desc}"
                        asset_vec = cast(np.ndarray, list(encoder.embed([text_to_embed]))[0])
                        asset_vec_list = asset_vec.tolist()

                        # Surgical Background Update (Zero-Hydration)
                        asset_meta.embedding = asset_vec_list
                        upd_sql = text("UPDATE media_registry SET media_metadata = :meta WHERE id = :id")
                        await session.execute(upd_sql, {"meta": json.dumps(asset_meta.model_dump()), "id": r[0]})
                    else:
                        asset_vec = np.array(asset_vec_data)

                    # Cosine Similarity
                    score = np.dot(query_vec, asset_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(asset_vec))
                    scored_rows.append((score, r, asset_meta))

                # 4. Sort by score and paginate
                scored_rows.sort(key=lambda x: x[0], reverse=True)
                relevant_rows = [item for item in scored_rows if item[0] > 0.3]
                total = len(relevant_rows)
                rows_to_process_items = relevant_rows[offset : offset + limit]

                # Transform to final format
                assets = [
                    MediaAssetResponse(
                        id=str(r[0]),
                        filename=r[1],
                        file_path=r[2],
                        file_size=r[3],
                        mime_type=r[4],
                        dimensions=r[5],
                        blurhash=r[6],
                        alt_text=r[7],
                        is_public=bool(r[8]),
                        campaign_id=str(r[9]) if r[9] else None,
                        owner_id=str(r[10]) if r[10] else None,
                        created_at=r[11].isoformat() if r[11] else None,
                        media_metadata=meta_obj
                    )
                    for score, r, meta_obj in rows_to_process_items
                ]

                await session.commit()
                return MediaListResult(items=assets, total=total, limit=limit, offset=offset)

            # Fallback/Keyword processing
            assets = [
                MediaAssetResponse(
                    id=str(r[0]),
                    filename=r[1],
                    file_path=r[2],
                    file_size=r[3],
                    mime_type=r[4],
                    dimensions=r[5],
                    blurhash=r[6],
                    alt_text=r[7],
                    is_public=bool(r[8]),
                    campaign_id=str(r[9]) if r[9] else None,
                    owner_id=str(r[10]) if r[10] else None,
                    created_at=r[11].isoformat() if r[11] else None,
                    media_metadata=MediaMetadata.model_validate(r[12] if isinstance(r[12], dict) else json.loads(r[12] or "{}"))
                )
                for r in rows_to_process
            ]

        return MediaListResult(
            items=assets,
            total=total,
            limit=limit,
            offset=offset
        )


    async def get_asset(
        self,
        session: AsyncSession,
        asset_id: str,
        owner_id: Optional[str] = None,
        tenant_id: str = "default"
    ) -> Optional[MediaAssetResponse]:
        """Lấy thông tin chi tiết một tài nguyên (Zero-Hydration)."""
        from backend.schemas.media import MediaMetadata, MediaAssetResponse
        import json

        sql = text("""
            SELECT id, filename, file_path, file_size, mime_type, dimensions, blurhash,
                   alt_text, is_public, campaign_id, owner_id, created_at, media_metadata
            FROM media_registry
            WHERE id = :id AND tenant_id = :tenant_id AND deleted_at IS NULL
        """)

        result = await session.execute(sql, {"id": asset_id, "tenant_id": tenant_id})
        r = result.first()
        if not r:
            return None

        # RBAC Check (V10.0 Elite)
        r_is_public = bool(r[8])
        r_owner_id = str(r[10]) if r[10] else None

        if not r_is_public and owner_id and r_owner_id and r_owner_id != owner_id:
            logger.warning(f"[RBAC] Access denied to asset {asset_id} for user {owner_id}")
            return None

        return MediaAssetResponse(
            id=str(r[0]),
            filename=r[1],
            file_path=r[2],
            file_size=r[3],
            mime_type=r[4],
            dimensions=r[5],
            blurhash=r[6],
            alt_text=r[7],
            is_public=r_is_public,
            campaign_id=str(r[9]) if r[9] else None,
            owner_id=r_owner_id,
            created_at=r[11].isoformat() if r[11] else None,
            media_metadata=MediaMetadata.model_validate(r[12] if isinstance(r[12], dict) else json.loads(r[12] or "{}"))
        )


    async def update_metadata(
        self,
        session: AsyncSession,
        asset_id: str,
        metadata: MediaUpdateMetadata,
        owner_id: Optional[str] = None
    ) -> Optional[Dict[str, object]]:
        """Cập nhật metadata (alt_text, AI tags...) cho ảnh (Zero-Hydration)."""
        from backend.schemas.media import MediaMetadata

        # 1. Fetch current state via scalar
        sql = text("SELECT id, owner_id, alt_text, is_public, media_metadata FROM media_registry WHERE id = :id")
        res = await session.execute(sql, {"id": asset_id})
        r = res.first()
        if not r:
            return None

        # RBAC Check (V10.0 Elite)
        r_owner_id = str(r[1]) if r[1] else None
        if owner_id and r_owner_id and r_owner_id != owner_id:
            logger.warning(f"[RBAC] Unauthorized metadata update attempt on {asset_id} by {owner_id}")
            return None

        set_clauses = ["updated_at = NOW()"]
        params = {"id": asset_id}

        if metadata.alt_text is not None:
            set_clauses.append("alt_text = :alt")
            params["alt"] = metadata.alt_text

        if metadata.is_public is not None:
            set_clauses.append("is_public = :public")
            params["public"] = metadata.is_public

        if metadata.media_metadata is not None:
            current_meta_raw = r[4]
            current_meta_dict = current_meta_raw if isinstance(current_meta_raw, dict) else json.loads(current_meta_raw or "{}")
            try:
                current_meta = MediaMetadata.model_validate(current_meta_dict)
            except Exception:
                current_meta = MediaMetadata()

            # Merge fields
            update_dict = metadata.media_metadata.model_dump(exclude_unset=True)
            new_meta_dict = {**current_meta.model_dump(), **update_dict}

            set_clauses.append("media_metadata = :meta")
            params["meta"] = json.dumps(new_meta_dict)

        if len(set_clauses) > 1:
            upd_sql = text(f"UPDATE media_registry SET {', '.join(set_clauses)} WHERE id = :id")
            await session.execute(upd_sql, params)
            await session.commit()

        # Return updated state (simplified dict for service consumption or re-fetch if needed)
        return {"id": asset_id, "status": "updated"}

    async def delete_asset(self, session: AsyncSession, asset_id: str, permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """
        Xóa tài nguyên (Zero-Hydration).
        Mặc định là Soft-delete (V10.0 Trash Bin).
        """
        try:
            sql = text("SELECT id, owner_id, file_path FROM media_registry WHERE id = :id")
            res = await session.execute(sql, {"id": asset_id})
            r = res.first()
            if not r:
                return False

            # RBAC Check (V10.0 Elite)
            r_owner_id = str(r[1]) if r[1] else None
            if owner_id and r_owner_id and r_owner_id != owner_id:
                logger.warning(f"[RBAC] Unauthorized delete attempt on {asset_id} by {owner_id}")
                return False

            if permanent:
                # Xóa file vật lý
                await storage.delete(r[2])
                del_sql = text("DELETE FROM media_registry WHERE id = :id")
                await session.execute(del_sql, {"id": asset_id})
            else:
                # Soft-delete
                upd_sql = text("UPDATE media_registry SET deleted_at = NOW(), updated_at = NOW() WHERE id = :id")
                await session.execute(upd_sql, {"id": asset_id})

            await session.commit()
            return True
        except Exception as e:
            logger.error(f"[MediaService] Failed to delete asset {asset_id}: {e}")
            return False

    async def restore_asset(self, session: AsyncSession, asset_id: str, owner_id: Optional[str] = None) -> bool:
        """Khôi phục tài nguyên từ Thùng rác (Zero-Hydration)."""
        try:
            sql = text("SELECT id, owner_id FROM media_registry WHERE id = :id")
            res = await session.execute(sql, {"id": asset_id})
            r = res.first()
            if not r:
                return False

            # RBAC Check
            r_owner_id = str(r[1]) if r[1] else None
            if owner_id and r_owner_id and r_owner_id != owner_id:
                logger.warning(f"[RBAC] Unauthorized restore attempt on {asset_id} by {owner_id}")
                return False

            upd_sql = text("UPDATE media_registry SET deleted_at = NULL, updated_at = NOW() WHERE id = :id")
            await session.execute(upd_sql, {"id": asset_id})
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"[MediaService] Failed to restore asset {asset_id}: {e}")
            return False

    async def bulk_delete(self, session: AsyncSession, ids: List[str], permanent: bool = False, owner_id: Optional[str] = None) -> bool:
        """Xóa hàng loạt tài nguyên (Zero-Hydration)."""
        if not ids:
            return True
        try:
            # RBAC: Chỉ chọn những ảnh mình sở hữu
            conditions = ["id = ANY(:ids)"]
            params = {"ids": ids}
            if owner_id:
                conditions.append("owner_id = :owner_id")
                params["owner_id"] = owner_id

            sql = text(f"SELECT id, file_path FROM media_registry WHERE {' AND '.join(conditions)}")
            res = await session.execute(sql, params)
            rows = res.all()
            if not rows:
                return True

            target_ids = [r[0] for r in rows]

            if permanent:
                for r in rows:
                    await storage.delete(r[1])
                del_sql = text("DELETE FROM media_registry WHERE id = ANY(:t_ids)")
                await session.execute(del_sql, {"t_ids": target_ids})
            else:
                upd_sql = text("UPDATE media_registry SET deleted_at = NOW(), updated_at = NOW() WHERE id = ANY(:t_ids)")
                await session.execute(upd_sql, {"t_ids": target_ids})

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
        """Tạo file ZIP hàng loạt tài nguyên (Zero-Hydration)."""
        import os
        import zipfile
        from datetime import datetime

        if not ids:
            return None

        try:
            conditions = ["id = ANY(:ids)"]
            params = {"ids": ids}

            # RBAC Check (V10.0 Elite)
            if owner_id:
                conditions.append("(is_public = TRUE OR owner_id = :owner_id)")
                params["owner_id"] = owner_id
            else:
                conditions.append("is_public = TRUE")

            sql = text(f"SELECT filename, file_path FROM media_registry WHERE {' AND '.join(conditions)}")
            result = await session.execute(sql, params)
            assets = result.all()

            if not assets:
                return None

            # Tạo thư mục download tạm
            download_dir = os.path.join("frontend/static/v65_assets/downloads")
            os.makedirs(download_dir, exist_ok=True)

            zip_filename = f"bulk_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join(download_dir, zip_filename)

            def make_zip():
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for filename, file_path in assets:
                        rel_path = file_path.lstrip("/")
                        full_path = os.path.join("frontend/static", rel_path)
                        if os.path.exists(full_path):
                            # Thêm vào zip với tên gốc
                            zipf.write(full_path, arcname=filename)
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
    ) -> Optional[Dict[str, object]]:
        """Thực hiện xử lý nhanh (Xoay/Lật/Crop/Watermark) - Zero-Hydration."""
        import os
        from PIL import Image
        import uuid

        # 1. Fetch via scalar
        sql = text("SELECT id, owner_id, file_path, filename, media_metadata FROM media_registry WHERE id = :id")
        res = await session.execute(sql, {"id": asset_id})
        r = res.first()

        if not r:
            if source_url:
                logger.info(f"[QuickEdit] Asset {asset_id} not found, registering from source_url: {source_url}")
                asset_data = await self.fetch_remote_asset(session, source_url, owner_id=owner_id)
                if not asset_data:
                    return None
                asset_id = str(asset_data["id"])
                file_path = str(asset_data["file_path"])
                filename = str(asset_data["filename"])
                media_metadata = asset_data.get("media_metadata", {})
                r_owner_id = asset_data.get("owner_id")
            else:
                return None
        else:
            asset_id = str(r[0])
            r_owner_id = str(r[1]) if r[1] else None
            file_path = r[2]
            filename = r[3]
            media_metadata = r[4] if isinstance(r[4], dict) else json.loads(r[4] or "{}")

        if owner_id and r_owner_id and r_owner_id != owner_id:
            logger.warning(f"[RBAC] Unauthorized quick-edit attempt on {asset_id} by {owner_id}")
            return None

        is_remote = file_path.startswith("http")
        temp_path = f"/tmp/edit_{uuid.uuid4()}"
        source_path = temp_path if is_remote else os.path.join("frontend/static", file_path.lstrip("/"))

        try:
            if is_remote:
                from backend.utils.http_client import SharedHttpClient
                client = await SharedHttpClient.get_client()
                resp = await client.get(file_path)
                resp.raise_for_status()
                with open(temp_path, "wb") as f:
                    f.write(resp.content)

            def process():
                with Image.open(source_path) as img:
                    if img.mode != 'RGBA' and action in ["rotate_left", "rotate_right", "flip_h", "flip_v", "watermark"]:
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
                        if params.preset:
                            preset_name = params.preset.upper()
                            target_ratio = AspectRatio[preset_name].value if preset_name in AspectRatio.__members__ else AspectRatio.SQUARE.value
                            box = calculate_smart_crop(img.width, img.height, 0.5, 0.5, target_ratio)
                            img = img.crop(box)
                        else:
                            p_dict = params.model_dump()
                            x, y, w, h = p_dict.get('x', 0), p_dict.get('y', 0), p_dict.get('w', img.width), p_dict.get('h', img.height)
                            img = img.crop((x, y, x + (w or img.width), y + (h or img.height)))
                    elif action == "smart_crop" and params:
                        preset_name = (params.preset or 'square').upper()
                        target_ratio = AspectRatio[preset_name].value if preset_name in AspectRatio.__members__ else AspectRatio.SQUARE.value
                        f_x, f_y = 0.5, 0.5
                        if media_metadata:
                            fp = media_metadata.get("focal_point", {})
                            if isinstance(fp, dict):
                                f_x, f_y = fp.get("x", 0.5), fp.get("y", 0.5)
                        box = calculate_smart_crop(img.width, img.height, f_x, f_y, target_ratio)
                        img = img.crop(box)
                    elif action == "watermark":
                        logo_path = "frontend/static/logo_watermark.png"
                        if os.path.exists(logo_path):
                            with Image.open(logo_path) as logo:
                                logo_w = int(img.width * 0.15)
                                logo_h = int(logo.height * (logo_w / logo.width))
                                logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                                position = (img.width - logo_w - 20, img.height - logo_h - 20)
                                img.paste(logo, position, logo if logo.mode == 'RGBA' else None)
                        else:
                            from PIL import ImageDraw, ImageFont
                            draw = ImageDraw.Draw(img)
                            text_wm = "FAST-PLATFORM AI"
                            f_size = max(20, int(img.height * 0.04))
                            try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", f_size)
                            except: font = ImageFont.load_default()
                            bbox = draw.textbbox((0, 0), text_wm, font=font)
                            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                            pos = (img.width - tw - 30, img.height - th - 30)
                            draw.text((pos[0]+2, pos[1]+2), text_wm, font=font, fill=(0,0,0,100))
                            draw.text(pos, text_wm, font=font, fill=(255,255,255,160))

                    save_path = temp_path if is_remote else source_path
                    if not (is_remote or source_path.endswith((".webp", ".png"))):
                        img = img.convert('RGB')
                    img.save(save_path, "WEBP", quality=DEFAULT_QUALITY, optimize=True)
                    return f"{img.width}x{img.height}"

            import asyncio
            new_dims = await asyncio.to_thread(process)

            # 4. Update Path/Extension
            old_file_path = file_path
            new_file_path = old_file_path if old_file_path.endswith(".webp") else os.path.splitext(old_file_path)[0] + ".webp"
            new_filename = filename if filename.endswith(".webp") else os.path.splitext(filename)[0] + ".webp"

            if is_remote:
                remote_path_key = "/".join(new_file_path.split("/")[-4:])
                await storage.upload(temp_path, remote_path_key)
            else:
                if new_file_path != old_file_path:
                    full_new = os.path.join("frontend/static", new_file_path.lstrip("/"))
                    if os.path.exists(source_path) and source_path != full_new:
                        if os.path.exists(full_new): os.remove(full_new)
                        os.rename(source_path, full_new)

            new_size = os.path.getsize(temp_path) if is_remote else os.path.getsize(os.path.join("frontend/static", new_file_path.lstrip("/")))

            await session.execute(text("""
                UPDATE media_registry
                SET dimensions = :dims, file_path = :path, filename = :name,
                    mime_type = 'image/webp', file_size = :size, updated_at = NOW()
                WHERE id = :id
            """), {"dims": new_dims, "path": new_file_path, "name": new_filename, "size": new_size, "id": asset_id})
            await session.commit()

            # Cleanup
            cache_dir = os.path.join("frontend/static/v65_assets/cache")
            if os.path.exists(cache_dir):
                target_f = os.path.basename(new_file_path.split("?")[0])
                for f in os.listdir(cache_dir):
                    if target_f in f:
                        try: os.remove(os.path.join(cache_dir, f))
                        except: pass

            return {"id": asset_id, "file_path": new_file_path, "dimensions": new_dims, "filename": new_filename, "file_size": new_size, "mime_type": "image/webp"}

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

    async def get_stats(self, session: AsyncSession, owner_id: Optional[str] = None, tenant_id: str = "default") -> MediaStatsResult:
        """Thống kê kho tài nguyên (Zero-Hydration)."""
        conditions = ["tenant_id = :tenant_id", "deleted_at IS NULL"]
        params = {"tenant_id": tenant_id}

        if owner_id:
            conditions.append("(is_public = TRUE OR owner_id = :owner_id)")
            params["owner_id"] = owner_id
        else:
            conditions.append("is_public = TRUE")

        where_clause = " AND ".join(conditions)

        # 1. Tổng quan
        sql = text(f"SELECT COUNT(id), SUM(file_size) FROM media_registry WHERE {where_clause}")
        res = await session.execute(sql, params)
        row = res.first()
        total_count = int(row[0] or 0) if row else 0
        total_size = int(row[1] or 0) if row else 0

        # 2. Phân loại theo MIME type
        mime_sql = text(f"""
            SELECT mime_type, COUNT(id), SUM(file_size)
            FROM media_registry
            WHERE {where_clause}
            GROUP BY mime_type
        """)
        mime_res = await session.execute(mime_sql, params)

        breakdown: List[MimeTypeBreakdown] = [
            MimeTypeBreakdown(
                type=str(r[0]).split("/")[-1].upper(),
                count=int(r[1]),
                size=int(r[2] or 0)
            )
            for r in mime_res.all()
        ]

        return MediaStatsResult(
            total_count=total_count,
            total_size=total_size,
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
        owner_id: Optional[str] = None,
        tenant_id: str = "default"
    ) -> Optional[Dict[str, object]]:
        """Xử lý upload file trực tiếp (Zero-Hydration)."""
        import uuid
        import os
        from PIL import Image
        from io import BytesIO
        from datetime import datetime

        try:
            asset_id = str(uuid.uuid4())
            folder = datetime.now().strftime("%Y/%m")

            # 1. Xử lý ảnh
            def process_image() -> tuple[bytes, str]:
                with Image.open(BytesIO(file_content)) as img:
                    dims = f"{img.width}x{img.height}"
                    buffer = BytesIO()
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

            temp_path = f"/tmp/{asset_id}.webp"
            with open(temp_path, "wb") as f:
                f.write(webp_content)

            try:
                final_url = await storage.upload(temp_path, remote_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            # 3. Đăng ký vào Database (Scalar Insert)
            sql = text("""
                INSERT INTO media_registry (
                    id, filename, file_path, file_size, mime_type, dimensions,
                    campaign_id, owner_id, provider, is_public, tenant_id,
                    created_at, updated_at
                ) VALUES (
                    :id, :name, :path, :size, :mime, :dims,
                    :camp_id, :owner_id, :provider, TRUE, :tenant_id,
                    NOW(), NOW()
                )
            """)
            await session.execute(sql, {
                "id": asset_id, "name": final_filename, "path": final_url,
                "size": len(webp_content), "mime": "image/webp", "dims": dims,
                "camp_id": campaign_id, "owner_id": owner_id,
                "provider": str(os.getenv("STORAGE_PROVIDER", "local")),
                "tenant_id": tenant_id
            })
            await session.commit()

            # 4. Trigger AI Analysis
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {
                "id": asset_id,
                "file_path": final_url,
                "campaign_id": campaign_id
            })

            return {"id": asset_id, "file_path": final_url, "filename": final_filename}

        except Exception as e:
            logger.error(f"[MediaService] Direct upload failed: {e}")
            return None

    async def fetch_remote_asset(
        self,
        session: AsyncSession,
        url: str,
        campaign_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        tenant_id: str = "default"
    ) -> Optional[Dict[str, object]]:
        """Tải ảnh từ URL và lưu vào hệ thống (V9.0 Remote Fetch - Zero-Hydration)."""
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

            # 4. Đăng ký vào Database (Zero-Hydration)
            valid_campaign_id = None
            if campaign_id:
                stmt = text("SELECT id FROM content_campaigns WHERE id = :id LIMIT 1")
                res = await session.execute(stmt, {"id": campaign_id})
                if res.scalar():
                    valid_campaign_id = campaign_id
                else:
                    logger.warning(f"[MediaService] Orphaned fetch: Campaign {campaign_id} not found.")

            valid_owner_id = None
            if owner_id:
                stmt = text("SELECT id FROM users WHERE id = :id LIMIT 1")
                res = await session.execute(stmt, {"id": owner_id})
                if res.scalar():
                    valid_owner_id = owner_id
                else:
                    logger.warning(f"[MediaService] Orphaned fetch: Owner {owner_id} not found.")

            final_filename = filename if filename.endswith(".webp") else filename + ".webp"
            provider = str(os.getenv("STORAGE_PROVIDER", "local"))

            await session.execute(
                text("""
                    INSERT INTO media_registry (
                        id, filename, file_path, file_size, mime_type, dimensions,
                        campaign_id, owner_id, provider, tenant_id, created_at, updated_at
                    ) VALUES (
                        :id, :filename, :path, :size, 'image/webp', :dims,
                        :campaign_id, :owner_id, :provider, :tenant_id, NOW(), NOW()
                    )
                """),
                {
                    "id": asset_id,
                    "filename": final_filename,
                    "path": final_url,
                    "size": actual_size,
                    "dims": dims,
                    "campaign_id": valid_campaign_id,
                    "owner_id": valid_owner_id,
                    "provider": provider,
                    "tenant_id": tenant_id
                }
            )
            await session.commit()

            # 5. Trigger AI Analysis (Async)
            from backend.services.event_bus import event_bus
            await event_bus.emit("MEDIA_UPLOADED", {
                "id": asset_id,
                "file_path": final_url,
                "campaign_id": valid_campaign_id
            })

            return {
                "id": asset_id,
                "filename": final_filename,
                "file_path": final_url,
                "file_size": actual_size,
                "mime_type": "image/webp",
                "dimensions": dims
            }

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

        # 3. Dọn dẹp Trash Bin (V10.0: Xóa vĩnh viễn sau 30 ngày - Zero-Hydration)
        try:
            from backend.database import alchemy_config
            from datetime import datetime, timezone, timedelta

            cutoff = datetime.now(timezone.utc) - timedelta(days=30)

            async with alchemy_config.create_session_maker()() as session:
                # 3.1 Fetch files to delete from storage
                stmt = text("SELECT file_path FROM media_registry WHERE deleted_at IS NOT NULL AND deleted_at < :cutoff")
                result = await session.execute(stmt, {"cutoff": cutoff})
                expired_paths = [r[0] for r in result]

                for path in expired_paths:
                    try:
                        await storage.delete(path)
                    except Exception as e:
                        logger.error(f"[MediaService] Storage delete failed for {path}: {e}")

                # 3.2 Hard delete from DB
                del_stmt = text("DELETE FROM media_registry WHERE deleted_at IS NOT NULL AND deleted_at < :cutoff")
                res = await session.execute(del_stmt, {"cutoff": cutoff})
                stats["trash_purged"] = res.rowcount

                if stats["trash_purged"] > 0:
                    await session.commit()
        except Exception as e:
            logger.error(f"[MediaService] Trash purge failed: {e}")

        if stats["zip_deleted"] > 0 or stats["cache_deleted"] > 0 or stats["trash_purged"] > 0:
            logger.info(f"[MediaService] Cleanup complete: {stats}")

        return stats


media_service = MediaService()
