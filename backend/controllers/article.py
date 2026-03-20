from __future__ import annotations
import logging
from typing import List, Dict, Union, Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories import ArticleRepository, provide_article_repo
from backend.guards import PermissionGuard
from backend.schemas.common import SuccessResponse, BulkActionResponse, BulkIdsRequest
from backend.schemas.article import (
    ArticleResponse, ArticleListResponse, CreateArticleRequest,
    UpdateArticleRequest
)
from backend.services.article_service import article_service

logger = logging.getLogger("api-gateway")

class ArticleController(Controller):
    """R2: Class-based Litestar Controller for Article/News CRUD."""
    path = "/api/v1/articles"
    dependencies = {"art_repo": Provide(provide_article_repo)}

    @get("/", guards=[PermissionGuard("content:read")])
    async def list_articles(
        self, db_session: "AsyncSession",
        limit: int = 20, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> ArticleListResponse:
        """List articles with server-side pagination. R41: N+1 Safe. R1.5: Zero-Hydration."""
        return await article_service.list_articles(db_session, limit, offset, status, search, category)

    @get("/{article_id:str}", guards=[PermissionGuard("content:read")])
    async def get_article(self, db_session: "AsyncSession", article_id: str) -> ArticleResponse:
        """Get a single article (R76: Scalar Projection)."""
        return await article_service.get_article(db_session, article_id)

    @post("/", guards=[PermissionGuard("content:write")])
    async def create_article(self, db_session: "AsyncSession", data: CreateArticleRequest) -> SuccessResponse:
        """Create a new article (Service-Centric RAG)."""
        res = await article_service.create_article(db_session, data)
        await db_session.commit()
        return res

    @patch("/{article_id:str}", guards=[PermissionGuard("content:write")])
    async def update_article(self, db_session: "AsyncSession", article_id: str, data: UpdateArticleRequest) -> SuccessResponse:
        """Update an article (Service-Centric RAG)."""
        res = await article_service.update_article(db_session, article_id, data)
        await db_session.commit()
        return res

    @delete("/{article_id:str}", status_code=200, guards=[PermissionGuard("content:write")])
    async def delete_article(self, db_session: "AsyncSession", article_id: str) -> SuccessResponse:
        """R18: Soft delete."""
        res = await article_service.delete_article(db_session, article_id)
        await db_session.commit()
        return res

    @post("/bulk-delete", guards=[PermissionGuard("content:write")])
    async def bulk_delete(self, db_session: "AsyncSession", data: BulkIdsRequest) -> BulkActionResponse:
        """R18: Soft delete multiple articles."""
        res = await article_service.bulk_delete(db_session, data.ids)
        await db_session.commit()
        return res

    @post("/bulk-publish", guards=[PermissionGuard("content:publish")])
    async def bulk_publish(self, db_session: "AsyncSession", data: BulkIdsRequest) -> BulkActionResponse:
        """Publish multiple articles."""
        res = await article_service.bulk_publish(db_session, data.ids)
        await db_session.commit()
        return res

    @patch("/bulk-update", guards=[PermissionGuard("content:write")])
    async def bulk_patch(self, db_session: "AsyncSession", data: "Any") -> BulkActionResponse:
        """Bulk update status or category."""
        from backend.schemas.article import BulkPatchRequest
        # Cast for type safety in logic if needed, but here simple access is fine
        res = await article_service.bulk_patch(db_session, data.ids, data.status, data.category)
        await db_session.commit()
        return res
