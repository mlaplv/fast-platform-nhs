from typing import List, Dict, Union, Optional
import logging
from litestar import Controller, get, patch, Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update

from backend.database.models import Notification, User
from backend.database.repositories import UserRepository

logger = logging.getLogger("api-gateway")

class NotificationController(Controller):
    path = "/api/v1/notifications"

    @get("/")
    async def get_notifications(self, db_session: AsyncSession, request: Request) -> List[Dict[str, object]]:
        """Lấy danh sách thông báo của user hiện tại"""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub")
        
        # Build query conditions
        conditions = []
        
        if not user_email:
            stmt = select(
                Notification.id, Notification.user_id, Notification.type, 
                Notification.message, Notification.is_read, Notification.created_at
            ).where(Notification.user_id == None).order_by(Notification.created_at.desc()).limit(20)
        else:
            user_repo = UserRepository(session=db_session)
            user = await user_repo.get_one_or_none(email=user_email)
            if not user:
                raise NotAuthorizedException("User context not found")
            
            stmt = select(
                Notification.id, Notification.user_id, Notification.type, 
                Notification.message, Notification.is_read, Notification.created_at
            ).where(
                or_(
                    Notification.user_id == str(user.id),
                    Notification.user_id == None
                )
            ).order_by(Notification.created_at.desc()).limit(20)

        res = await db_session.execute(stmt)
        # Result contains rows (tuples), not objects
        return [
            {
                "id": str(row.id),
                "userId": str(row.user_id) if row.user_id else None,
                "type": row.type,
                "message": row.message,
                "isRead": row.is_read,
                "createdAt": row.created_at.isoformat() if row.created_at else "",
            }
            for row in res
        ]

    @patch("/{notification_id:str}/read")
    async def mark_as_read(self, db_session: AsyncSession, notification_id: str) -> Dict[str, object]:
        """Đánh dấu thông báo đã đọc"""
        stmt = update(Notification).where(Notification.id == notification_id).values(is_read=True)
        await db_session.execute(stmt)
        await db_session.commit()
        return {"status": "success"}
