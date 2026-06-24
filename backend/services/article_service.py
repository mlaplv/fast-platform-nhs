import re
import json
import time
from backend.utils.uid import new_id
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy import update, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

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
from backend.services.lexical_sanitizer import sanitize_ai_text
from backend.services.prompt_entropy import build_entropy_system_prompt
from backend.database import current_tenant_id

logger = logging.getLogger("api-gateway")


async def _get_sge_config_async() -> dict[str, object]:
    """SGE Shield V1.0: Đọc entropy config từ Redis. Fallback defaults nếu unavailable."""
    defaults: dict[str, object] = {
        "enabled": True,
        "lexical_sanitizer_enabled": True,
        "tone_override": None,
        "structure_override": None,
        "schema_drop_probability": 0.2,
    }
    try:
        raw = await xohi_memory.client.get("system:entropy_config")
        if raw:
            return json.loads(raw)  # type: ignore[return-value]
    except Exception:
        pass
    return defaults


class ArticleService:
    """Business Logic for Articles/News (Elite V2.2)."""
    
    def __init__(self, vector_service: ArticleVectorService):
        self.vector_service = vector_service

    async def _get_product_context(self, db_session: AsyncSession, product_id: str) -> tuple[str, str]:
        """Helper to fetch product context (name, keywords, description) for AI prompts."""
        if not product_id:
            return "", ""
        
        product_id = product_id.strip()
        if product_id.lower() in ("null", "undefined", ""):
            return "", ""

        from backend.database.models import ProductBase
        try:
            prod_stmt = select(
                ProductBase.name, ProductBase.seo_keywords, ProductBase.short_description
            ).where(ProductBase.id == product_id, ProductBase.deleted_at == None)
            prod_row = (await db_session.execute(prod_stmt)).first()
            if prod_row:
                product_name = prod_row.name
                product_context = (
                    f"SẢN PHẨM LIÊN QUAN ĐƯỢC CHỌN (BẮT BUỘC PHẢI LIÊN KẾT/NHẮC TỚI TRONG NỘI DUNG):\n"
                    f"- Tên sản phẩm: {prod_row.name}\n"
                    f"- Từ khóa sản phẩm: {prod_row.seo_keywords or ''}\n"
                    f"- Mô tả ngắn sản phẩm: {prod_row.short_description or ''}\n"
                )
                return product_name, product_context
        except Exception as e:
            logger.exception(f"[ArticleService] Lỗi khi truy vấn thông tin sản phẩm {product_id}: {e}")
        
        return "", ""

    async def list_articles(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        exclude_status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> ArticleListResponse:
        """List articles (R76: Scalar Projection) with Keyset Cursor Pagination."""
        conditions = [Article.deleted_at == None]
        if status and status != "all":
            conditions.append(Article.status == status.upper())
        if exclude_status:
            conditions.append(Article.status != exclude_status.upper())
        if category and category != "all":
            conditions.append(Article.category == category)
        if search:
            safe = escape_like(search)
            conditions.append(or_(
                Article.title.ilike(f"%{safe}%"),
                Article.category.ilike(f"%{safe}%"),
            ))

        # Keyset (Cursor) Pagination if cursor is provided
        if cursor and cursor != "undefined":
            # Fetch created_at of the cursor record
            cursor_query = select(Article.id, Article.created_at).where(Article.id == cursor)
            cursor_res = await db_session.execute(cursor_query)
            cursor_row = cursor_res.first()
            if cursor_row:
                c_id, c_time = cursor_row[0], cursor_row[1]
                conditions.append(
                    or_(
                        Article.created_at < c_time,
                        and_(Article.created_at == c_time, Article.id < c_id)
                    )
                )

        # 1. COUNT Cache Redis Optimization
        total = 0
        if not cursor:
            cache_key = f"articles:count:status={status}:cat={category}:search={search}"
            if xohi_memory._use_redis:
                try:
                    cached_count = await xohi_memory.client.get(cache_key)
                    if cached_count is not None:
                        total = int(cached_count)
                except Exception:
                    pass

            if total is None or total == 0:
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
            Article.created_at, Article.updated_at, Article.author_id, Article.featured_image,
            Article.seo_keywords, Article.seo_og_image, Article.article_metadata,
            UserModel.name.label("author_name")
        ).outerjoin(UserModel, Article.author_id == UserModel.id).where(
            and_(*conditions)
        ).order_by(Article.created_at.desc(), Article.id.desc()).limit(limit + 1)

        if not cursor:
            stmt = stmt.offset(offset)

        result = await db_session.execute(stmt)
        rows = result.all()

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        # Elite V2.2: Fast bulk fetch for review counts
        review_counts = {}
        upcoming_appts = {}
        if rows:
            from backend.database.models import SystemReview, Appointment
            rc_stmt = select(SystemReview.entity_id, func.count(SystemReview.id)).where(
                SystemReview.entity_id.in_([str(r.id) for r in rows]),
                SystemReview.entity_type == "NEWS",
                SystemReview.status == "APPROVED"
            ).group_by(SystemReview.entity_id)
            rc_res = await db_session.execute(rc_stmt)
            review_counts = {r[0]: r[1] for r in rc_res.all()}

            draft_ids = [str(r.id) for r in rows if r.status != "PUBLISHED"]
            if draft_ids:
                appt_stmt = select(
                    Appointment.id, Appointment.start_time, Appointment.status, Appointment.metadata_json
                ).where(
                    and_(
                        Appointment.deleted_at == None,
                        Appointment.status == "UPCOMING"
                    )
                )
                appt_res = await db_session.execute(appt_stmt)
                for appt in appt_res.all():
                    meta = appt.metadata_json or {}
                    if meta.get("action") == "publish_article":
                        aid = meta.get("article_id")
                        if aid in draft_ids:
                            upcoming_appts[str(aid)] = {
                                "id": appt.id,
                                "start_time": appt.start_time.isoformat() if appt.start_time else None,
                                "status": appt.status
                            }

        data = []
        for row in rows:
            row_dict = dict(row._mapping)
            row_dict["review_count"] = review_counts.get(str(row.id), 0)
            row_dict["upcoming_appointment"] = upcoming_appts.get(str(row.id))
            data.append(ArticleResponse.model_validate(row_dict))

        next_cursor = None
        if data and has_more:
            next_cursor = str(data[-1].id)

        return ArticleListResponse(
            data=data,
            total=total,
            next_cursor=next_cursor,
            has_more=has_more
        )

    async def search_semantic(
        self,
        db_session: AsyncSession,
        query: str,
        limit: int = 5
    ) -> List[ArticleResponse]:
        """Elite V2.2: Hybrid Search (Keyword + Semantic) for articles."""
        safe = query.strip()
        if not safe:
            return []

        # 1. First Pass: Fast Keyword Search (Explicit matching)
        keyword_stmt = select(Article.id).where(
            and_(
                Article.status == "PUBLISHED",
                Article.title.ilike(f"%{safe}%")
            )
        ).limit(limit)
        keyword_result = await db_session.execute(keyword_stmt)
        keyword_ids = [str(row[0]) for row in keyword_result.fetchall()]

        # 2. Second Pass: Deep Semantic Search (Vector)
        vectors = await self.vector_service.search_semantic(
            db_session=db_session,
            query=safe,
            limit=limit
        )
        
        # Merge IDs maintaining order: Keywords first, then new semantic hits
        seen_ids = set(keyword_ids)
        final_ids = list(keyword_ids)
        
        vector_ids = []
        scores_map = {}
        for v in vectors:
            vid = str(v["id"])
            scores_map[vid] = v["match_score"]
            if vid not in seen_ids:
                final_ids.append(vid)
                seen_ids.add(vid)
        
        if not final_ids:
            return []

        # 3. Final Hydration (Scalar Projection)
        stmt = select(
            Article.id, Article.title, Article.slug, Article.excerpt,
            Article.status, Article.category, Article.views,
            Article.created_at, Article.updated_at, Article.author_id, Article.featured_image,
            Article.article_metadata,
            UserModel.name.label("author_name")
        ).outerjoin(UserModel, Article.author_id == UserModel.id).where(
            Article.id.in_(final_ids[:limit])
        )
        
        result = await db_session.execute(stmt)
        articles_map = {str(row.id): row._mapping for row in result}
        
        # Reconstruct ordered list with metadata injection
        final_results = []
        for aid in final_ids[:limit]:
            if aid in articles_map:
                art_data = dict(articles_map[aid])
                # Inject match score if available from vector search, else 0.99 for exact keyword hit
                art_data["match_score"] = scores_map.get(aid, 0.995 if aid in keyword_ids else 0.5)
                final_results.append(ArticleResponse.model_validate(art_data))
                
        return final_results


    async def get_article(self, db_session: AsyncSession, article_id: str) -> ArticleResponse:
        """Get a single article (R76: Scalar Projection)."""
        stmt = select(
            Article.id, Article.title, Article.slug, Article.excerpt, Article.content,
            Article.status, Article.category, Article.views,
            Article.seo_title, Article.seo_description,
            Article.seo_keywords, Article.seo_og_image,
            Article.featured_image, Article.article_metadata,
            Article.created_at, Article.updated_at, Article.author_id,
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
            Article.created_at, Article.updated_at, Article.author_id,
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
        seo_meta = await SeoService.generate_article_seo_meta(
            title=article_data["title"],
            slug=article_data["slug"],
            excerpt=article_data["excerpt"],
            image=article_data["featured_image"],
            author=article_data["author_name"],
            date_published=article_data["created_at"].isoformat() if article_data["created_at"] else None,
            date_modified=article_data["updated_at"].isoformat() if article_data.get("updated_at") else None,
            faqs=faqs,
            db=db_session,
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

        new_id_val = new_id()

        # SGE Shield V1.0: Lexical Sanitizer — tôn trọng flag admin
        sge_cfg = await _get_sge_config_async()
        lex_enabled: bool = bool(sge_cfg.get("enabled", True)) and bool(sge_cfg.get("lexical_sanitizer_enabled", True))
        pre_content = sanitize_ai_text(data.content, seed=slug, enabled=lex_enabled) if data.content else ""
        pre_excerpt = sanitize_ai_text(data.excerpt, seed=f"{slug}:excerpt", enabled=lex_enabled) if data.excerpt else ""

        # Phase 76.95: Advanced Structural Noise Cleaning (Elite V2.2)
        cleaned_content = await noise_cleaner.clean(pre_content, strip_html=False) if pre_content else ""
        cleaned_excerpt = await noise_cleaner.clean(pre_excerpt, strip_html=True) if pre_excerpt else ""

        article = Article(
            id=new_id_val,
            title=data.title,
            slug=slug,
            excerpt=cleaned_excerpt,
            content=cleaned_content,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            seo_keywords=data.seo_keywords,
            seo_og_image=data.seo_og_image,
            status=data.status.upper(),
            category=data.category if isinstance(data.category, str) else data.category.value,
            author_id=data.authorId,
            tenant_id=current_tenant_id.get() or "default",
            featured_image=data.featured_image,

            article_metadata=data.metadata.model_dump() if data.metadata else {},
            analysis_report=data.analysis_report or {},
        )
        db_session.add(article)
        await db_session.flush() # Elite V2.2: Force flush to DB so raw SQL FK check passes

        # RAG Upsert
        await self.vector_service.upsert_article_embedding(
            db_session, new_id_val, data.title, cleaned_content
        )

        # Elite V2.2: Knowledge Graph Generation (SGE Optimization)
        # [LEAK FIX] flush+expire_all trước khi gọi AI — trả connection về pool
        # trong suốt thời gian AI xử lý, tránh checkout leak.
        await db_session.flush()
        db_session.expire_all()
        from backend.services.xohi.creative_studio.operatives.kg_generator import generate_knowledge_graph
        import asyncio as _asyncio
        try:
            async with _asyncio.timeout(25):
                kg_data = await generate_knowledge_graph(
                    content=cleaned_content,
                    topic=data.title
                )
            # Reload article để set field sau khi expire_all
            res_after_kg = await db_session.execute(select(Article).where(Article.id == new_id_val))
            article = res_after_kg.scalar_one()
            article.article_metadata["knowledge_graph"] = kg_data
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(article, "article_metadata")
        except _asyncio.TimeoutError:
            logger.error(f"[ArticleService] KG Generation timed out (>25s) for {new_id_val} — skipping to protect DB pool.")
        except Exception as e:
            logger.error(f"[ArticleService] KG Generation failed for {new_id_val}: {e}")

        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        
        # Elite V2.2: Sync Media Links
        await self._sync_media_links(db_session, new_id_val, article)
        
        # SEO Pillar & Cluster: Emit ARTICLE_PUBLISHED on creation if published immediately
        if data.status and data.status.upper() == "PUBLISHED":
            await event_bus.emit("ARTICLE_PUBLISHED", {
                "entity_type": "article",
                "entity_id": str(new_id_val),
                "title": article.title,
                "excerpt": article.excerpt or "",
                "slug": article.slug,
                "tenant_id": current_tenant_id.get() or "default",
            })
            logger.info(f"[ArticleService] Emitted ARTICLE_PUBLISHED on creation for SEO matching: {new_id_val}")
            
        return SuccessResponse(ok=True, id=new_id_val)

    async def update_article(self, db_session: AsyncSession, article_id: str, data: UpdateArticleRequest) -> SuccessResponse:
        """Update an article and its embedding."""
        # Rule 1.5: Detail fetch for update (Surgical)
        stmt = select(Article).where(Article.id == article_id, Article.deleted_at == None)
        res = await db_session.execute(stmt)
        article = res.scalar_one_or_none()

        if not article:
            raise NotFoundException(f"Article {article_id} not found")

        # SEO: Track previous status to detect publish transition
        _prev_status = article.status

        if data.title is not None: article.title = data.title
        if data.slug is not None: article.slug = data.slug

        # SGE Shield V1.0: Lexical Sanitizer — tôn trọng flag admin
        sge_cfg = await _get_sge_config_async()
        lex_enabled = bool(sge_cfg.get("enabled", True)) and bool(sge_cfg.get("lexical_sanitizer_enabled", True))
        if data.excerpt is not None:
            pre_excerpt = sanitize_ai_text(data.excerpt, seed=f"{article.slug}:excerpt", enabled=lex_enabled)
            article.excerpt = await noise_cleaner.clean(pre_excerpt, strip_html=True)
        if data.content is not None:
            pre_content = sanitize_ai_text(data.content, seed=article.slug, enabled=lex_enabled)
            article.content = await noise_cleaner.clean(pre_content, strip_html=False)

        if data.seo_title is not None: article.seo_title = data.seo_title
        if data.seo_description is not None: article.seo_description = data.seo_description
        if data.seo_keywords is not None: article.seo_keywords = data.seo_keywords
        if data.seo_og_image is not None: article.seo_og_image = data.seo_og_image
        if data.status is not None: article.status = data.status.upper()
        if data.category is not None:
            article.category = data.category if isinstance(data.category, str) else data.category.value
        if data.featured_image is not None: article.featured_image = data.featured_image

        # GEO 2026: Merge metadata (FAQs etc.)
        if data.metadata is not None:
            existing_meta = article.article_metadata or {}
            new_meta = data.metadata.model_dump()
            article.article_metadata = {**existing_meta, **new_meta}
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(article, "article_metadata")

        # CNS V87.0: Analysis Report Merge
        if data.analysis_report is not None:
            existing_analysis = article.analysis_report or {}
            article.analysis_report = {**existing_analysis, **data.analysis_report}
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(article, "analysis_report")

        if data.title is not None or data.content is not None:
            await self.vector_service.upsert_article_embedding(
                db_session, article_id, article.title, article.content
            )

            # Elite V2.2: Re-generate Knowledge Graph on content change
            # [LEAK FIX] flush+expire_all để trả connection trước AI call,
            # rồi reload article sau khi AI xong để tiếp tục.
            _kg_content = article.content  # capture trước khi expire
            _kg_title = article.title
            await db_session.flush()
            db_session.expire_all()

            from backend.services.xohi.creative_studio.operatives.kg_generator import generate_knowledge_graph
            import asyncio as _asyncio
            try:
                async with _asyncio.timeout(25):
                    kg_data = await generate_knowledge_graph(
                        content=_kg_content,
                        topic=_kg_title
                    )
                # Reload sau khi AI xong để merge kết quả
                res_kg = await db_session.execute(select(Article).where(Article.id == article_id))
                article = res_kg.scalar_one()
                if not article.article_metadata:
                    article.article_metadata = {}
                article.article_metadata["knowledge_graph"] = kg_data
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(article, "article_metadata")
            except _asyncio.TimeoutError:
                logger.error(f"[ArticleService] KG Refresh timed out (>25s) for {article_id} — skipping to protect DB pool.")
            except Exception as e:
                logger.error(f"[ArticleService] KG Refresh failed for {article_id}: {e}")

        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()

        # Elite V2.2: Sync Media Links
        await self._sync_media_links(db_session, article_id, article)

        # SEO Pillar & Cluster: Emit ARTICLE_PUBLISHED when status transitions to PUBLISHED, or ARTICLE_UNPUBLISHED when status transitions away from PUBLISHED
        if data.status is not None:
            new_status = data.status.upper()
            if new_status == "PUBLISHED" and _prev_status != "PUBLISHED":
                await event_bus.emit("ARTICLE_PUBLISHED", {
                    "entity_type": "article",
                    "entity_id": str(article_id),
                    "title": article.title,
                    "excerpt": article.excerpt or "",
                    "slug": article.slug,
                    "tenant_id": current_tenant_id.get() or "default",
                })
                logger.info(f"[ArticleService] Emitted ARTICLE_PUBLISHED for SEO matching: {article_id}")
            elif new_status != "PUBLISHED" and _prev_status == "PUBLISHED":
                await event_bus.emit("ARTICLE_UNPUBLISHED", {
                    "entity_type": "article",
                    "entity_id": str(article_id),
                    "tenant_id": current_tenant_id.get() or "default",
                })
                logger.info(f"[ArticleService] Emitted ARTICLE_UNPUBLISHED for SEO matching: {article_id}")

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
        # Fetch status before soft delete to check if we need to emit UNPUBLISHED
        prev_status = await db_session.scalar(
            select(Article.status).where(Article.id == article_id, Article.deleted_at == None)
        )
        
        stmt = update(Article).where(Article.id == article_id).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        
        # SEO Pillar & Cluster: Emit ARTICLE_UNPUBLISHED if it was published
        if prev_status and prev_status.upper() == "PUBLISHED":
            await event_bus.emit("ARTICLE_UNPUBLISHED", {
                "entity_type": "article",
                "entity_id": str(article_id),
                "tenant_id": current_tenant_id.get() or "default",
            })
            logger.info(f"[ArticleService] Emitted ARTICLE_UNPUBLISHED on deletion for SEO: {article_id}")
            
        return SuccessResponse(ok=True, id=article_id)

    async def bulk_delete(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        # Fetch status before soft delete for those currently PUBLISHED
        published_ids = (await db_session.scalars(
            select(Article.id).where(
                Article.id.in_(ids),
                Article.status == "PUBLISHED",
                Article.deleted_at == None
            )
        )).all()
        
        stmt = update(Article).where(Article.id.in_(ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        
        # SEO Pillar & Cluster: Emit ARTICLE_UNPUBLISHED for each published article deleted
        tid = current_tenant_id.get() or "default"
        for art_id in published_ids:
            await event_bus.emit("ARTICLE_UNPUBLISHED", {
                "entity_type": "article",
                "entity_id": str(art_id),
                "tenant_id": tid,
            })
            logger.info(f"[ArticleService] Emitted ARTICLE_UNPUBLISHED on bulk deletion for SEO: {art_id}")
            
        return BulkActionResponse(ok=True, count=len(ids))

    async def bulk_publish(self, db_session: AsyncSession, ids: List[str]) -> BulkActionResponse:
        # Fetch titles/slugs before bulk update for SEO emit
        rows = (await db_session.execute(
            select(Article.id, Article.title, Article.slug, Article.excerpt)
            .where(Article.id.in_(ids), Article.deleted_at == None, Article.status != "PUBLISHED")
        )).all()
        stmt = update(Article).where(Article.id.in_(ids)).values(status="PUBLISHED")
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()
        # SEO Pillar & Cluster: emit for each newly published article
        tid = current_tenant_id.get() or "default"
        for row in rows:
            await event_bus.emit("ARTICLE_PUBLISHED", {
                "entity_type": "article",
                "entity_id": str(row.id),
                "title": row.title or "",
                "excerpt": row.excerpt or "",
                "slug": row.slug or "",
                "tenant_id": tid,
            })
        return BulkActionResponse(ok=True, count=len(ids))

    async def bulk_patch(
        self, db_session: AsyncSession, ids: List[str], status: Optional[str] = None, category: Optional[str] = None
    ) -> BulkActionResponse:
        values = {}
        if status: values["status"] = status.upper()
        if category: values["category"] = category
        
        if not values:
            return BulkActionResponse(ok=True, count=0)

        # SEO Pillar & Cluster event tracking
        published_emits = []
        unpublished_emits = []
        if status:
            target_status = status.upper()
            # Fetch previous status, titles, slugs, and excerpts
            rows = (await db_session.execute(
                select(Article.id, Article.status, Article.title, Article.slug, Article.excerpt)
                .where(Article.id.in_(ids), Article.deleted_at == None)
            )).all()
            
            for row in rows:
                if target_status == "PUBLISHED" and row.status != "PUBLISHED":
                    published_emits.append({
                        "entity_type": "article",
                        "entity_id": str(row.id),
                        "title": row.title or "",
                        "excerpt": row.excerpt or "",
                        "slug": row.slug or "",
                    })
                elif target_status != "PUBLISHED" and row.status == "PUBLISHED":
                    unpublished_emits.append({
                        "entity_type": "article",
                        "entity_id": str(row.id),
                    })
            
        stmt = update(Article).where(Article.id.in_(ids)).values(**values)
        await db_session.execute(stmt)
        # Invalidate Count Cache
        await xohi_memory.clear_article_cache()

        # Emit events
        tid = current_tenant_id.get() or "default"
        for payload in published_emits:
            payload["tenant_id"] = tid
            await event_bus.emit("ARTICLE_PUBLISHED", payload)
            logger.info(f"[ArticleService] Emitted ARTICLE_PUBLISHED on bulk patch for SEO: {payload['entity_id']}")
        for payload in unpublished_emits:
            payload["tenant_id"] = tid
            await event_bus.emit("ARTICLE_UNPUBLISHED", payload)
            logger.info(f"[ArticleService] Emitted ARTICLE_UNPUBLISHED on bulk patch for SEO: {payload['entity_id']}")
            
        return BulkActionResponse(ok=True, count=len(ids))

    async def suggest_seo(self, db_session: AsyncSession, title: str, content: str, product_id: str = "") -> Dict[str, str]:
        """GEO 2026: XOHI Auto SEO Suggestion for Articles."""
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        # SGE Shield V1.0: Dynamic Prompting — inject entropy với admin config
        base_seo_prompt = (
            "Bạn là chuyên gia SEO bài viết hàng đầu Việt Nam. Hãy gợi ý metadata SEO tối ưu cho bài báo này.\n"
            "Nếu có thông tin sản phẩm liên kết dưới đây, hãy đảm bảo các từ khóa SEO và mô tả SEO có liên quan trực tiếp đến sản phẩm đó để tăng tỉ lệ chuyển đổi.\n"
            "QUY TẮC TỐI CAO: Dù tiêu đề hoặc nội dung đầu vào là tiếng Anh, toàn bộ kết quả BẮT BUỘC phải là tiếng Việt thuần 100%.\n"
            "Yêu cầu:\n"
            "1. Tiêu đề SEO: Tối đa 60 ký tự, hấp dẫn, chuyên nghiệp.\n"
            "2. Mô tả SEO: Tối đa 160 ký tự, súc tích và lôi cuốn.\n"
            "3. Từ khóa: 5-7 từ khóa cách nhau bởi dấu phẩy.\n"
            "Chỉ trả về JSON hợp lệ: {\"seo_title\": \"...\", \"seo_description\": \"...\", \"seo_keywords\": \"...\"}"
        )
        sge_cfg_seo = await _get_sge_config_async()
        system_prompt = build_entropy_system_prompt(
            base_seo_prompt,
            tone_override=str(sge_cfg_seo["tone_override"]) if sge_cfg_seo.get("tone_override") else None,
            structure_override=str(sge_cfg_seo["structure_override"]) if sge_cfg_seo.get("structure_override") else None,
        ) if sge_cfg_seo.get("enabled", True) else base_seo_prompt

        agent = Agent(system_prompt=system_prompt)
        content_excerpt = (content or "")[:2000]

        _, product_context = await self._get_product_context(db_session, product_id)

        prompt_parts = []
        if product_context:
            prompt_parts.append(product_context)
        prompt_parts.append(f"Article Title: {title}")
        prompt_parts.append(f"Article Content: {content_excerpt}")
        prompt = "\n\n".join(prompt_parts)

        try:
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                role="fast",
                timeout=90.0
            )

            if result:
                suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r'\{.*\}', suggested_json_str, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, dict):
                        from backend.utils.text import validate_vietnamese_sentence
                        seo_title = parsed.get("seo_title", "")
                        seo_desc = parsed.get("seo_description", "")
                        seo_kw = parsed.get("seo_keywords", "")
                        
                        try:
                            seo_title = validate_vietnamese_sentence(seo_title, mode="light")
                        except Exception as ve:
                            logger.warning(f"[ArticleService] SEO Title validation failed: {ve}")
                        
                        try:
                            seo_desc = validate_vietnamese_sentence(seo_desc, mode="standard")
                        except Exception as ve:
                            logger.warning(f"[ArticleService] SEO Description validation failed: {ve}")
                            
                        return {
                            "seo_title": seo_title,
                            "seo_description": seo_desc,
                            "seo_keywords": seo_kw,
                        }

            return {"seo_title": "", "seo_description": "", "seo_keywords": ""}

        except Exception as e:
            logger.exception(f"[ArticleService] AI SEO Suggestion Failed: {e}")
            return {"seo_title": "", "seo_description": "", "seo_keywords": ""}

    async def suggest_faqs(self, db_session: AsyncSession, title: str, content: str, product_id: str = "") -> List[Dict[str, str]]:
        """GEO 2026: XOHI Auto FAQ Generator for Articles."""
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        # SGE Shield V1.0: Dynamic Prompting — inject entropy vào system prompt
        base_faq_prompt = (
            "Bạn là chuyên gia cố vấn nội dung và SEO chuyên tối ưu hóa dữ liệu Hỏi & Đáp (Q&A Blocks) đáp ứng tiêu chuẩn hiển thị của Google SGE và AI Overviews.\n"
            "Dựa trên tiêu đề, nội dung bài viết và sản phẩm liên kết (nếu có), hãy tạo từ 3 đến 5 câu hỏi thường gặp và câu trả lời ngắn gọn, hữu ích bằng tiếng Việt.\n"
            "Nếu có sản phẩm liên kết dưới đây, hãy đảm bảo có ít nhất 1-2 câu hỏi/trả lời đề cập trực tiếp hoặc gián tiếp đến sản phẩm liên kết đó (ví dụ cách sử dụng sản phẩm này cho vấn đề nêu trong bài viết).\n\n"
            "YÊU CẦU CHO CÂU HỎI SGE/AI OVERVIEWS:\n"
            "1. Tiêu đề câu hỏi (question) bắt buộc phải viết dưới dạng các câu hỏi tìm kiếm tự nhiên của người dùng, sử dụng các từ nghi vấn như: 'Là gì', 'Làm thế nào', 'Có tác dụng gì', 'Tại sao', 'Có tốt không', 'Cách thực hiện', 'Cách dùng'.\n"
            "2. Tránh các câu hỏi chung chung. Câu hỏi phải bám sát từ khóa cốt lõi của bài viết để phục vụ truy vấn tìm kiếm.\n"
            "3. Câu trả lời (answer) phải ngắn gọn, súc tích (dưới 80 từ), chính xác và đi thẳng vào trọng tâm câu hỏi.\n"
            "4. QUY TẮC TỐI CAO: Bất kể ngôn ngữ đầu vào là gì, đầu ra phải là tiếng Việt thuần 100%.\n"
            "5. Chỉ trả về mảng JSON chính xác các đối tượng, không có markdown:\n"
            "[{\"question\": \"...\", \"answer\": \"...\"}]"
        )
        sge_cfg_faq = await _get_sge_config_async()
        system_prompt = build_entropy_system_prompt(
            base_faq_prompt,
            tone_override=str(sge_cfg_faq["tone_override"]) if sge_cfg_faq.get("tone_override") else None,
            structure_override=str(sge_cfg_faq["structure_override"]) if sge_cfg_faq.get("structure_override") else None,
        ) if sge_cfg_faq.get("enabled", True) else base_faq_prompt

        agent = Agent(system_prompt=system_prompt)
        # Truncate content to first 2000 chars for prompt efficiency
        content_excerpt = (content or "")[:2000]

        _, product_context = await self._get_product_context(db_session, product_id)

        prompt_parts = []
        if product_context:
            prompt_parts.append(product_context)
        prompt_parts.append(f"Article Title: {title}")
        prompt_parts.append(f"Article Content: {content_excerpt}")
        prompt = "\n\n".join(prompt_parts)

        try:
            result = await trinity_bridge.run(
                agent=agent,
                prompt=prompt,
                role="fast",
                timeout=90.0
            )

            if result:
                suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r'\[.*\]', suggested_json_str, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list):
                        from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
                        validated_faqs = []
                        for faq in parsed:
                            if isinstance(faq, dict) and "question" in faq and "answer" in faq:
                                q = str(faq["question"]).strip()
                                a = str(faq["answer"]).strip()
                                try:
                                    q = validate_vietnamese_sentence(q, mode="light")
                                except Exception as ve:
                                    logger.warning(f"[ArticleService] FAQ Question validation failed: {ve}")
                                try:
                                    a = sanitize_sentence_linebreaks(a)
                                    a = validate_vietnamese_sentence(a, mode="standard")
                                except Exception as ve:
                                    logger.warning(f"[ArticleService] FAQ Answer validation failed: {ve}")
                                validated_faqs.append({"question": q, "answer": a})
                        return validated_faqs

            return []

        except Exception as e:
            logger.exception(f"[ArticleService] AI FAQ Suggestion Failed: {e}")
            return []

    async def suggest_excerpt(self, db_session: AsyncSession, title: str, category: str, content: str = "", product_id: str = "") -> str:
        """GEO 2026: XOHI Auto Excerpt Generator — sinh tóm tắt 1-2 câu theo tiêu đề và nội dung."""
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        base_prompt = (
            "Bạn là chuyên gia viết tóm tắt bài báo tiếng Việt.\n"
            "Nếu có thông tin sản phẩm liên kết dưới đây, hãy đảm bảo tóm tắt đề cập hoặc dẫn dắt khéo léo liên quan tới sản phẩm đó.\n"
            "QUY TẮC TỐI CAO:\n"
            "1. Dù tiêu đề hay nội dung đầu vào là tiếng Anh, bạn BẮT BUỘC phải viết tóm tắt hoàn toàn bằng tiếng Việt thuần 100%.\n"
            "2. Các câu bắt buộc phải là một câu hoàn chỉnh về mặt ngữ nghĩa (Có đầy đủ chủ ngữ + vị ngữ).\n"
            "3. Tuyệt đối không được ngắt dòng khi chưa viết hết câu.\n"
            "4. Hãy chủ động viết ngắn gọn ngay từ đầu. Độ dài tóm tắt không được vượt quá 250 ký tự để đảm bảo tính súc tích và tránh bị cắt cụt.\n"
            "5. Dựa vào tiêu đề, chuyên mục, sản phẩm liên kết (nếu có) và nội dung bài viết (nếu có), hãy viết 1-2 câu tóm tắt súc tích, hấp dẫn, chứa từ khóa chính.\n"
            "6. Chỉ trả về đoạn văn thuần túy (paragraph), KHÔNG dùng markdown, KHÔNG ghi danh sách (ví dụ: không viết dạng '1. ...', '2. ...' hoặc dùng dấu gạch đầu dòng), KHÔNG giải thích thêm."
        )
        sge_cfg = await _get_sge_config_async()
        system_prompt = build_entropy_system_prompt(
            base_prompt,
            tone_override=str(sge_cfg["tone_override"]) if sge_cfg.get("tone_override") else None,
            structure_override=str(sge_cfg["structure_override"]) if sge_cfg.get("structure_override") else None,
        ) if sge_cfg.get("enabled", True) else base_prompt

        agent = Agent(system_prompt=system_prompt)
        
        _, product_context = await self._get_product_context(db_session, product_id)
        
        prompt_parts = []
        if product_context:
            prompt_parts.append(product_context)
        prompt_parts.append(f"Tiêu đề: {title}")
        prompt_parts.append(f"Chuyên mục: {category or 'Chung'}")
        if content:
            prompt_parts.append(f"Nội dung bài viết: {content[:1500]}")
            
        prompt = "\n\n".join(prompt_parts)

        try:
            result = await trinity_bridge.run(agent=agent, prompt=prompt, role="fast", timeout=60.0)
            if result:
                text = str(getattr(result, "data", getattr(result, "output", result))).strip()
                
                # Loại bỏ hoàn toàn các ký tự xuống dòng dư thừa trong tóm tắt
                text = re.sub(r'[\r\n]+', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Cắt gọn an toàn đến câu hoàn chỉnh cuối cùng nếu vượt quá 300 ký tự
                if len(text) > 300:
                    matches = list(re.finditer(r'[.!?](?:\s|$)', text[:300]))
                    if matches:
                        text = text[:matches[-1].end()].strip()
                    else:
                        space_idx = text[:300].rfind(' ')
                        if space_idx > 0:
                            text = text[:space_idx].strip()
                        else:
                            text = text[:300].strip()

                from backend.utils.text import validate_vietnamese_sentence
                try:
                    text = validate_vietnamese_sentence(text, mode="standard")
                except Exception as ve:
                    logger.warning(f"[ArticleService] Excerpt validation failed: {ve}")
                return text
            return ""
        except Exception as e:
            logger.exception(f"[ArticleService] AI Excerpt Suggestion Failed: {e}")
            return ""

    async def suggest_content(self, db_session: AsyncSession, title: str, category: str, excerpt: str, product_id: str = "") -> str:
        """GEO 2026: XOHI Auto Content Generator — sinh HTML bài viết hoàn chỉnh EEAT."""
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        base_prompt = (
            "Bạn là nhà báo/chuyên gia nội dung EEAT tiêu chuẩn 2026.\n"
            "Nếu có thông tin sản phẩm liên kết dưới đây, bạn BẮT BUỘC phải lồng ghép sản phẩm liên quan này vào bài viết một cách tự nhiên, chuyên nghiệp và có sức thuyết phục cao. Giải thích rõ tại sao sản phẩm này là giải pháp tốt cho vấn đề được thảo luận trong bài viết.\n"
            "QUY TẮC TỐI CAO: Dù tiêu đề hoặc tóm tắt đầu vào là tiếng Anh, bạn BẮT BUỘC phải viết bài hoàn toàn bằng tiếng Việt thuần 100%.\n"
            "Viết bài viết HTML hoàn chỉnh bằng tiếng Việt dựa trên tiêu đề, chuyên mục, tóm tắt và sản phẩm liên kết được cung cấp.\n"
            "Yêu cầu cấu trúc:\n"
            "- Dùng <h2> cho các luận điểm chính (chứa từ khóa), <h3> cho luận điểm phụ.\n"
            "- Dùng <p>, <ul>, <li>, <strong> để làm phong phú nội dung.\n"
            "- Viết tối thiểu 600 từ, chia đều thành 3-5 phần logic.\n"
            "- TUYỆT ĐỐI không dùng Markdown. Không JSON. Chỉ HTML thuần.\n"
            "- Không có <!DOCTYPE>, <html>, <head>, <body> — chỉ nội dung bài viết."
        )
        sge_cfg = await _get_sge_config_async()
        system_prompt = build_entropy_system_prompt(
            base_prompt,
            tone_override=str(sge_cfg["tone_override"]) if sge_cfg.get("tone_override") else None,
            structure_override=str(sge_cfg["structure_override"]) if sge_cfg.get("structure_override") else None,
        ) if sge_cfg.get("enabled", True) else base_prompt

        agent = Agent(system_prompt=system_prompt, output_type=str, retries=2)
        
        _, product_context = await self._get_product_context(db_session, product_id)
        
        prompt_parts = []
        if product_context:
            prompt_parts.append(product_context)
        prompt_parts.append(f"Tiêu đề: {title}")
        prompt_parts.append(f"Chuyên mục: {category or 'Chung'}")
        prompt_parts.append(f"Tóm tắt: {excerpt or ''}")
        
        prompt = "\n\n".join(prompt_parts)

        try:
            result = await trinity_bridge.run(
                agent=agent, prompt=prompt, role="fast", timeout=120.0,
                model_settings={"max_tokens": 8192}
            )
            if result:
                raw = str(getattr(result, "data", getattr(result, "output", result))).strip()
                from backend.utils.noise_cleaner import noise_cleaner
                cleaned = await noise_cleaner.clean(raw, strip_html=False)
                from backend.utils.text import validate_vietnamese_text_block
                try:
                    cleaned = validate_vietnamese_text_block(cleaned)
                except Exception as ve:
                    logger.warning(f"[ArticleService] Content validation warning: {ve}")
                return cleaned
            return ""
        except Exception as e:
            logger.exception(f"[ArticleService] AI Content Generation Failed: {e}")
            return ""

    async def suggest_titles(
        self,
        db_session: AsyncSession,
        category: str,
        keywords: str,
        product_id: str,
    ) -> Dict[str, List[str]]:
        """V2026: XOHI Title Generator — sinh tiêu đề chia theo 3 nhóm dựa trên Top 10 + context sản phẩm."""
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
        from backend.services.xohi.google_search import google_search_service
        from backend.database.models import ProductBase

        # 1. Fetch product context nếu có
        product_context = ""
        product_name = ""
        
        # Chuẩn hóa và làm sạch product_id đầu vào
        if product_id:
            product_id = product_id.strip()
            if product_id.lower() in ("null", "undefined", ""):
                product_id = ""

        if product_id:
            try:
                prod_stmt = select(
                    ProductBase.name, ProductBase.seo_keywords, ProductBase.short_description
                ).where(ProductBase.id == product_id, ProductBase.deleted_at == None)
                prod_row = (await db_session.execute(prod_stmt)).first()
                if prod_row:
                    product_name = prod_row.name
                    product_context = (
                        f"Sản phẩm liên quan: {prod_row.name}\n"
                        f"Từ khóa SP: {prod_row.seo_keywords or ''}\n"
                        f"Mô tả SP: {(prod_row.short_description or '')[:200]}"
                    )
            except Exception as e:
                logger.exception(f"[ArticleService] Lỗi khi truy vấn thông tin sản phẩm {product_id}: {e}")

        # 2. Google Search top 10 — tìm trend và tiêu đề đang rank
        search_query = f"{category} {keywords}".strip() or category or "bài viết"
        if product_name:
            search_query = f"{product_name} {search_query}"
        top10_context = ""
        try:
            search_results = await google_search_service.search(search_query, num=10)
            if search_results:
                titles_snippets = [
                    f"- {r.get('title', '')} | {r.get('snippet', '')[:100]}"
                    for r in search_results[:10]
                ]
                top10_context = "TOP 10 TIÊU ĐỀ ĐANG RANK TRÊN GOOGLE (TRÁNH TRÙNG LẶP HOÀN TOÀN):\n" + "\n".join(titles_snippets)
        except Exception as e:
            logger.warning(f"[ArticleService] Google Search for title-suggest failed: {e}")

        # 2.5. Fetch existing articles in database to prevent internal duplicates
        db_context = ""
        try:
            db_stmt = select(Article.title).where(
                Article.deleted_at == None
            ).order_by(Article.created_at.desc()).limit(30)
            db_rows = (await db_session.execute(db_stmt)).scalars().all()
            if db_rows:
                db_context = "DANH SÁCH TIÊU ĐỀ ĐÃ TỒN TẠI TRONG CƠ SỞ DỮ LIỆU HỆ THỐNG (BẮT BUỘC TRÁNH TRÙNG LẶP):\n" + "\n".join(f"- {title}" for title in db_rows)
        except Exception as e:
            logger.warning(f"[ArticleService] Fetching DB titles for suggestion failed: {e}")

        # 3. Build prompt
        base_prompt = (
            "Bạn là chuyên gia viết tiêu đề bài viết SEO hàng đầu Việt Nam, chuyên tối ưu cho Google SGE 2026.\n\n"
            "PHÂN TÍCH ĐẦU VÀO:\n"
            "- Top 10 tiêu đề đang rank trên mạng xã hội/Google cho chủ đề này (được cung cấp dưới đây)\n"
            "- Các tiêu đề đã tồn tại trong cơ sở dữ liệu nội bộ của hệ thống (được cung cấp dưới đây)\n"
            "- Thông tin sản phẩm liên quan (nếu có)\n"
            "- Từ khóa SEO mục tiêu\n\n"
            "YÊU CẦU QUAN TRỌNG VỀ TÍNH DUY NHẤT & CHẤT LƯỢNG:\n"
            "1. Các tiêu đề được sinh ra PHẢI là duy nhất, tuyệt đối KHÔNG trùng lặp hoàn toàn hoặc quá giống với bất kỳ tiêu đề nào trong danh sách Top 10 Google hoặc danh sách tiêu đề hệ thống đã có.\n"
            "2. Tiêu đề phải chuẩn SGE (trả lời trực tiếp ý định tìm kiếm của người dùng, giàu thông tin thực tế) và chuẩn SEO (chứa từ khóa chính ở vị trí dễ nhìn để thu hút CTR).\n\n"
            "Hãy sinh tổng cộng 9 tiêu đề hấp dẫn, chia thành 3 nhóm rõ rệt (mỗi nhóm đúng 3 tiêu đề):\n"
            "1. Nhóm 'seo_sge': Tập trung vào tối ưu hóa SEO và Google SGE, bắt buộc phải chứa tên sản phẩm liên quan (nếu có). Nếu không có tên sản phẩm cụ thể, dùng từ khóa SEO chính.\n"
            "2. Nhóm 'guide_advanced': Các tiêu đề dạng hướng dẫn sử dụng, mẹo hay, kinh nghiệm thực tế, cách làm nâng cao nhằm giải quyết bài toán của người dùng.\n"
            "3. Nhóm 'related_keywords': Tận dụng các từ khóa phụ liên quan, chủ đề mở rộng xung quanh để tăng tối đa độ bao phủ chủ đề (coverage).\n\n"
            "Mỗi tiêu đề dài từ 50-65 ký tự, tự nhiên, không clickbait rẻ tiền.\n"
            "QUY TẮC TỐI CAO: Dù dữ liệu đầu vào là tiếng Anh, toàn bộ kết quả BẮT BUỘC phải là tiếng Việt thuần 100%.\n"
            "Chỉ trả về định dạng JSON hợp lệ duy nhất sau:\n"
            "{\n"
            "  \"seo_sge\": [\"tiêu đề 1\", \"tiêu đề 2\", \"tiêu đề 3\"],\n"
            "  \"guide_advanced\": [\"tiêu đề 1\", \"tiêu đề 2\", \"tiêu đề 3\"],\n"
            "  \"related_keywords\": [\"tiêu đề 1\", \"tiêu đề 2\", \"tiêu đề 3\"]\n"
            "}"
        )

        sge_cfg = await _get_sge_config_async()
        system_prompt = build_entropy_system_prompt(
            base_prompt,
            tone_override=str(sge_cfg["tone_override"]) if sge_cfg.get("tone_override") else None,
            structure_override=str(sge_cfg["structure_override"]) if sge_cfg.get("structure_override") else None,
        ) if sge_cfg.get("enabled", True) else base_prompt

        agent = Agent(system_prompt=system_prompt)
        prompt_parts = [f"Chuyên mục: {category or 'Chung'}"]
        if keywords:
            prompt_parts.append(f"Từ khóa SEO: {keywords}")
        if product_context:
            prompt_parts.append(product_context)
        if top10_context:
            prompt_parts.append(top10_context)
        if db_context:
            prompt_parts.append(db_context)

        prompt = "\n\n".join(prompt_parts)

        fallback: Dict[str, List[str]] = {
            "seo_sge": [],
            "guide_advanced": [],
            "related_keywords": []
        }

        try:
            result = await trinity_bridge.run(
                agent=agent, prompt=prompt, role="fast", timeout=90.0
            )
            if result:
                raw = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, dict):
                        from backend.utils.text import validate_vietnamese_sentence
                        validated_res = {"seo_sge": [], "guide_advanced": [], "related_keywords": []}
                        for key in ["seo_sge", "guide_advanced", "related_keywords"]:
                            for t in parsed.get(key, []):
                                if isinstance(t, str) and t.strip():
                                    try:
                                        clean_t = validate_vietnamese_sentence(t.strip(), mode="light")
                                        validated_res[key].append(clean_t)
                                    except Exception as ve:
                                        logger.warning(f"[ArticleService] Title validation failed for '{t}': {ve}")
                        return {k: v[:3] for k, v in validated_res.items()}
            return fallback
        except Exception as e:
            logger.exception(f"[ArticleService] AI Title Suggestion Failed: {e}")
            return fallback

# ==========================================
# SERVICE PROVIDERS (V76.2 DI PATTERN)
# ==========================================

async def provide_article_service(vector_service: ArticleVectorService) -> ArticleService:
    """Standard Litestar Provider for ArticleService."""
    return ArticleService(vector_service=vector_service)

