import logging
from typing import List, Optional
from sqlalchemy import select, or_, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotAuthorizedException

from backend.database.models import Notification, User
from backend.database.repositories import UserRepository
from backend.schemas.notification import NotificationResponse, NotificationListResponse, NotificationCursorPaginatedResponse
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
        filters = [*conditions, Notification.deleted_at == None]
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
    async def get_notifications_paginated(
        db_session: AsyncSession,
        user_email: Optional[str],
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> NotificationCursorPaginatedResponse:
        """Fetch notifications using cursor pagination (O(1) lookups on large datasets)."""
        from sqlalchemy.orm import selectinload
        import base64
        
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
            conditions = [
                or_(
                    Notification.user_id == str(user.id),
                    Notification.user_id == "user_admin",
                    Notification.user_id == None
                )
            ]

        filters = [*conditions, Notification.deleted_at == None]
        if not is_staff:
            from sqlalchemy import not_
            system_filter = not_(Notification.type.like("SYSTEM_%"))
            filters.append(system_filter)

        # Cursor decoding
        cursor_created_at = None
        cursor_id = None
        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode("utf-8")).decode("utf-8")
                parts = decoded.split("|")
                if len(parts) == 2:
                    cursor_created_at = datetime.fromisoformat(parts[0])
                    cursor_id = parts[1]
            except Exception:
                logger.warning(f"Malformed cursor received: {cursor}")

        # Apply cursor conditions
        if cursor_created_at and cursor_id:
            filters.append(
                or_(
                    Notification.created_at < cursor_created_at,
                    and_(
                        Notification.created_at == cursor_created_at,
                        Notification.id < cursor_id
                    )
                )
            )

        # Fetch limit + 1 items to determine if next page exists
        stmt = (
            select(
                Notification.id, Notification.type, Notification.message,
                Notification.is_read, Notification.created_at, Notification.user_id
            )
            .where(*filters)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit + 1)
        )

        res = await db_session.execute(stmt)
        rows = list(res)
        
        has_more = len(rows) > limit
        items_to_return = rows[:limit] if has_more else rows
        
        data = [NotificationResponse.model_validate(row._mapping) for row in items_to_return]
        
        next_cursor = None
        if has_more and items_to_return:
            last_item = items_to_return[-1]._mapping
            # Encode next cursor
            raw_cursor = f"{last_item['created_at'].isoformat()}|{last_item['id']}"
            next_cursor = base64.b64encode(raw_cursor.encode("utf-8")).decode("utf-8")

        return NotificationCursorPaginatedResponse(data=data, next_cursor=next_cursor, has_more=has_more)

    @staticmethod
    async def mark_as_read(db_session: AsyncSession, notification_id: str) -> SuccessResponse:
        """Mark a notification as read."""
        stmt = update(Notification).where(Notification.id == notification_id).values(is_read=True)
        await db_session.execute(stmt)
        return SuccessResponse(ok=True, id=notification_id)

    @staticmethod
    async def bulk_delete(db_session: AsyncSession, notification_ids: List[str]) -> SuccessResponse:
        """Xoá mềm danh sách thông báo"""
        from datetime import datetime, timezone
        stmt = (
            update(Notification)
            .where(Notification.id.in_(notification_ids))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await db_session.execute(stmt)
        return SuccessResponse(ok=True)

    @staticmethod
    async def clear_notifications(db_session: AsyncSession, filter_type: str) -> SuccessResponse:
        """Xoá sạch thông báo theo bộ lọc"""
        from datetime import datetime, timezone
        from sqlalchemy import or_

        conditions = [
            or_(
                Notification.user_id == "user_admin",
                Notification.user_id == None
            )
        ]

        if filter_type == "ORDER":
            conditions.append(or_(Notification.type.like("%ORDER%"), Notification.type.like("%COMMERCE%")))
        elif filter_type == "CHAT":
            conditions.append(or_(Notification.type == "CHAT", Notification.type.like("%SUPPORT%")))
        elif filter_type == "SECURITY":
            conditions.append(or_(Notification.type.like("%SECURITY%"), Notification.type.like("%SYSTEM%"), Notification.type.like("%ANOMALY%")))
        elif filter_type == "URGENT":
            conditions.append(or_(Notification.type.like("%URGENT%"), Notification.type == "CRITICAL"))

        # Chỉ xoá những thông báo chưa xoá
        conditions.append(Notification.deleted_at == None)

        stmt = (
            update(Notification)
            .where(*conditions)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await db_session.execute(stmt)
        return SuccessResponse(ok=True)

notification_service = NotificationService()
