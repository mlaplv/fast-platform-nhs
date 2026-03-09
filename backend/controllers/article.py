import re
import time
import uuid
import logging
from datetime import datetime, timezone
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from typing import List, Dict, Union, Optional
from sqlalchemy import text, update, select
from sqlalchemy.orm import selectinload

from backend.database.repositories import ArticleRepository, provide_article_repo
from backend.database.models import Article
from backend.guards import PermissionGuard
from backend.utils.sql import escape_like
from backend.schemas.article import CreateArticleRequest, UpdateArticleRequest, BulkIdsRequest

logger = logging.getLogger("api-gateway")

class ArticleController(Controller):
    """R2: Class-based Litestar Controller for Article/News CRUD."""
    path = "/api/v1/articles"
    dependencies = {"art_repo": Provide(provide_article_repo)}

    @get("/", guards=[PermissionGuard("content:read")])
    async def list_articles(
        self, art_repo: ArticleRepository, 
        limit: int = 20, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, object]:
        """List articles with server-side pagination. R41: N+1 Safe. R1.5: Zero-Hydration COUNT."""
        from sqlalchemy import func, and_, or_
        
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

        # 1. COUNT Cache Redis Optimization (Scout Rule R01.1)
        from backend.services.xohi_memory import xohi_memory
        
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
            total = await art_repo.session.scalar(count_stmt) or 0
            
            if xohi_memory._use_redis:
                try:
                    await xohi_memory.client.set(cache_key, str(total), ex=300) # 5-min TTL
                except Exception:
                    pass

        # 2. Paginated fetch with eager loading
        stmt = select(Article).where(and_(*conditions)).options(
            selectinload(Article.author)
        ).limit(limit).offset(offset).order_by(Article.created_at.desc())
        
        result = await art_repo.session.execute(stmt)
        articles = result.scalars().all()
        
        data = [
            {
                "id": str(a.id),
                "title": a.title,
                "slug": a.slug,
                "excerpt": a.excerpt,
                "status": a.status.lower() if a.status else "draft",
                "category": a.category,
                "views": a.views,
                "author": a.author.name if a.author else "System",
                "authorId": str(a.author_id) if a.author_id else None,
                "createdAt": a.created_at.strftime("%Y-%m-%d") if a.created_at else "",
            }
            for a in articles
        ]
        return {"data": data, "total": total}

    @get("/{article_id:str}", guards=[PermissionGuard("content:read")])
    async def get_article(self, art_repo: ArticleRepository, article_id: str) -> Dict[str, object]:
        """Get a single article using repository."""
        from litestar.exceptions import NotFoundException
        try:
            article = await art_repo.get(article_id)
        except Exception:
            raise NotFoundException(f"Article {article_id} not found")
            
        return {
            "id": str(article.id),
            "title": article.title,
            "slug": article.slug,
            "excerpt": article.excerpt,
            "content": article.content,
            "seo_title": article.seo_title,
            "seo_description": article.seo_description,
            "status": article.status.lower() if article.status else "draft",
            "category": article.category,
            "views": article.views,
        }

    @post("/", guards=[PermissionGuard("content:write")])
    async def create_article(self, art_repo: ArticleRepository, data: CreateArticleRequest) -> Dict[str, object]:
        """Create a new article using repository."""
        slug = data.slug or re.sub(
            r'[^a-z0-9]+', '-',
            data.title.lower()
                .replace("đ", "d")
                .replace("ă", "a").replace("â", "a")
                .replace("ê", "e").replace("ô", "o")
                .replace("ơ", "o").replace("ư", "u")
        ).strip("-") + f"-{int(time.time())}"

        new_id = str(uuid.uuid4())
        article = Article(
            id=new_id,
            title=data.title,
            slug=slug,
            excerpt=data.excerpt,
            content=data.content,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            status=data.status.upper(),
            category=data.category,
            author_id=data.authorId,
        )
        await art_repo.add(article)
        
        # RAG: Generate embedding using repo session
        await self._upsert_embedding(art_repo, new_id, data.title, data.content)
        
        await art_repo.session.commit()
        
        return {
            "id": new_id,
            "title": article.title,
            "slug": article.slug,
            "excerpt": article.excerpt,
            "status": article.status.lower(),
            "category": article.category,
            "views": article.views,
            "author": "Admin",
            "createdAt": article.created_at.strftime("%Y-%m-%d") if article.created_at else "",
        }

    @patch("/{article_id:str}", guards=[PermissionGuard("content:write")])
    async def update_article(self, art_repo: ArticleRepository, article_id: str, data: UpdateArticleRequest) -> Dict[str, object]:
        """Update an article using repository."""
        article = await art_repo.get(article_id)
        
        if data.title is not None: article.title = data.title
        if data.slug is not None: article.slug = data.slug
        if data.excerpt is not None: article.excerpt = data.excerpt
        if data.content is not None: article.content = data.content
        if data.seo_title is not None: article.seo_title = data.seo_title
        if data.seo_description is not None: article.seo_description = data.seo_description
        if data.status is not None: article.status = data.status.upper()
        if data.category is not None: article.category = data.category

        # RAG: Update embedding
        if data.title is not None or data.content is not None:
            await self._upsert_embedding(art_repo, article_id, article.title, article.content)
            
        await art_repo.session.commit()
        
        return {
            "id": str(article.id),
            "title": article.title,
            "status": article.status.lower(),
            "category": article.category,
        }

    @delete("/{article_id:str}", status_code=200, guards=[PermissionGuard("content:write")])
    async def delete_article(self, art_repo: ArticleRepository, article_id: str) -> dict:
        """R18: Soft delete using repository."""
        stmt = update(Article).where(Article.id == article_id).values(deleted_at=datetime.now(timezone.utc))
        await art_repo.session.execute(stmt)
        await art_repo.session.commit()
        return {"ok": True, "id": article_id}

    @post("/bulk-delete", guards=[PermissionGuard("content:write")])
    async def bulk_delete(self, art_repo: ArticleRepository, data: BulkIdsRequest) -> dict:
        """R18: Soft delete multiple articles using repository."""
        stmt = update(Article).where(Article.id.in_(data.ids)).values(deleted_at=datetime.now(timezone.utc))
        await art_repo.session.execute(stmt)
        await art_repo.session.commit()
        return {"ok": True, "deleted": len(data.ids)}

    @post("/bulk-publish", guards=[PermissionGuard("content:publish")])
    async def bulk_publish(self, art_repo: ArticleRepository, data: BulkIdsRequest) -> dict:
        """Publish multiple articles using repository."""
        stmt = update(Article).where(Article.id.in_(data.ids)).values(status="PUBLISHED")
        await art_repo.session.execute(stmt)
        await art_repo.session.commit()
        return {"ok": True, "published": len(data.ids)}

    async def _upsert_embedding(self, art_repo: ArticleRepository, article_id: str, title: str, content: Optional[str]) -> None:
        """Helper to generate and store pgvector embedding using repo session."""
        try:
            from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
            import asyncio
            
            # Rule 1.10 Encoder Singleton Fix (V56.0)
            encoder = get_shared_encoder()
            if not encoder:
                logger.warning("[RAG] Shared encoder not ready, skipping embedding")
                return
            
            text_to_embed = f"{title}\n{content or ''}".strip()
            
            def _embed_sync():
                # list() is required to force generator evaluation
                return list(encoder.embed([text_to_embed]))
                
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(None, _embed_sync)
            
            if not embeddings:
                return
                
            vector = embeddings[0].tolist()
            vector_str = "[" + ",".join(map(str, vector)) + "]"
            
            from backend.database import current_tenant_id
            tenant = current_tenant_id.get() or "default"
            
            # Rule R1.5/R2.2: Ensure execute context stays clean
            sql = text("""
                INSERT INTO article_embeddings (id, article_id, embedding, created_at, updated_at, tenant_id)
                VALUES (:id, :article_id, :vector::vector, NOW(), NOW(), :tenant_id)
                ON CONFLICT (article_id) 
                DO UPDATE SET embedding = :vector::vector, updated_at = NOW();
            """)
            await art_repo.session.execute(sql, {
                "id": str(uuid.uuid4()), 
                "article_id": article_id, 
                "vector": vector_str,
                "tenant_id": tenant
            })
        except Exception as e:
            logger.error(f"[RAG] Article embedding failed for {article_id}: {e}")
