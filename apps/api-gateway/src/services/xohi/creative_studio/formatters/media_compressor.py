import os
import httpx
from PIL import Image
from io import BytesIO
from typing import List, Dict
from src.database.models import ContentCampaign

class MediaCompressor:
    """
    Step 6: Media Localization.
    Hardened Rule 6: Download, Compress (WebP), Store Local.
    """
    def __init__(self, upload_dir: str = "/Users/lv/Desktop/fast-platform-core/static/uploads/v62"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def localize_assets(self, campaign: ContentCampaign) -> List[str]:
        """
        Downloads images from assets_data, converts to WebP, and updates paths.
        """
        local_paths = []
        async with httpx.AsyncClient() as client:
            for i, url in enumerate(campaign.assets_data or []):
                try:
                    response = await client.get(url, timeout=10.0)
                    response.raise_for_status()
                    
                    # Process image with Pillow
                    img = Image.open(BytesIO(response.content))
                    
                    # Rule: Convert to WebP 80% quality for SEO/Performance
                    filename = f"{campaign.id}_{i}.webp"
                    filepath = os.path.join(self.upload_dir, filename)
                    
                    img.save(filepath, "WEBP", quality=80)
                    
                    # Return public URL path
                    local_paths.append(f"/static/uploads/v62/{filename}")
                except Exception as e:
                    # If one image fails, we log it and continue
                    print(f"Failed to localize image {url}: {e}")
                    # Keep original URL as fallback or skip
                    local_paths.append(url)
                    
        return local_paths

    def wrap_html(self, content: str, local_assets: List[str], gold_metadata: Dict) -> str:
        """
        Injects localized assets and applies final SEO formatting.
        """
        final_html = content
        for i, path in enumerate(local_assets):
            placeholder = f"[IMAGE_{i+1}]"
            # Rule 4.2: SEO Alt Tag Injection
            alt_text = gold_metadata.get("primary_keyword", "Content Factory V62")
            img_tag = f'<img src="{path}" alt="{alt_text}" class="v62-localized-asset" />'
            final_html = final_html.replace(placeholder, img_tag)
            
        return f"<article class='xohi-v62-article'>{final_html}</article>"
