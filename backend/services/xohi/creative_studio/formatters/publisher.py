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

async def publish_campaign_to_news(campaign, campaign_repo, category_id: str = None) -> bool:
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
            tenant_id=campaign.tenant_id, 
            category="Tin tức",
            category_id=category_id, # CNS V85.2: Synced Category ID
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

async def publish_campaign_to_products(campaign, campaign_repo, category_id: str = None) -> bool:
    """CNS V85.1: Publication to Commerce (ProductBase) + Hard Memory Cleanup."""
    try:
        from backend.database.repositories import ProductBaseRepository
        from backend.database.models.commerce import ProductBase, ProductEmbedding
        
        if hasattr(campaign_repo, "session"):
            from sqlalchemy import inspect
            if "final_html" in inspect(campaign).unloaded:
                await campaign_repo.session.refresh(campaign, ["final_html"])

        product_repo = ProductBaseRepository(session=campaign_repo.session)
        name = campaign.get_gold_val("topic") or campaign.get_gold_val("title", "Sản phẩm mới")
        content = campaign.final_html or campaign.draft_content
        if not content: return False

        # CNS V85.1: Extract Rich Metadata from Gold
        gold = campaign.gold_metadata or {}
        attrs = gold.get("attributes", {})
        price = float(gold.get("price", 0))
        seo_t = gold.get("seo_title") or name
        seo_d = gold.get("seo_description") or name
        seo_k = campaign.get_gold_val("primary_keyword", "")

        images = []
        if campaign.assets_data and isinstance(campaign.assets_data, list):
            for a in campaign.assets_data:
                url = a.get("url") or a.get("path") if isinstance(a, dict) else (a if isinstance(a, str) else None)
                if url: images.append(url)

        new_prod = ProductBase(
            id=str(uuid.uuid4()), name=name, description=content,
            sku=f"XH-{str(uuid.uuid4())[:8].upper()}",
            price=price, status="ACTIVE",
            slug=f"{slugify(name)}-{str(uuid.uuid4())[:8]}",
            tenant_id=campaign.tenant_id,
            images=images,
            attributes=attrs,
            seo_title=seo_t,
            seo_description=seo_d,
            seo_keywords=seo_k,
            category_id=category_id # CNS V85.2: Synced Category ID
        )
        await product_repo.add(new_prod)

        # Generate Embedding (Shared logic with Articles)
        try:
            encoder = get_shared_encoder()
            if encoder:
                vec = (await asyncio.get_event_loop().run_in_executor(None, lambda: list(encoder.embed([name]))))[0]
                session = campaign_repo.session
                session.add(ProductEmbedding(
                    id=str(uuid.uuid4()), product_base_id=new_prod.id,
                    embedding=np.array(vec, dtype=np.float32).tobytes().hex()
                ))
        except Exception as e: logger.error(f"[Publisher] Product Embedding failed: {e}")

        # Hard Cleanup (Memory Safety)
        campaign.status, campaign.draft_content, campaign.final_html = "COMPLETED", "", ""
        campaign.topic_data, campaign.assets_data, campaign.outline_data = {}, [], {}
        await campaign_repo.update(campaign); return True
    except Exception as e:
        logger.exception(f"[Publisher] Product Publication Failed: {e}"); return False
