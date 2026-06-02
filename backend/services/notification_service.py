import logging
from typing import List, Optional
from sqlalchemy import select, or_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotAuthorizedException

from backend.database.models import Notification, User
from backend.database.repositories import UserRepository
from backend.schemas.notification import NotificationResponse, NotificationListResponse
from backend.schemas.common import SuccessResponse

logger = logging.getLogger("api-gateway")

class NotificationService:
    @staticmethod
    async def get_notifications(db_session: AsyncSession, user_email: Optional[str]) -> NotificationListResponse:
        """Fetch notifications (R76: Scalar Projection). R1.5: Zero-Hydration.
        SECURITY: SYSTEM_ type notifications are strictly admin-only and never
        returned to end clients regardless of user_id linkage.
        """
        from sqlalchemy.orm import selectinload
        
        is_staff = False
        user = None

        if user_email:
            stmt = select(User).options(selectinload(User.roles)).where(User.email == user_email)
            user = (await db_session.execute(stmt)).scalar_one_or_none()
            if not user:
                raise NotAuthorizedException("User context not found")
            
            user_roles = [r.code for r in getattr(user, "roles", [])]
            is_staff = any(role in ["SUPER_ADMIN", "MANAGER", "EDITOR", "AI_TRAINER"] for role in user_roles)

        # Build query conditions
        if not user_email:
            conditions = [Notification.user_id == None]
        else:
            # Sếp's administrative portal always includes admin notifications
            conditions = [
                or_(
                    Notification.user_id == str(user.id),
                    Notification.user_id == "user_admin",
                    Notification.user_id == None
                )
            ]

        # SECURITY FILTER: Never expose SYSTEM_ alerts to end clients.
        # System alerts (DB pool, AI latency, order anomaly) are infra-internal.
        filters = [*conditions]
        if not is_staff:
            from sqlalchemy import not_
            system_filter = not_(Notification.type.like("SYSTEM_%"))
            filters.append(system_filter)

        # 1. Total Count (Zero-Hydration)
        count_stmt = select(func.count(Notification.id)).where(*filters)
        total = await db_session.scalar(count_stmt) or 0

        # 2. Results (R76: Scalar Projection)
        stmt = (
            select(
                Notification.id, Notification.type, Notification.message,
                Notification.is_read, Notification.created_at, Notification.user_id
            )
            .where(*filters)
            .order_by(Notification.created_at.desc())
            .limit(200 if is_staff else 20)
        )

        res = await db_session.execute(stmt)
        data = [NotificationResponse.model_validate(row._mapping) for row in res]
        return NotificationListResponse(data=data, total=total)

    @staticmethod
    async def mark_as_read(db_session: AsyncSession, notification_id: str) -> SuccessResponse:
        """Mark a notification as read."""
        stmt = update(Notification).where(Notification.id == notification_id).values(is_read=True)
        await db_session.execute(stmt)
        return SuccessResponse(ok=True, id=notification_id)

notification_service = NotificationService()
