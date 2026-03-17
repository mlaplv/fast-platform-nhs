from typing import List, Dict, Optional
import logging
from litestar import Controller, get, patch, Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.notification_service import notification_service

logger = logging.getLogger("api-gateway")

class NotificationController(Controller):
    path = "/api/v1/notifications"

    @get("/")
    async def get_notifications(self, db_session: AsyncSession, request: Request) -> List[Dict[str, object]]:
        """Lấy danh sách thông báo qua NotificationService"""
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")

        if not user_id:
            raise NotAuthorizedException("User context not found")

        return await notification_service.get_notifications(
            session=db_session,
            user_id=user_id,
            limit=20
        )

    @patch("/{notification_id:str}/read")
    async def mark_as_read(self, db_session: AsyncSession, notification_id: str) -> Dict[str, object]:
        """Đánh dấu thông báo đã đọc qua NotificationService"""
        await notification_service.mark_as_read(db_session, notification_id)
        return {"status": "success"}
