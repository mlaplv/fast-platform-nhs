from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from litestar import Controller, get, patch, Request
from litestar.exceptions import NotAuthorizedException

from backend.services.notification_service import notification_service
from backend.schemas.notification import NotificationListResponse
from backend.schemas.common import SuccessResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api-gateway")

class ClientNotificationController(Controller):
    path = "/api/v1/client/notifications"

    @get("/")
    async def get_notifications(self, db_session: AsyncSession, request: Request) -> NotificationListResponse:
        """
        Elite V3.0: Fetch personal notifications for the current authenticated user.
        """
        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            raise NotAuthorizedException("Vui lòng đăng nhập để xem thông báo")
            
        user_email = user_state.get("sub")
        return await notification_service.get_notifications(db_session, user_email)

    @patch("/{notification_id:str}/read")
    async def mark_as_read(self, db_session: AsyncSession, request: Request, notification_id: str) -> SuccessResponse:
        """
        Elite V3.0: Mark a notification as read. 
        Safety: mark_as_read in service handles core logic.
        """
        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            raise NotAuthorizedException("Session expired")
            
        res = await notification_service.mark_as_read(db_session, notification_id)
        await db_session.commit()
        return res
