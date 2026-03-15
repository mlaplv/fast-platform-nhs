import os
import re
import httpx
import asyncio
import logging
import hashlib
from PIL import Image
from io import BytesIO
from typing import List, Dict, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import flag_modified

import uuid
from backend.database.models import ContentCampaign, MediaRegistry
from backend.database.repositories import ContentCampaignRepository, MediaRegistryRepository
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
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(3)
        self.analyst = MediaAnalyst()

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, media_repo: Optional[MediaRegistryRepository] = None, **kwargs: object) -> AgentResponse:
        """Entry point for standard agentic flow."""
        campaign: Optional[ContentCampaign] = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found.", data={})

        # Step 1: Localize standard assets (images from Step 2)
        original_assets: List[str] = campaign.get_gold_val("original_remote_assets", list(campaign.assets_data or []))
        local_assets: List[str] = await self.localize_assets(campaign, media_repo)

        # Step 2: Localize Avatar (Gold Metadata)
        gold: Dict[str, object] = dict(campaign.gold_metadata or {})
        remote_avatar: Optional[str] = gold.get("avatar") # type: ignore

        if remote_avatar and remote_avatar.startswith("http"):
            async with httpx.AsyncClient(follow_redirects=True) as client:
                local_avatar = await self._download_and_save(client, remote_avatar, str(campaign.id), "avatar", media_repo)
                if local_avatar:
                    gold["avatar"] = local_avatar
                    campaign.gold_metadata = gold
                    flag_modified(campaign, "gold_metadata")

        # Step 3: Wrap Draft Content and apply asset replacement
        final_html: str = self.wrap_html(campaign.draft_content or "", local_assets, original_assets)

        # Step 4: Final Surgical Scan for manual/rogue external links
        final_html = await self._localize_remaining_html_images(final_html, str(campaign.id), media_repo)

        campaign.final_html = final_html
        campaign.assets_data = local_assets

        # Synchronize persistence
        await repo.update(campaign)
        if hasattr(repo, "session"):
            await repo.session.commit()

        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message="Media localized and verified for production.",
            data={"assets": local_assets, "final_html": final_html}
        )

    async def localize_assets(self, campaign: ContentCampaign, media_repo: Optional[MediaRegistryRepository] = None) -> List[str]:
        """Downloads and processes all assets defined in assets_data."""
        local_paths: List[str] = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for i, url in enumerate(campaign.assets_data or []):
                # Phase 73: Fast Path for already localized assets
                if url.startswith("/") or url.startswith("static"):
                    # Normalize paths (Remove /static prefix if present)
                    norm_path = url if url.startswith("/") else f"/{url}"
                    if norm_path.startswith("/static/v65_assets/"):
                        norm_path = norm_path.replace("/static/v65_assets/", "/v65_assets/")
                    local_paths.append(norm_path)
                    continue

                async with self.semaphore:
                    local_path = await self._download_and_save(client, url, str(campaign.id), i, media_repo)
                    local_paths.append(local_path if local_path else "/v65_assets/placeholder.webp")

        return local_paths

    async def _download_and_save(self, client: httpx.AsyncClient, url: str, campaign_id: str, suffix: Union[int, str], media_repo: Optional[MediaRegistryRepository] = None) -> Optional[str]:
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
                if media_repo:
                    full_path = os.path.join(self.upload_dir, f"{campaign_id}_{suffix}.webp")
                    file_size = os.path.getsize(full_path)

                    registry_entry = MediaRegistry(
                        id=str(uuid.uuid4()),
                        filename=f"{campaign_id}_{suffix}.webp",
                        file_path=local_path,
                        file_size=file_size,
                        mime_type="image/webp",
                        dimensions=dims,
                        campaign_id=campaign_id,
                        media_metadata={
                            "original_url": url,
                            "localized_at": datetime.now(timezone.utc).isoformat(),
                            "source": "MediaCompressor"
                        }
                    )
                    await media_repo.add(registry_entry)

                    # --- AI AUTO-TAGGING & VISUAL INTELLIGENCE (Giai đoạn 5) ---
                    # Chạy phân tích background để không block quá trình localization chính
                    asyncio.create_task(self.analyst.process_registry_entry(registry_entry.id))

                return local_path
            finally:
                buffer.close()
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
            img.save(filepath, "WEBP", quality=85)
            return f"{width}x{height}"

    async def _localize_remaining_html_images(self, html: str, campaign_id: str, media_repo: Optional[MediaRegistryRepository] = None) -> str:
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
                    local_path = await self._download_and_save(client, url, campaign_id, f"ext_{i}", media_repo)
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
