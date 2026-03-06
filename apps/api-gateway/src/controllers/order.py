import logging
import uuid
from datetime import datetime, timezone
from src.services.event_bus import event_bus
from src.services.anti_spam import AntiSpamService

logger = logging.getLogger("api-gateway")
from litestar import Controller, get, patch, Request
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from typing import List, Dict, Optional, Union
from pydantic import BaseModel
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.orm import selectinload

from src.database.repositories import OrderRepository, provide_order_repo
from src.database.models import Order, User
from src.guards import PermissionGuard
from src.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class OrderStatusUpdate(BaseModel):
    status: str
    
class CancelOrderRequest(BaseModel):
    reason: str

class OrderController(Controller):
    """R2: Class-based Litestar Controller for Order operations."""
    path = "/api/v1/orders"
    guards = [PermissionGuard("order:read")]
    dependencies = {"order_repo": Provide(provide_order_repo)}

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
        """List orders with advanced filtering using direct SQLAlchemy."""
        
        # Build dynamic where conditions
        conditions = [Order.deleted_at == None]
        
        if status and status != "all":
            conditions.append(Order.status == status.upper())
            
        if search:
            safe = escape_like(search)
            # V56.0 Phase 4: unaccent() for Vietnamese diacritic-insensitive search
            conditions.append(or_(
                Order.id.ilike(f"%{safe}%"),
                Order.user.has(func.unaccent(User.name).ilike(f"%{func.unaccent(safe)}%"))
            ))

        # 1. Total Count (Rule 1.5 - Scalar Zero-Hydration)
        count_stmt = select(func.count(Order.id)).where(and_(*conditions))
        total_res = await order_repo.session.execute(count_stmt)
        total = total_res.scalar_one()
        
        # 2. Optimized Fetch (Rule R41 - N+1 Safe with selectinload)
        stmt = select(Order).where(and_(*conditions)).options(
            selectinload(Order.user)
        ).limit(limit).offset(offset).order_by(Order.created_at.desc())
        
        result = await order_repo.session.execute(stmt)
        orders = result.scalars().all()
        
        data = [
            {
                "id": str(o.id),
                "customerName": o.user.name if o.user else "Unknown",
                "status": o.status.lower() if o.status else "pending",
                "total": float(o.total_amount) if o.total_amount else 0.0,
                "items": len(o.items) if isinstance(o.items, list) else 0,
                "createdAt": o.created_at.isoformat() if o.created_at else "",
            }
            for o in orders
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
        
        await order_repo.session.commit()
        
        # V56.5 Proactive Nerve System: Emit event
        await event_bus.emit("ORDER_UPDATED", {
            "id": order_id, 
            "status": new_status, 
            "tenant_id": str(order.user.id) if order.user else None
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
        
        await order_repo.session.commit()
        
        # V56.5 Proactive Nerve System: Emit event instantly
        await event_bus.emit("ORDER_CANCELLED", {
            "id": order_id, 
            "reason": data.reason,
            "tenant_id": str(order.user.id) if order.user else None
        })
        
        return {"success": True, "new_status": "cancelled"}
