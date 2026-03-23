import re
import logging
from typing import List
from backend.utils.noise_cleaner import noise_cleaner

logger = logging.getLogger("api-gateway")

async def process_pen_draft(content: str, assets: List[str], primary: str) -> str:
    """Sanitize, cleanup and handle image placeholders for CreativePen."""
    # Remove markdown code fences
    if content.startswith("```"):
        content = content.split("```", 2)[-1] if "```" in content[3:] else content[3:]
        content = content.lstrip("html\n").rstrip("`")

    # Replace [IMAGE_N]
    content = replace_image_placeholders(content, assets, primary)
    
    # Final Noise Shield
    return await noise_cleaner.clean(content, mode="aggressive")

def replace_image_placeholders(content: str, assets: List[str], alt_text: str = "") -> str:
    """Surgical [IMAGE_N] replacement pass."""
    clean_assets: List[str] = []
    for a in assets:
        if isinstance(a, dict): clean_assets.append(a.get("file_path") or a.get("url") or str(a))
        elif hasattr(a, "file_path"): clean_assets.append(getattr(a, "file_path") or getattr(a, "url") or str(a))
        else: clean_assets.append(str(a))

    for i, url in enumerate(clean_assets[:30], 1):
        p = f"[IMAGE_{i}]"
        # In src attribute
        content = re.sub(rf'(src|href)=["\']\s*{re.escape(p)}\s*["\']', rf'\1="{url}"', content)
        # Standalone
        if p in content:
            fig = f'<figure class="content-image"><img src="{str(url)}" alt="{alt_text}" loading="lazy" /></figure>'
            content = content.replace(p, fig)
    
    return re.sub(r'\[IMAGE_\d+\]', '', content)
