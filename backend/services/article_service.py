import re
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional
from sqlalchemy import text, update, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException, HTTPException

from backend.database.models import Article, User as UserModel
from backend.schemas.article import (
    ArticleResponse, ArticleListResponse, CreateArticleRequest,
    UpdateArticleRequest
)
from backend.schemas.common import SuccessResponse, BulkActionResponse
from backend.services.article_vector_service import ArticleVectorService
from backend.services.xohi_memory import xohi_memory
from backend.utils.sql import escape_like
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.event_bus import event_bus
from backend.utils.media import extract_media_urls

logger = logging.getLogger("api-gateway")

class ArticleService:
    """Business Logic for Articles/News (Elite V2.2)."""
    
    def __init__(self, vector_service: ArticleVectorService):
        self.vector_service = vector_service

    async def list_articles(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> ArticleListResponse:
        """List articles (R76: Scalar Projection). R1.5: Zero-Hydration."""
        conditions = [Article.deleted_at == None]
        if status and status != "all":
            conditions.append(Article.status == status.upper())
        if category and category != "all":
            conditions.append(Article.category == category)
        if search:
            safe = escape_like(search)
            conditions.append(or_(
                Article.title.ilike(f"%{safe}%"),
                Article.category.ilike(f"%{safe}%"),
            ))

        # 1. COUNT Cache Redis Optimization
        cache_key = f"articles:count:status={status}:cat={category}:search={search}"
        total = None

        if xohi_memory._use_redis:
            try:
                cached_count = await xohi_memory.client.get(cache_key)
                if cached_count is not None:
                    total = int(cached_count)
            except Exception:
                pass

        if total is None:
            count_stmt = select(func.count(Article.id)).where(and_(*conditions))
            total = await db_session.scalar(count_stmt) or 0

            if xohi_memory._use_redis:
                try:
                    await xohi_memory.client.set(cache_key, str(total), ex=300)
                except Exception:
                    pass

        # 2. Scalar Projection Fetch
        stmt = select(
            Article.id, Article.title, Article.slug, Article.excerpt,
            Article.status, Article.category, Article.views,
            Article.created_at, Article.author_id, Article.featured_image,
            Article.seo_keywords, Article.seo_og_image, Article.article_metadata,
            UserModel.name.label("author_name")
        ).outerjoin(UserModel, Article.author_id == UserModel.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(Article.created_at.desc())

        result = await db_session.execute(stmt)
        data = [ArticleResponse.model_validate(row._mapping) for row in result]
        return ArticleListResponse(data=data, total=total)

    async def get_article(self, db_session: AsyncSession, article_id: str) -> ArticleResponse:
        """Get a single article (R76: Scalar Projection)."""
        stmt = select(
            Article.id, Article.title, Article.slug, Article.excerpt, Article.content,
            Article.status, Article.category, Article.views,
            Article.seo_title, Article.seo_description,
            Article.seo_keywords, Article.seo_og_image,
            Article.featured_image, Article.article_metadata,
            Article.created_at, Article.author_id,
            UserModel.name.label("author_name")
        ).outerjoin(UserModel, Article.author_id == UserModel.id).where(
            Article.id == article_id,
            Article.deleted_at == None
        )

        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Article {article_id} not found")

        return ArticleResponse.model_validate(row._mapping)


    async def get_article_by_slug(self, db_session: AsyncSession, slug: str) -> ArticleResponse:
        """Get a single article by slug (R76: Scalar Projection)."""
        stmt = select(
            Article.id, Article.title, Article.slug, Article.excerpt, Article.content,
            Article.status, Article.category, Article.views,
            Article.seo_title, Article.seo_description,
            Article.seo_keywords, Article.seo_og_image,
            Article.featured_image, Article.article_metadata,
            Article.created_at, Article.author_id,
            UserModel.name.label("author_name")
        ).outerjoin(UserModel, Article.author_id == UserModel.id).where(
            Article.slug == slug,
            Article.deleted_at == None
        )

        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Article with slug '{slug}' not found")

        # GEO 2026: Inject real FAQs into pre-computed SEO Meta
        article_data = dict(row._mapping)
        meta_dict = article_data.get("article_metadata") or {}
        faqs = meta_dict.get("faqs", [])

        from backend.services.commerce.seo_service import SeoService
        seo_meta = SeoService.generate_article_seo_meta(
            title=article_data["title"],
            slug=article_data["slug"],
            excerpt=article_data["excerpt"],
            image=article_data["featured_image"],
            author=article_data["author_name"],
            date_published=article_data["created_at"].isoformat() if article_data["created_at"] else None,
            faqs=faqs
        )
        article_data["seo_meta"] = seo_meta
        
        return ArticleResponse.model_validate(article_data)

    async def create_article(self, db_session: AsyncSession, data: CreateArticleRequest) -> SuccessResponse:
        """Create a new article and its embedding."""
        slug = data.slug or re.sub(
            r'[^a-z0-9]+', '-',
            data.title.lower()
                .replace("đ", "d")
                .replace("ă", "a").replace("â", "a")
                .replace("ê", "e").replace("ô", "o")
                .replace("ơ", "o").replace("ư", "u")
        ).strip("-") + f"-{int(time.time())}"

        new_id = str(uuid.uuid4())

        # Phase 76.95: Advanced Structural Noise Cleaning (Elite V2.2)
        cleaned_content = await noise_cleaner.clean(data.content, strip_html=False) if data.content else ""
        cleaned_excerpt = await noise_cleaner.clean(data.excerpt, strip_html=True) if data.excerpt else ""

        article = Article(
            id=new_id,
            title=data.title,
            slug=slug,
            excerpt=cleaned_excerpt,
            content=cleaned_content,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            seo_keywords=data.seo_keywords,
            seo_og_image=data.seo_og_image,
            status=data.status.upper(),
            category=data.category,
            author_id=data.authorId,
            featured_image=data.featured_image,
            article_metadata=data.metadata.model_dump() if data.metadata else {},
        )
        db_session.add(article)

        # RAG Upsert
        await self.vector_service.upsert_article_embedding(
            db_session, new_id, data.title, cleaned_content
        )

        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        
        # Elite V2.2: Sync Media Links
        await self._sync_media_links(db_session, new_id, article)
        
        return SuccessResponse(ok=True, id=new_id)

    async def update_article(self, db_session: AsyncSession, article_id: str, data: UpdateArticleRequest) -> SuccessResponse:
        """Update an article and its embedding."""
        # Rule 1.5: Detail fetch for update (Surgical)
        stmt = select(Article).where(Article.id == article_id, Article.deleted_at == None)
        res = await db_session.execute(stmt)
        article = res.scalar_one_or_none()

        if not article:
            raise NotFoundException(f"Article {article_id} not found")

        if data.title is not None: article.title = data.title
        if data.slug is not None: article.slug = data.slug

        # Phase 76.95: Advanced Structural Noise Cleaning (Elite V2.2)
        if data.excerpt is not None:
            article.excerpt = await noise_cleaner.clean(data.excerpt, strip_html=True)
        if data.content is not None:
            article.content = await noise_cleaner.clean(data.content, strip_html=False)

        if data.seo_title is not None: article.seo_title = data.seo_title
        if data.seo_description is not None: article.seo_description = data.seo_description
        if data.seo_keywords is not None: article.seo_keywords = data.seo_keywords
        if data.seo_og_image is not None: article.seo_og_image = data.seo_og_image
        if data.status is not None: article.status = data.status.upper()
        if data.category is not None: article.category = data.category
        if data.featured_image is not None: article.featured_image = data.featured_image

        # GEO 2026: Merge metadata (FAQs etc.)
        if data.metadata is not None:
            existing_meta = article.article_metadata or {}
            new_meta = data.metadata.model_dump()
            existing_meta.update(new_meta)
            article.article_metadata = existing_meta

        if data.title is not None or data.content is not None:
            await self.vector_service.upsert_article_embedding(
                db_session, article_id, article.title, article.content
            )

        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()

        # Elite V2.2: Sync Media Links
        await self._sync_media_links(db_session, article_id, article)

        return SuccessResponse(ok=True, id=article_id)

    async def _sync_media_links(self, db_session: AsyncSession, article_id: str, article: Article) -> None:
        """
        Elite V2.2: Neural Media Sync for News/Articles.
        Trích xuất và đồng bộ toàn bộ liên kết hình ảnh thông qua Recursive Scan.
        Bao gồm: Featured Image, SEO OG Image, Content (HTML).
        """
        try:
            article_data = {
                "featured_image": article.featured_image,
                "seo_og_image": article.seo_og_image,
                "content": article.content
            }
            urls = extract_media_urls(article_data)

            # 3. Phát sự kiện (Decoupled Flow)
            if urls:
                await event_bus.emit("MEDIA_SYNC_REQUIRED", {
                    "entity_id": str(article_id),
                    "entity_type": "news",
                    "urls": list(urls)
                })
                logger.info(f"[ArticleService] Emitted MEDIA_SYNC_REQUIRED for news {article_id} with {len(urls)} URLs")
        except Exception as e:
            logger.error(f"[ArticleService] Failed to emit media sync: {e}")

    async def delete_article(self, db_session: AsyncSession, article_id: str) -> SuccessResponse:
        stmt = update(Article).where(Article.id == article_id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        return SuccessResponse(ok=True, id=article_id)

    async def bulk_delete(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(Article).where(Article.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        return BulkActionResponse(ok=True, count=len(ids))

    async def bulk_publish(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        stmt = update(Article).where(Article.id.in_(ids)).values(status="PUBLISHED")
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        return BulkActionResponse(ok=True, count=len(ids))

    async def bulk_patch(
        self, db_session: AsyncSession, ids: List[str], status: Optional[str] = None, category: Optional[str] = None
    ) -> BulkActionResponse:
        values = {}
        if status: values["status"] = status.upper()
        if category: values["category"] = category
        
        if not values:
            return BulkActionResponse(ok=True, count=0)
            
        stmt = update(Article).where(Article.id.in_(ids)).values(**values)
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        return BulkActionResponse(ok=True, count=len(ids))

    async def suggest_seo(self, title: str, content: str) -> Dict[str, str]:
        """GEO 2026: XOHI Auto SEO Suggestion for Articles."""
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        agent = Agent(
            system_prompt=(
                "You are an SEO expert. Given an article title and content, suggest optimized SEO metadata.\n"
                "Constraints:\n"
                "1. SEO Title: Max 60 characters, catchy but professional.\n"
                "2. SEO Description: Max 160 characters, concise and engaging.\n"
                "3. Keywords: 5-7 keywords separated by commas.\n"
                "Return ONLY exact valid JSON object: {\"seo_title\": \"...\", \"seo_description\": \"...\", \"seo_keywords\": \"...\"}"
            )
        )
        content_excerpt = (content or "")[:2000]
        prompt = f"Article Title: {title}\nArticle Content: {content_excerpt}"

        try:
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                role="fast",
                timeout=45.0
            )

            if result:
                suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r'\{.*\}', suggested_json_str, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, dict):
                        return {
                            "seo_title": parsed.get("seo_title", ""),
                            "seo_description": parsed.get("seo_description", ""),
                            "seo_keywords": parsed.get("seo_keywords", ""),
                        }

            return {"seo_title": "", "seo_description": "", "seo_keywords": ""}

        except Exception as e:
            logger.exception(f"[ArticleService] AI SEO Suggestion Failed: {e}")
            return {"seo_title": "", "seo_description": "", "seo_keywords": ""}

    async def suggest_faqs(self, title: str, content: str) -> List[Dict[str, str]]:
        """GEO 2026: XOHI Auto FAQ Generator for Articles."""
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        agent = Agent(
            system_prompt="You are an expert content advisor. Given an article title and content excerpt, generate 3 to 5 frequently asked questions and short, helpful answers in Vietnamese. Return ONLY exact valid JSON array of objects without markdown wrapping or backticks, like this: [{\"question\": \"...\", \"answer\": \"...\"}]"
        )
        # Truncate content to first 2000 chars for prompt efficiency
        content_excerpt = (content or "")[:2000]
        prompt = f"Article Title: {title}\nArticle Content: {content_excerpt}"

        try:
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                role="fast",
                timeout=45.0
            )

            if result:
                suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r'\[.*\]', suggested_json_str, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list):
                        return parsed

            return []

        except Exception as e:
            logger.exception(f"[ArticleService] AI FAQ Suggestion Failed: {e}")
            return []

# ==========================================
# SERVICE PROVIDERS (V76.2 DI PATTERN)
# ==========================================

async def provide_article_service(vector_service: ArticleVectorService) -> ArticleService:
    """Standard Litestar Provider for ArticleService."""
    return ArticleService(vector_service=vector_service)
