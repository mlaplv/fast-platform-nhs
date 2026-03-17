import logging
from typing import List, Dict, Optional, Union
from sqlalchemy import select, or_, update, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api-gateway")

class NotificationService:
    """
    ULTRA-LEAN NOTIFICATION SERVICE (ELITE V2.2)
    -------------------------------------------
    Handles system and user-specific notifications.
    Zero-Hydration (Rule 1.5): Raw SQL & Scalar Projection for <2GB RAM.
    """

    async def get_notifications(
        self,
        session: AsyncSession,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, object]]:
        """Fetch notifications via Scalar Projection (Zero-Hydration)."""

        stmt = text("""
            SELECT id, user_id, type, message, is_read, created_at
            FROM notifications
            WHERE user_id = :uid OR user_id IS NULL
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        res = await session.execute(stmt, {"uid": user_id, "limit": limit})
        rows = res.all()

        return [
            {
                "id": str(row[0]),
                "userId": str(row[1]) if row[1] else None,
                "type": row[2],
                "message": row[3],
                "isRead": row[4],
                "createdAt": row[5].isoformat() if row[5] else "",
            }
            for row in rows
        ]

    async def mark_as_read(self, session: AsyncSession, notification_id: str) -> bool:
        """Mark a notification as read via direct SQL."""
        stmt = text("UPDATE notifications SET is_read = true, updated_at = NOW() WHERE id = :id")
        await session.execute(stmt, {"id": notification_id})
        await session.commit()
        return True

# Global Instance
notification_service = NotificationService()
