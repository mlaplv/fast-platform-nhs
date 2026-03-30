import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, TypedDict, Union

from sqlalchemy import select, func, or_, and_
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException, ValidationException

from backend.database.models import Order, User
from backend.database import current_tenant_id
from backend.services.event_bus import event_bus
from backend.utils.sql import escape_like
from backend.schemas.order import OrderResponse, OrderListResponse, OrderCreateRequest, OrderStatusUpdate, CancelOrderRequest, OrderPlanningRequest
from backend.schemas.common import SuccessResponse

# Phase 85: Strict JSON Typography
JSONType = Union[str, int, float, bool, None, List["JSONType"], Dict[str, "JSONType"]]

class OrderMetadata(TypedDict, total=False):
    user_agent: str
    fingerprint: Optional[str]
    client_notes: Optional[str]

class OrderHistoryItem(TypedDict):
    status: str
    timestamp: str
    actor: str
    note: str

class PreviousOrder(TypedDict):
    id: str
    created_at: str
    status: str
    total: float
    item_count: int

class OrderInsight(TypedDict):
    ltv: float
    total_orders: int
    trust_score: float
    first_order: Optional[str]
    last_order: Optional[str]
    previous_orders: List[PreviousOrder]

logger = logging.getLogger("api-gateway")

class OrderService:
    @staticmethod
    async def create_order(db_session: AsyncSession, data: OrderCreateRequest, ip: str, ua: str) -> SuccessResponse:
        """Moves logic from OrderController.create_order. Emits ORDER_CREATED event via event_bus."""
        new_id = str(uuid.uuid4())
        history: List[OrderHistoryItem] = [{
            "status": "PENDING",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "Storefront",
            "note": "Order created via checkout"
        }]

        order = Order(
            id=new_id,
            items=data.items,
            total_amount=data.total_amount,
            status="PENDING",
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_address=data.customer_address,
            customer_ip=ip,
            tenant_id=current_tenant_id.get() or "default",
            order_metadata=OrderMetadata(
                user_agent=ua,
                fingerprint=data.items[0].get("fingerprint") if isinstance(data.items, list) and data.items else None 
            ),
            history=history
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
            "tenant_id": current_tenant_id.get() or "default",
            "items": data.items if isinstance(data.items, list) else [],
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
        conditions = [
            Order.deleted_at == None,
            Order.tenant_id == (current_tenant_id.get() or "default")
        ]

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

        # 2. R76: Scalar Projection Fetch with Aggregate History
        # Identity match: customer_phone (if exists) OR user_id OR fingerprint
        
        # Subqueries for stats (Performance Optimized Viral 2026)
        success_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"), # Reference outer column
                Order.status == "DELIVERED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("successful_count")
        
        cancel_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"),
                Order.status == "CANCELLED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("cancelled_count")

        stmt = select(
            Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
            Order.is_spam, Order.spam_score, Order.spam_reason, Order.fingerprint,
            Order.customer_name, Order.customer_phone, Order.customer_address, Order.customer_ip,
            User.name.label("user_name"),
            success_sq, cancel_sq
        ).outerjoin(User, Order.user_id == User.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(Order.created_at.desc())

        result = await db_session.execute(stmt)
        data = [OrderResponse.model_validate(row) for row in result]

        return OrderListResponse(data=data, total=total)

    @staticmethod
    async def get_order(db_session: AsyncSession, order_id: str) -> OrderResponse:
        """Moves logic from OrderController.get_order. Uses Scalar Projection."""
        success_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"),
                Order.status == "DELIVERED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("successful_count")
        
        cancel_sq = select(sa.func.count(Order.id)).where(
            and_(
                Order.customer_phone == sa.column("customer_phone"),
                Order.status == "CANCELLED",
                Order.tenant_id == (current_tenant_id.get() or "default")
            )
        ).scalar_subquery().label("cancelled_count")

        stmt = (
            select(
                Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
                Order.is_spam, Order.spam_score, Order.spam_reason, Order.fingerprint,
                Order.customer_name, Order.customer_phone, Order.customer_address, Order.customer_ip,
                Order.history, Order.cancellation_reason,
                User.name.label("user_name"),
                success_sq, cancel_sq
            )
            .outerjoin(User, Order.user_id == User.id)
        )

        # R2026: Elite Suffix Lookup Support
        if len(order_id) == 6:
             stmt = stmt.where(Order.id.ilike(f"%{order_id}"))
        else:
             stmt = stmt.where(Order.id == order_id)
        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            raise NotFoundException(f"Order {order_id} not found")

        # Customer 360 Insights (Viral 2026 Deep Intelligence)
        phone = row.customer_phone
        insight: Optional[OrderInsight] = None
        if phone:
            insight_stmt = select(
                sa.func.sum(Order.total_amount).filter(Order.status == "DELIVERED").label("ltv"),
                sa.func.count(Order.id).label("total_orders"),
                # Success rate calculation
                (sa.func.count(Order.id).filter(Order.status == "DELIVERED") * 100.0 / sa.func.count(Order.id)).label("trust_score"),
                sa.func.min(Order.created_at).label("first_order"),
                sa.func.max(Order.created_at).label("last_order")
            ).where(
                and_(
                    Order.customer_phone == phone,
                    Order.tenant_id == (current_tenant_id.get() or "default")
                )
            )
            stats = (await db_session.execute(insight_stmt)).fetchone()
            
            # Fetch previous 10 orders (excluding self)
            history_stmt = select(
                Order.id, Order.created_at, Order.status, Order.total_amount, Order.items
            ).where(
                and_(
                    Order.customer_phone == phone,
                    Order.id != order_id,
                    Order.tenant_id == (current_tenant_id.get() or "default")
                )
            ).order_by(Order.created_at.desc()).limit(10)
            
            history_result = await db_session.execute(history_stmt)
            previous_orders: List[PreviousOrder] = []
            for h in history_result:
                previous_orders.append({
                    "id": h.id,
                    "created_at": h.created_at.isoformat(),
                    "status": h.status,
                    "total": float(h.total_amount),
                    "item_count": sum(it.get("quantity", 1) for it in h.items) if isinstance(h.items, list) else 0
                })

            if stats:
                insight = OrderInsight(
                    ltv=float(stats.ltv) if stats.ltv else 0.0,
                    total_orders=int(stats.total_orders) if stats.total_orders else 0,
                    trust_score=float(stats.trust_score) if stats.trust_score else 0.0,
                    first_order=stats.first_order.isoformat() if stats.first_order else None,
                    last_order=stats.last_order.isoformat() if stats.last_order else None,
                    previous_orders=previous_orders
                )

        # Validate with custom insight field
        res_dict = dict(row._asdict())
        res_dict["insight"] = insight
        return OrderResponse.model_validate(res_dict)

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
            "PENDING": ["PACKED", "CANCELLED"],
            "PACKED": ["SHIPPING", "CANCELLED"],
            "SHIPPING": ["DELIVERED"],
            "DELIVERED": [],
            "CANCELLED": ["PENDING"] # Allow reopening
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

        if current_status not in ["PENDING", "PACKED"]:
            raise ValidationException("Only PENDING or PACKED orders can be cancelled")

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

    @staticmethod
    async def update_planning(
        db_session: AsyncSession,
        order_id: str,
        data: OrderPlanningRequest,
        actor_email: str
    ) -> SuccessResponse:
        """Elite V2.2: Professional Logistics Planning Logic"""
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        # Update order_metadata with planning fields
        meta = dict(order.order_metadata or {})
        meta.update({
            "assigned_to": data.assigned_to,
            "scheduled_at": data.scheduled_at.isoformat() if data.scheduled_at else None,
            "priority": data.priority,
            "planning_notes": data.planning_notes
        })
        order.order_metadata = meta

        # Add trace log to history
        history = list(order.history or [])
        history.append({
            "status": order.status, # Keep current status
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor_email,
            "note": f"Planning Updated: Assigned={data.assigned_to}, Priority={data.priority}"
        })
        order.history = history

        await event_bus.emit("ORDER_PLANNING_UPDATED", {
            "id": order_id,
            "assigned_to": data.assigned_to,
            "priority": data.priority,
            "tenant_id": order.user_id
        })

        return SuccessResponse(ok=True, id=order_id, message="Planning details updated")

order_service = OrderService()
