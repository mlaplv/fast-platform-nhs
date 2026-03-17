import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, cast
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import Order, User
from backend.services.event_bus import event_bus
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class OrderService:
    """
    ULTRA-LEAN ORDER SERVICE (ELITE V2.2)
    -------------------------------------
    Handles Order CRUD, State Machine transitions, and Anti-Spam triggers.
    """

    async def list_orders(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List orders with total count and customer projection (R76)."""
        conditions = [Order.deleted_at == None]

        if status and status != "all":
            conditions.append(Order.status == status.upper())

        if search:
            safe = escape_like(search)
            conditions.append(or_(
                Order.id.ilike(f"%{safe}%"),
                Order.user.has(func.unaccent(User.name).ilike(f"%{func.unaccent(safe)}%"))
            ))

        # 1. COUNT (Zero-Hydration)
        count_stmt = select(func.count(Order.id)).where(and_(*conditions))
        total = await session.scalar(count_stmt) or 0

        # 2. Scalar Projection Fetch
        stmt = select(
            Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
            Order.is_spam, Order.spam_score, Order.spam_reason, Order.fingerprint,
            User.name.label("customer_name")
        ).outerjoin(User, Order.user_id == User.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(Order.created_at.desc())

        result = await session.execute(stmt)
        data = [
            {
                "id": str(row.id),
                "customerName": row.customer_name or "Storefront Customer",
                "status": row.status.lower() if row.status else "pending",
                "total": float(row.total_amount) if row.total_amount else 0.0,
                "items": len(row.items) if isinstance(row.items, list) else 0,
                "createdAt": row.created_at.isoformat() if row.created_at else "",
                "isSpam": row.is_spam,
                "spamScore": row.spam_score,
                "spamReason": row.spam_reason,
                "fingerprint": row.fingerprint
            }
            for row in result
        ]

        return {"data": data, "total": total}

    async def get_order(self, session: AsyncSession, order_id: str) -> Dict[str, object]:
        """Get a single order with user details via Scalar Projection (R76)."""
        stmt = (
            select(
                Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
                Order.cancellation_reason, Order.is_spam, Order.spam_score, Order.spam_reason,
                Order.fingerprint, Order.history,
                User.name.label("customer_name")
            )
            .outerjoin(User, Order.user_id == User.id)
            .where(Order.id == order_id)
        )
        result = await session.execute(stmt)
        row = result.first()

        if not row:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Order {order_id} not found")

        return {
            "id": str(row.id),
            "customerName": row.customer_name or "Unknown",
            "status": row.status.lower() if row.status else "pending",
            "total": float(row.total_amount) if row.total_amount else 0.0,
            "items": row.items,
            "createdAt": row.created_at.isoformat() if row.created_at else "",
            "cancellationReason": row.cancellation_reason,
            "isSpam": row.is_spam,
            "spamScore": row.spam_score,
            "spamReason": row.spam_reason,
            "fingerprint": row.fingerprint,
            "history": row.history or []
        }

    async def _get_order_model(self, session: AsyncSession, order_id: str) -> Order:
        """Internal helper to get the ORM model for updates."""
        stmt = select(Order).where(Order.id == order_id)
        res = await session.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Order {order_id} not found")
        return order

    async def create_order(
        self,
        session: AsyncSession,
        data: Dict[str, object],
        ip: str = "unknown",
        ua: str = "unknown"
    ) -> Dict[str, object]:
        """Create order and emit creation event for Anti-Spam processing."""
        new_id = str(uuid.uuid4())
        order = Order(
            id=new_id,
            items=cast(List, data.get("items", [])),
            total_amount=cast(float, data.get("total_amount", 0.0)),
            status="PENDING",
            history=[{
                "status": "PENDING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": "Storefront",
                "note": "Order created via checkout"
            }]
        )

        session.add(order)
        await session.commit()

        # Emit event for XoHiResponder/AntiSpam
        await event_bus.emit("ORDER_CREATED", {
            "id": new_id,
            "ip": ip,
            "user_agent": ua,
            "customer": data.get("customer_name"),
            "phone": data.get("customer_phone"),
            "address": data.get("customer_address"),
            "total_amount": data.get("total_amount"),
        })

        return {"id": new_id, "status": "pending", "success": True}

    async def update_status(
        self,
        session: AsyncSession,
        order_id: str,
        new_status: str,
        actor: str = "System"
    ) -> Dict[str, object]:
        """Handle state machine transitions and history."""
        order = await self._get_order_model(session, order_id)
        current_status = order.status.upper()
        new_status = new_status.upper()

        # State Machine R60
        VALID_TRANSITIONS = {
            "PENDING": ["PAID", "CANCELLED"],
            "PAID": ["PROCESSING", "CANCELLED"],
            "PROCESSING": ["SHIPPED"],
            "SHIPPED": ["DELIVERED"],
            "DELIVERED": ["COMPLETED"],
            "COMPLETED": [],
            "CANCELLED": []
        }

        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            from litestar.exceptions import ValidationException
            raise ValidationException(f"Invalid transition from {current_status} to {new_status}")

        order.status = new_status

        history = list(order.history or [])
        history.append({
            "status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "note": "Status updated via admin"
        })
        order.history = history

        user_id = order.user_id
        await session.commit()

        await event_bus.emit("ORDER_UPDATED", {
            "id": order_id,
            "status": new_status,
            "tenant_id": user_id
        })

        return {"success": True, "new_status": new_status.lower()}

    async def cancel_order(
        self,
        session: AsyncSession,
        order_id: str,
        reason: str,
        actor: str = "System"
    ) -> Dict[str, object]:
        """Cancel order with reason."""
        order = await self._get_order_model(session, order_id)
        if order.status.upper() not in ["PENDING", "PAID"]:
            from litestar.exceptions import ValidationException
            raise ValidationException("Only PENDING or PAID orders can be cancelled")

        order.status = "CANCELLED"
        order.cancellation_reason = reason

        history = list(order.history or [])
        history.append({
            "status": "CANCELLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "note": f"Reason: {reason}"
        })
        order.history = history

        user_id = order.user_id
        await session.commit()

        await event_bus.emit("ORDER_CANCELLED", {
            "id": order_id,
            "reason": reason,
            "tenant_id": user_id
        })

        return {"success": True, "new_status": "cancelled"}

    async def toggle_spam(self, session: AsyncSession, order_id: str, actor: str = "System") -> Dict[str, object]:
        """Manual spam toggle override."""
        order = await self._get_order_model(session, order_id)
        new_state = not order.is_spam
        order.is_spam = new_state

        if not new_state:
            order.spam_score = 0.0
            order.spam_reason = "Manual Whitelist (Admin)"
        else:
            order.spam_score = 100.0
            order.spam_reason = "Manual Blacklist (Admin)"

        history = list(order.history or [])
        history.append({
            "status": order.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "note": f"Manual Spam Override: {'SPAM_MARKED' if new_state else 'SPAM_REMOVED'}"
        })
        order.history = history

        await session.commit()
        return {
            "success": True,
            "isSpam": order.is_spam,
            "spamScore": order.spam_score,
            "spamReason": order.spam_reason
        }

# Global Instance
order_service = OrderService()
