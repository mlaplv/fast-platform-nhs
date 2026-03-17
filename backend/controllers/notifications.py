from __future__ import annotations
from typing import List, Dict, Union, Optional
import logging
from litestar import Controller, get, patch, Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update, func

from backend.services.notification_service import notification_service
from backend.schemas.notification import NotificationResponse, NotificationListResponse
from backend.schemas.common import SuccessResponse

logger = logging.getLogger("api-gateway")

class NotificationController(Controller):
    path = "/api/v1/notifications"

    @get("/")
    async def get_notifications(self, db_session: "AsyncSession", request: Request) -> NotificationListResponse:
        """Lấy danh sách thông báo của user hiện tại"""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub")
        return await notification_service.get_notifications(db_session, user_email)

    @patch("/{notification_id:str}/read")
    async def mark_as_read(self, db_session: "AsyncSession", notification_id: str) -> SuccessResponse:
        """Đánh dấu thông báo đã đọc"""
        res = await notification_service.mark_as_read(db_session, notification_id)
        await db_session.commit()
        return res
