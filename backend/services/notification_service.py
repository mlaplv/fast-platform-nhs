import logging
from typing import List, Dict, Optional, Union
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Notification

logger = logging.getLogger("api-gateway")

class NotificationService:
    """
    ULTRA-LEAN NOTIFICATION SERVICE (ELITE V2.2)
    -------------------------------------------
    Handles system and user-specific notifications.
    """

    async def get_notifications(
        self,
        session: AsyncSession,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, object]]:
        """Fetch notifications for a specific user or global system notifications."""

        # Build query: notifications for user OR global (user_id IS NULL)
        stmt = select(
            Notification.id, Notification.user_id, Notification.type,
            Notification.message, Notification.is_read, Notification.created_at
        ).where(
            or_(
                Notification.user_id == user_id,
                Notification.user_id == None
            )
        ).order_by(Notification.created_at.desc()).limit(limit)

        res = await session.execute(stmt)

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

    async def mark_as_read(self, session: AsyncSession, notification_id: str) -> bool:
        """Mark a notification as read."""
        stmt = update(Notification).where(Notification.id == notification_id).values(is_read=True)
        await session.execute(stmt)
        await session.commit()
        return True

# Global Instance
notification_service = NotificationService()
