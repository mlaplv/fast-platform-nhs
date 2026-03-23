import logging
import uuid
import asyncio
import numpy as np
from datetime import datetime, timezone
from backend.database.repositories import ArticleRepository, ArticleEmbeddingRepository
from backend.database.models import Article, ArticleEmbedding
from backend.utils.text import slugify
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder

logger = logging.getLogger("publisher")

async def publish_campaign_to_news(campaign, campaign_repo) -> bool:
    """Phase 76.3: Publication to News (Articles) + Hard Memory Cleanup."""
    try:
        if hasattr(campaign_repo, "session"):
            from sqlalchemy import inspect
            if "final_html" in inspect(campaign).unloaded:
                await campaign_repo.session.refresh(campaign, ["final_html"])

        article_repo = ArticleRepository(session=campaign_repo.session)
        title = campaign.get_gold_val("topic") or campaign.get_gold_val("title", "Bài viết sáng tạo mới")
        content = campaign.final_html or campaign.draft_content
        if not content: return False

        feat_img = None
        if campaign.assets_data and isinstance(campaign.assets_data, list) and len(campaign.assets_data) > 0:
            a = campaign.assets_data[0]
            feat_img = a.get("url") or a.get("path") if isinstance(a, dict) else (a if isinstance(a, str) else None)

        new_art = Article(
            id=str(uuid.uuid4()), title=title, content=content,
            slug=f"{slugify(title)}-{str(uuid.uuid4())[:8]}",
            author_id=campaign.user_id, status="PUBLISHED",
            tenant_id=campaign.tenant_id, category="Tin tức",
            featured_image=feat_img
        )
        await article_repo.add(new_art)

        # Generate Embedding
        try:
            encoder = get_shared_encoder()
            if encoder:
                vec = (await asyncio.get_event_loop().run_in_executor(None, lambda: list(encoder.embed([title]))))[0]
                await ArticleEmbeddingRepository(session=campaign_repo.session).add(ArticleEmbedding(
                    id=str(uuid.uuid4()), article_id=new_art.id,
                    embedding=np.array(vec, dtype=np.float32).tobytes().hex()
                ))
        except Exception as e: logger.error(f"[Publisher] Embedding failed: {e}")

        # Hard Cleanup (Memory Safety)
        campaign.status, campaign.draft_content, campaign.final_html = "COMPLETED", "", ""
        campaign.topic_data, campaign.assets_data, campaign.outline_data = {}, [], {}
        await campaign_repo.update(campaign); return True
    except Exception as e:
        logger.exception(f"[Publisher] Failed: {e}"); return False
