import os
import re
import httpx
import gc
import asyncio
import logging
import hashlib
from PIL import Image
from io import BytesIO
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, timezone

import uuid
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.campaign_service import campaign_service
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal

from backend.services.xohi.creative_studio.operatives.media_analyst import MediaAnalyst

logger = logging.getLogger("api-gateway")

class MediaCompressor:
    """
    Step 6: Media Localization & Optimization.
    Standards: SvelteKit 5 + SQLAlchemy 2.0 + Litestar.
    R115: Zero External Links in Final Production Content.
    """
    def __init__(self, upload_dir: str = "frontend/static/v65_assets") -> None:
        self.upload_dir: str = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        # R106: Semaphore-based concurrency to protect 2GB RAM limits.
        # Phase 76: Enforce serial processing for heavy media tasks
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(1)
        self.analyst = MediaAnalyst()

    async def execute(self, campaign_id: str, session: AsyncSession, **kwargs: object) -> AgentResponse:
        """Entry point for standard agentic flow (Elite V2.2 Zero-Hydration)."""
        campaign = await campaign_service.get_campaign(session, campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found.", data={})

        # Step 1: Localize standard assets (images from Step 2)
        original_assets: List[str] = campaign_service.get_gold_val(campaign, "original_remote_assets", list(campaign.get("assets_data") or []))
        local_assets: List[str] = await self.localize_assets(campaign, session)

        # Step 2: Localize Avatar (Gold Metadata)
        gold: Dict[str, Any] = dict(campaign.get("gold_metadata") or {})
        remote_avatar: Optional[str] = gold.get("avatar")

        if remote_avatar and isinstance(remote_avatar, str) and remote_avatar.startswith("http"):
            async with httpx.AsyncClient(follow_redirects=True) as client:
                local_avatar = await self._download_and_save(client, remote_avatar, str(campaign["id"]), "avatar", session)
                if local_avatar:
                    gold["avatar"] = local_avatar
                    # Rule R1.5: Surgical Update for metadata
                    await campaign_service.update_campaign(session, campaign_id, {"gold_metadata": gold})

        # Step 3: Wrap Draft Content and apply asset replacement
        final_html: str = self.wrap_html(campaign.get("draft_content") or "", local_assets, original_assets)

        # Step 4: Final Surgical Scan for manual/rogue external links
        final_html = await self._localize_remaining_html_images(final_html, str(campaign["id"]), session)

        # Final persistence via CampaignService
        await campaign_service.update_campaign(session, campaign_id, {
            "final_html": final_html,
            "assets_data": local_assets
        })

        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message="Media localized and verified for production.",
            data={"assets": local_assets, "final_html": final_html}
        )

    async def localize_assets(self, campaign: Dict[str, Any], session: Optional[AsyncSession] = None) -> List[str]:
        """Downloads and processes all assets defined in assets_data."""
        local_paths: List[str] = []
        assets_data = campaign.get("assets_data") or []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for i, url in enumerate(assets_data):
                # Handle cases where url might be a dict (old format support)
                if isinstance(url, dict):
                    url = url.get("file_path", "")

                # Phase 73: Fast Path for already localized assets
                if url.startswith("/") or url.startswith("static"):
                    # Normalize paths (Remove /static prefix if present)
                    norm_path = url if url.startswith("/") else f"/{url}"
                    if norm_path.startswith("/static/v65_assets/"):
                        norm_path = norm_path.replace("/static/v65_assets/", "/v65_assets/")
                    local_paths.append(norm_path)
                    continue

                async with self.semaphore:
                    local_path = await self._download_and_save(client, url, str(campaign["id"]), i, session)
                    local_paths.append(local_path if local_path else "/v65_assets/placeholder.webp")

        return local_paths

    async def _download_and_save(self, client: httpx.AsyncClient, url: str, campaign_id: str, suffix: Union[int, str], session: Optional[AsyncSession] = None) -> Optional[str]:
        """Robust download and WebP conversion flow."""
        if not url.startswith("http"):
            return url

        try:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()

            buffer = BytesIO(response.content)
            try:
                # Offload blocking Pillow logic to thread pool
                dims = await asyncio.to_thread(self._save_webp, buffer, campaign_id, suffix)
                local_path = f"/v65_assets/{campaign_id}_{suffix}.webp"

                # --- AI PROFESSIONAL REGISTRY INTEGRATION (V65.0) ---
                if session:
                    full_path = os.path.join(self.upload_dir, f"{campaign_id}_{suffix}.webp")
                    file_size = os.path.getsize(full_path)
                    new_asset_id = str(uuid.uuid4())

                    # Rule R1.5: Surgical INSERT via Raw SQL (Zero-Hydration)
                    sql = text("""
                        INSERT INTO media_registry (
                            id, filename, file_path, file_size, mime_type, dimensions,
                            campaign_id, media_metadata, created_at, updated_at
                        ) VALUES (
                            :id, :filename, :file_path, :file_size, :mime_type, :dimensions,
                            :campaign_id, :media_metadata, NOW(), NOW()
                        )
                    """)

                    await session.execute(sql, {
                        "id": new_asset_id,
                        "filename": f"{campaign_id}_{suffix}.webp",
                        "file_path": local_path,
                        "file_size": file_size,
                        "mime_type": "image/webp",
                        "dimensions": dims,
                        "campaign_id": campaign_id,
                        "media_metadata": json.dumps({
                            "original_url": url,
                            "localized_at": datetime.now(timezone.utc).isoformat(),
                            "source": "MediaCompressor"
                        })
                    })

                    # --- AI AUTO-TAGGING & VISUAL INTELLIGENCE (Giai đoạn 5) ---
                    # Chạy phân tích background để không block quá trình localization chính
                    asyncio.create_task(self.analyst.process_registry_entry(new_asset_id))

                return local_path
            finally:
                buffer.close()
                # Memory discipline: Force GC after heavy buffer/image processing
                del buffer
                gc.collect()
        except Exception as e:
            logger.error(f"[MediaCompressor] Localization failure for {url}: {str(e)}")
            return None

    def _save_webp(self, buffer: BytesIO, campaign_id: str, suffix: Union[int, str]) -> str:
        """Internal worker for image processing (Resampling + WebP)."""
        filename: str = f"{campaign_id}_{suffix}.webp"
        filepath: str = os.path.join(self.upload_dir, filename)

        with Image.open(buffer) as img:
            # R105: Downscale for performance (max 1920px)
            if max(img.size) > 1920:
                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)

            width, height = img.size
            # Save as optimized WebP
            img.save(filepath, "WEBP", quality=90)
            return f"{width}x{height}"

    async def _localize_remaining_html_images(self, html: str, campaign_id: str, session: Optional[AsyncSession] = None) -> str:
        """Surgical scan to catch any escaped external links in HTML tags."""
        if not html: return ""

        # Hardened Regex for all quote types
        img_pattern = re.compile(r'<img[^>]+src\s*=\s*["\']?(https?://[^"\' >]+)["\']?', re.IGNORECASE)
        urls: List[str] = list(set(img_pattern.findall(html)))

        if not urls: return html

        final_html: str = html
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for i, url in enumerate(urls):
                if url.startswith("/") or url.startswith("static"):
                    continue

                async with self.semaphore:
                    local_path = await self._download_and_save(client, url, campaign_id, f"ext_{i}", session)
                    if local_path:
                        final_html = final_html.replace(url, local_path)

        return final_html

    def wrap_html(self, content: str, local_assets: List[str], original_assets: Optional[List[str]] = None) -> str:
        """Standardizes article container and performs mass asset substitution."""
        if not content: return ""
        
        final_html: str = content
        for i, path in enumerate(local_assets):
            # Replacement Group A: Placeholders [IMAGE_N]
            final_html = final_html.replace(f"[IMAGE_{i+1}]", path)

            # Replacement Group B: Absolute remote URLs
            if original_assets and i < len(original_assets):
                orig_url = original_assets[i]
                if orig_url and orig_url != path and orig_url.startswith("http"):
                    # Catch both quoted and raw URL strings
                    final_html = final_html.replace(f'"{orig_url}"', f'"{path}"')
                    final_html = final_html.replace(f"'{orig_url}'", f"'{path}'")
                    final_html = final_html.replace(orig_url, path)

        # Cleanup: Remove internal Xohi annotations
        final_html = self._strip_annotations(final_html)
        return f"<article class='xohi-v62-article'>{final_html}</article>"

    def _strip_annotations(self, html: str) -> str:
        """Surgically unwrap <mark> tags used during internal analysis."""
        if not html: return ""
        
        pattern = re.compile(r'<mark\s+[^>]*class=["\']xohi-annotation["\'][^>]*>(.*?)</mark>', re.DOTALL | re.IGNORECASE)
        
        clean_html: str = html
        while True:
            new_html = pattern.sub(r'\1', clean_html)
            if new_html == clean_html:
                break
            clean_html = new_html
        return clean_html
