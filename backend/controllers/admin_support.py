from __future__ import annotations
import logging
from typing import Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repositories import provide_support_kb_repo
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.support import (
    CreateSupportKnowledgeRequest,
    UpdateSupportKnowledgeRequest, 
    SupportKnowledgeResponse, 
    SupportKnowledgeListResponse,
    BulkDeleteRequest,
    BulkToggleRequest,
    SupportKnowledgeCategory
)
from backend.schemas.common import SuccessResponse
from backend.services.commerce.support_knowledge import SupportKnowledgeService, provide_support_kb_service

logger = logging.getLogger("api-gateway")

class AdminSupportController(Controller):
    """Elite V2.2: Admin Controller for Support Knowledge Base management."""
    path = "/api/v1/admin/support/knowledge"
    guards = [PermissionGuard(PermissionEnum.PRODUCT_WRITE)] # Reuse product write for now or define SUPPORT_WRITE
    dependencies = {
        "kb_service": Provide(provide_support_kb_service),
        "kb_repo": Provide(provide_support_kb_repo),
    }

    @get("/")
    async def list_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        limit: int = 20,
        offset: int = 0,
        category: Optional[SupportKnowledgeCategory] = None,
        search: Optional[str] = None,
    ) -> SupportKnowledgeListResponse:
        return await kb_service.list_knowledge(
            db_session=db_session, 
            limit=limit, 
            offset=offset, 
            category=category, 
            search=search
        )

    @get("/{item_id:str}")
    async def get_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        item_id: str
    ) -> SupportKnowledgeResponse:
        return await kb_service.get_knowledge(db_session, item_id)

    @post("/")
    async def create_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        data: CreateSupportKnowledgeRequest
    ) -> SuccessResponse:
        res = await kb_service.create_knowledge(db_session, data)
        await db_session.commit()
        return res

    @patch("/{item_id:str}")
    async def update_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        item_id: str,
        data: UpdateSupportKnowledgeRequest
    ) -> SuccessResponse:
        res = await kb_service.update_knowledge(db_session, item_id, data)
        await db_session.commit()
        return res

    @delete("/{item_id:str}", status_code=200)
    async def delete_knowledge(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        item_id: str
    ) -> SuccessResponse:
        res = await kb_service.delete_knowledge(db_session, item_id)
        await db_session.commit()
        return res

    @post("/bulk-delete")
    async def bulk_delete(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        data: BulkDeleteRequest
    ) -> SuccessResponse:
        res = await kb_service.bulk_delete(db_session, data)
        await db_session.commit()
        return res

    @post("/bulk-toggle")
    async def bulk_toggle(
        self,
        db_session: AsyncSession,
        kb_service: SupportKnowledgeService,
        data: BulkToggleRequest
    ) -> SuccessResponse:
        res = await kb_service.bulk_toggle_active(db_session, data)
        await db_session.commit()
        return res
