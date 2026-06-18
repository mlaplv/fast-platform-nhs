from __future__ import annotations
from typing import List, Dict, Union, Optional
import logging
from litestar import Controller, get, patch, post, Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update, func

from backend.services.notification_service import notification_service
from backend.schemas.notification import NotificationResponse, NotificationListResponse, NotificationCursorPaginatedResponse
from backend.schemas.common import SuccessResponse
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

class NotificationController(Controller):
    path = "/api/v1/notifications"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    @get("/")
    async def get_notifications(self, db_session: "AsyncSession", request: Request) -> NotificationListResponse:
        """Lấy danh sách thông báo của user hiện tại"""
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")
        user_roles = user_state.get("roles", [])
        return await notification_service.get_notifications(db_session, user_id, user_roles)

    @get("/paginated")
    async def get_notifications_paginated(
        self,
        db_session: "AsyncSession",
        request: Request,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> NotificationCursorPaginatedResponse:
        """Lấy danh sách thông báo sử dụng phân trang cursor pagination"""
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")
        user_roles = user_state.get("roles", [])
        return await notification_service.get_notifications_paginated(db_session, user_id, user_roles, cursor, limit)

    @patch("/{notification_id:str}/read")
    async def mark_as_read(self, db_session: "AsyncSession", notification_id: str) -> SuccessResponse:
        """Đánh dấu thông báo đã đọc"""
        res = await notification_service.mark_as_read(db_session, notification_id)
        await db_session.commit()
        return res

    @post("/bulk-delete")
    async def bulk_delete(self, db_session: "AsyncSession", data: dict) -> SuccessResponse:
        """Xoá mềm hàng loạt thông báo"""
        ids = data.get("ids", [])
        if not ids:
            return SuccessResponse(ok=True)
        res = await notification_service.bulk_delete(db_session, ids)
        await db_session.commit()
        return res

    @post("/clear")
    async def clear_notifications(self, db_session: "AsyncSession", data: dict) -> SuccessResponse:
        """Xoá sạch thông báo theo bộ lọc"""
        filter_type = data.get("filter_type", "ALL")
        res = await notification_service.clear_notifications(db_session, filter_type)
        await db_session.commit()
        return res

    @get("/trash")
    async def get_trash_notifications(
        self,
        db_session: "AsyncSession",
        request: Request,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> NotificationCursorPaginatedResponse:
        """Lấy danh sách thông báo đã bị xoá mềm (Thùng rác)"""
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")
        user_roles = user_state.get("roles", [])
        return await notification_service.get_trash_notifications_paginated(db_session, user_id, user_roles, cursor, limit)

    @post("/trash/restore")
    async def restore_notifications(self, db_session: "AsyncSession", data: dict) -> SuccessResponse:
        """Khôi phục các thông báo đã bị xoá mềm từ thùng rác"""
        ids = data.get("ids", [])
        if not ids:
            return SuccessResponse(ok=True)
        res = await notification_service.restore_notifications(db_session, ids)
        await db_session.commit()
        return res

    @post("/trash/hard-delete")
    async def hard_delete_notifications(self, db_session: "AsyncSession", data: dict) -> SuccessResponse:
        """Xoá cứng (vĩnh viễn) các thông báo trong thùng rác theo từng phần"""
        ids = data.get("ids", [])
        res = await notification_service.hard_delete_trash(db_session, ids if ids else None)
        await db_session.commit()
        return res

