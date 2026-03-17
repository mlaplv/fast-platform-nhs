import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException, ValidationException

from backend.database.models import Order, User
from backend.services.event_bus import event_bus
from backend.utils.sql import escape_like
from backend.schemas.order import OrderResponse, OrderListResponse, OrderCreateRequest, OrderStatusUpdate, CancelOrderRequest
from backend.schemas.common import SuccessResponse

logger = logging.getLogger("api-gateway")

class OrderService:
    @staticmethod
    async def create_order(db_session: AsyncSession, data: OrderCreateRequest, ip: str, ua: str) -> SuccessResponse:
        """Moves logic from OrderController.create_order. Emits ORDER_CREATED event via event_bus."""
        new_id = str(uuid.uuid4())
        order = Order(
            id=new_id,
            items=data.items,
            total_amount=data.total_amount,
            status="PENDING",
            history=[{
                "status": "PENDING",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": "Storefront",
                "note": "Order created via checkout"
            }]
        )

        db_session.add(order)
        # Flush to get it in the DB before emitting event if needed,
        # but the controller will commit.

        await event_bus.emit("ORDER_CREATED", {
            "id": new_id,
            "ip": ip,
            "user_agent": ua,
            "customer": data.customer_name,
            "phone": data.customer_phone,
            "address": data.customer_address,
            "total_amount": data.total_amount,
            "tenant_id": None
        })

        return SuccessResponse(ok=True, id=new_id)

    @staticmethod
    async def list_orders(
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> OrderListResponse:
        """Moves logic from OrderController.list_orders. Uses Scalar Projection."""
        conditions = [Order.deleted_at == None]

        if status and status != "all":
            conditions.append(Order.status == status.upper())

        if search:
            safe = escape_like(search)
            conditions.append(or_(
                Order.id.ilike(f"%{safe}%"),
                Order.user.has(func.unaccent(User.name).ilike(f"%{func.unaccent(safe)}%"))
            ))

        # 1. Total Count (Zero-Hydration)
        count_stmt = select(func.count(Order.id)).where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0

        # 2. R76: Scalar Projection Fetch
        stmt = select(
            Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
            Order.is_spam, Order.spam_score, Order.spam_reason, Order.fingerprint,
            User.name.label("customer_name")
        ).outerjoin(User, Order.user_id == User.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(Order.created_at.desc())

        result = await db_session.execute(stmt)
        data = [OrderResponse.model_validate(row) for row in result]

        return OrderListResponse(data=data, total=total)

    @staticmethod
    async def get_order(db_session: AsyncSession, order_id: str) -> OrderResponse:
        """Moves logic from OrderController.get_order. Uses Scalar Projection."""
        stmt = (
            select(
                Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
                Order.is_spam, Order.spam_score, Order.spam_reason, Order.fingerprint,
                Order.history, Order.cancellation_reason,
                User.name.label("customer_name")
            )
            .outerjoin(User, Order.user_id == User.id)
            .where(Order.id == order_id)
        )
        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Order {order_id} not found")

        return OrderResponse.model_validate(row)

    @staticmethod
    async def transition_status(
        db_session: AsyncSession,
        order_id: str,
        new_status: str,
        actor_email: str
    ) -> SuccessResponse:
        """Moves logic from OrderController.update_order_status. Implements State Machine R60 and emits ORDER_UPDATED."""
        # We need the full object to update it and its history
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        current_status = order.status.upper()
        new_status = new_status.upper()

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
            raise ValidationException(f"Invalid transition from {current_status} to {new_status}")

        order.status = new_status

        history = list(order.history or [])
        history.append({
            "status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": "Status updated via admin"
        })
        order.history = history

        tenant_id = order.user_id

        await event_bus.emit("ORDER_UPDATED", {
            "id": order_id,
            "status": new_status,
            "tenant_id": tenant_id
        })

        return SuccessResponse(ok=True, id=order_id, message=f"Status updated to {new_status}")

    @staticmethod
    async def cancel_order(
        db_session: AsyncSession,
        order_id: str,
        reason: str,
        actor_email: str
    ) -> SuccessResponse:
        """Moves logic from OrderController.cancel_order. Emits ORDER_CANCELLED."""
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        current_status = order.status.upper()

        if current_status not in ["PENDING", "PAID"]:
            raise ValidationException("Only PENDING or PAID orders can be cancelled")

        order.status = "CANCELLED"
        order.cancellation_reason = reason

        history = list(order.history or [])
        history.append({
            "status": "CANCELLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": f"Reason: {reason}"
        })
        order.history = history

        tenant_id = order.user_id

        await event_bus.emit("ORDER_CANCELLED", {
            "id": order_id,
            "reason": reason,
            "tenant_id": tenant_id
        })

        return SuccessResponse(ok=True, id=order_id, message="Order cancelled")

    @staticmethod
    async def toggle_spam(
        db_session: AsyncSession,
        order_id: str,
        actor_email: str
    ) -> SuccessResponse:
        """Moves logic from OrderController.toggle_order_spam."""
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        new_spam_state = not order.is_spam
        order.is_spam = new_spam_state

        if not new_spam_state:
            order.spam_score = 0.0
            order.spam_reason = "Manual Whitelist (Admin)"
        else:
            order.spam_score = 100.0
            order.spam_reason = "Manual Blacklist (Admin)"

        history = list(order.history or [])
        history.append({
            "status": order.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": f"Manual Spam Override: {'SPAM_MARKED' if new_spam_state else 'SPAM_REMOVED'}"
        })
        order.history = history

        return SuccessResponse(
            ok=True,
            id=order_id,
            data={
                "isSpam": new_spam_state,
                "spamScore": order.spam_score,
                "spamReason": order.spam_reason
            }
        )

order_service = OrderService()
