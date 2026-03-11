import logging
import uuid
from datetime import datetime, timezone
from backend.services.event_bus import event_bus
from backend.services.anti_spam import AntiSpamService

logger = logging.getLogger("api-gateway")
from litestar import Controller, get, patch, post, Request
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from typing import List, Dict, Optional, Union
from pydantic import BaseModel
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.orm import selectinload

from backend.database.repositories import OrderRepository, provide_order_repo
from backend.database.models import Order, User
from backend.guards import PermissionGuard
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class OrderStatusUpdate(BaseModel):
    status: str
    
class CancelOrderRequest(BaseModel):
    reason: str

class OrderCreateRequest(BaseModel):
    items: List[Dict[str, Union[str, int, float]]]
    total_amount: float
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

class OrderController(Controller):
    """R2: Class-based Litestar Controller for Order operations."""
    path = "/api/v1/orders"
    guards = [PermissionGuard("order:read")]
    dependencies = {"order_repo": Provide(provide_order_repo)}

    @post("/", guards=[])  # PUBLIC: Storefront Checkout
    async def create_order(self, request: Request, order_repo: OrderRepository, data: OrderCreateRequest) -> dict[str, object]:
        """PUBLIC: Handle storefront checkout with Anti-Spam Shield integration."""
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "unknown")
        
        new_id = str(uuid.uuid4())
        # Note: In a real system, we would link to a User or create a guest user
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
        
        await order_repo.add(order)
        await order_repo.session.commit()
        
        # V56.5 Proactive Nerve System: Emit event instantly
        # XoHiResponder will pick this up and run Anti-Spam check asynchronously
        await event_bus.emit("ORDER_CREATED", {
            "id": new_id,
            "ip": ip,
            "user_agent": ua,
            "customer": data.customer_name,
            "phone": data.customer_phone,
            "address": data.customer_address,
            "total_amount": data.total_amount,
            "tenant_id": None # Global tenant or resolve from header
        })
        
        return {"success": True, "order_id": new_id}

    @get("/")
    async def list_orders(
        self,
        request: Request,
        order_repo: OrderRepository,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict[str, object]:
        """List orders (R76: Scalar Projection)."""
        from sqlalchemy import select, func, or_, and_
        
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
        total = await order_repo.session.scalar(count_stmt) or 0
        
        # 2. R76: Scalar Projection Fetch
        stmt = select(
            Order.id, Order.status, Order.total_amount, Order.items, Order.created_at,
            Order.is_spam, Order.spam_score, Order.spam_reason, Order.fingerprint,
            User.name.label("customer_name")
        ).outerjoin(User, Order.user_id == User.id).where(
            and_(*conditions)
        ).limit(limit).offset(offset).order_by(Order.created_at.desc())
        
        result = await order_repo.session.execute(stmt)
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
        
        return {
            "data": data,
            "total": total
        }

    @get("/{order_id:str}")
    async def get_order(self, order_repo: OrderRepository, order_id: str) -> dict[str, object]:
        """Get a single order using direct SQLAlchemy."""
        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.user))
        result = await order_repo.session.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise NotFoundException(f"Order {order_id} not found")
            
        return {
            "id": str(order.id),
            "customerName": order.user.name if order.user else "Unknown",
            "status": order.status.lower(),
            "total": float(order.total_amount) if order.total_amount else 0.0,
            "items": order.items,
            "createdAt": order.created_at.isoformat() if order.created_at else "",
            "cancellationReason": order.cancellation_reason,
            "isSpam": order.is_spam,
            "spamScore": order.spam_score,
            "spamReason": order.spam_reason,
            "fingerprint": order.fingerprint,
            "history": order.history or []
        }

    @patch("/{order_id:str}/status", guards=[PermissionGuard("order:write")])
    async def update_order_status(self, request: Request, order_repo: OrderRepository, order_id: str, data: OrderStatusUpdate) -> dict[str, object]:
        """UPDATE order status with strict state machine validation and history."""
        order = await order_repo.get(order_id)
        current_status = order.status.upper()
        new_status = data.status.upper()
        
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
        user_state = request.scope.get("state", {}).get("user", {})
        user_email = user_state.get("sub", "System")
        
        # Append history
        history = list(order.history or [])
        history.append({
            "status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": user_email,
            "note": "Status updated via admin"
        })
        order.history = history
        
        # Save tenant_id before commit to avoid expire_on_commit lazy load MissingGreenlet
        tenant_id = order.user_id
        await order_repo.session.commit()
        
        # V56.5 Proactive Nerve System: Emit event
        await event_bus.emit("ORDER_UPDATED", {
            "id": order_id, 
            "status": new_status, 
            "tenant_id": tenant_id
        })
        
        return {"success": True, "new_status": new_status.lower()}

    @patch("/{order_id:str}/cancel", guards=[PermissionGuard("order:write")])
    async def cancel_order(self, request: Request, order_repo: OrderRepository, order_id: str, data: CancelOrderRequest) -> dict[str, object]:
        """Cancel an order with a reason."""
        order = await order_repo.get(order_id)
        current_status = order.status.upper()
        
        if current_status not in ["PENDING", "PAID"]:
            from litestar.exceptions import ValidationException
            raise ValidationException("Only PENDING or PAID orders can be cancelled")
            
        order.status = "CANCELLED"
        order.cancellation_reason = data.reason
        
        user_state = request.scope.get("state", {}).get("user", {})
        user_email = user_state.get("sub", "System")
        history = list(order.history or [])
        history.append({
            "status": "CANCELLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": user_email,
            "note": f"Reason: {data.reason}"
        })
        order.history = history
        
        # Save tenant_id before commit to avoid expire_on_commit lazy load MissingGreenlet
        tenant_id = order.user_id
        await order_repo.session.commit()
        
        # V56.5 Proactive Nerve System: Emit event instantly
        await event_bus.emit("ORDER_CANCELLED", {
            "id": order_id, 
            "reason": data.reason,
            "tenant_id": tenant_id
        })
        
        return {"success": True, "new_status": "cancelled"}

    @patch("/{order_id:str}/spam", guards=[PermissionGuard("order:write")])
    async def toggle_order_spam(self, request: Request, order_repo: OrderRepository, order_id: str) -> dict[str, object]:
        """Manually toggle the spam status of an order."""
        order = await order_repo.get(order_id)
        if not order:
            raise NotFoundException(f"Order {order_id} not found")

        # Toggle state
        new_spam_state = not order.is_spam
        order.is_spam = new_spam_state
        
        # If manually unmarking, we clear the low scores/reasons to indicate trust
        if not new_spam_state:
            order.spam_score = 0.0
            order.spam_reason = "Manual Whitelist (Admin)"
        else:
            order.spam_score = 100.0
            order.spam_reason = "Manual Blacklist (Admin)"

        user_state = request.scope.get("state", {}).get("user", {})
        user_email = user_state.get("sub", "System")
        
        history = list(order.history or [])
        history.append({
            "status": order.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": user_email,
            "note": f"Manual Spam Override: {'SPAM_MARKED' if new_spam_state else 'SPAM_REMOVED'}"
        })
        order.history = history
        
        res_score = order.spam_score
        res_reason = order.spam_reason
        
        await order_repo.session.commit()
        
        return {
            "success": True, 
            "isSpam": new_spam_state,
            "spamScore": res_score,
            "spamReason": res_reason
        }
