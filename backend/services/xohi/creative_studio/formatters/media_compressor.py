import os
import re
import httpx
import asyncio
from PIL import Image
from io import BytesIO
from typing import List, Dict
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository

class MediaCompressor:
    """
    Step 6: Media Localization.
    Hardened Rule 6: Download, Compress (WebP), Store Local.
    V61.0: Zero-Copy Optimization & Non-blocking I/O.
    """
    def __init__(self, upload_dir: str = "static/uploads/v62"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        # R106: Limit concurrent image processing for 2GB RAM safety
        self.semaphore = asyncio.Semaphore(3)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs):
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign: return

        # Phase 74: Retrieve original remote URLs from Golden Thread if available
        # This ensures reliable URL swapping even if assets_data has already been localized.
        original_assets = campaign.get_gold_val("original_remote_assets", list(campaign.assets_data or []))

        local_assets = await self.localize_assets(campaign)
        final_html = self.wrap_html(campaign.draft_content, local_assets, original_assets)
        campaign.final_html = final_html
        campaign.assets_data = local_assets
        # Explicit return for Registry protocol
        from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message="Media localized and compressed successfully.",
            data={"assets": local_assets, "final_html": final_html}
        )

    async def localize_assets(self, campaign: ContentCampaign) -> List[str]:
        """
        Downloads images from assets_data, converts to WebP, and updates paths.
        Enforces Rule 6.1: Explicit memory management for 2GB RAM constraints.
        """
        local_paths = []
        async with httpx.AsyncClient() as client:
            for i, url in enumerate(campaign.assets_data or []):
                # Phase 73: Skip if already localized
                if url.startswith("/static/"):
                    local_paths.append(url)
                    continue

                # R106: Throttle concurrency using semaphore
                async with self.semaphore:
                    try:
                        response = await client.get(url, timeout=10.0)
                        response.raise_for_status()
                        
                        # Process image with Pillow (Rule: Zero-Leak)
                        buffer = BytesIO(response.content)
                        try:
                            # R105: Use asyncio.to_thread for CPU-bound Pillow ops
                            await asyncio.to_thread(self._save_webp, buffer, campaign.id, i)
                            filename = f"{campaign.id}_{i}.webp"
                            local_paths.append(f"/static/uploads/v62/{filename}")
                        finally:
                            buffer.close()
                            
                    except Exception as e:
                        import logging
                        logging.getLogger("api-gateway").error(f"[MediaCompressor] Failed for {url}: {e}")
                        local_paths.append(url)
                    
        return local_paths

    def _save_webp(self, buffer: BytesIO, campaign_id: str, index: int):
        """Internal synchronous worker for thread pool."""
        with Image.open(buffer) as img:
            filename = f"{campaign_id}_{index}.webp"
            filepath = os.path.join(self.upload_dir, filename)
            # Hardened Rule: Max 1920px for web display
            if max(img.size) > 1920:
                img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            
            img.save(filepath, "WEBP", quality=80)
            # R105: Explicit close to reclaim RAM (2GB limit)
            img.close()

    def wrap_html(self, content: str, local_assets: List[str], original_assets: List[str] = None) -> str:
        """Injects localized assets and applies final SEO formatting."""
        final_html = content
        # Ensure we don't crash if content is None
        if not final_html: return ""

        # Phase 74: Dual-mode Replacement
        # 1. Replace traditional [IMAGE_N] placeholders
        # 2. Replace absolute URLs (in case Step 4 already swapped them)
        for i, path in enumerate(local_assets):
            placeholder = f"[IMAGE_{i+1}]"
            final_html = final_html.replace(placeholder, path)

            if original_assets and i < len(original_assets):
                original_url = original_assets[i]
                if original_url and original_url != path:
                    # Replace both quoted and unquoted (though quotes are safer)
                    final_html = final_html.replace(f'"{original_url}"', f'"{path}"')
                    final_html = final_html.replace(f"'{original_url}'", f"'{path}'")
                    # Fallback for raw text replacement if needed
                    final_html = final_html.replace(original_url, path)

        # Phase 71.30: Expert Safety Strip — Remove internal analysis markers
        final_html = self._strip_annotations(final_html)
            
        return f"<article class='xohi-v62-article'>{final_html}</article>"

    def _strip_annotations(self, html: str) -> str:
        """
        Expert Mode: Surgically removes <mark class='xohi-annotation'> tags while 
        preserving the inner text for professional production HTML.
        """
        if not html: return ""
        
        # Pattern matches <mark class="xohi-annotation"> ... </mark> Case-Insensitive
        # Captures group 1: the inner text
        pattern = re.compile(r'<mark\s+[^>]*class=["\']xohi-annotation["\'][^>]*>(.*?)</mark>', re.DOTALL | re.IGNORECASE)
        
        # Recursive replacement to handle any accidentally nested marks (though rare in Tiptap)
        clean_html = html
        while True:
            new_html = pattern.sub(r'\1', clean_html)
            if new_html == clean_html:
                break
            clean_html = new_html
            
        return clean_html
