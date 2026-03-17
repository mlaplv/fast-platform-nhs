from litestar import Controller, get, patch, post, Request
from litestar.exceptions import NotFoundException
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.order_service import order_service
from backend.guards import PermissionGuard

logger = logging.getLogger("api-gateway")

class OrderStatusUpdate(BaseModel):
    status: str

class CancelOrderRequest(BaseModel):
    reason: str

class OrderCreateRequest(BaseModel):
    items: List[Dict[str, object]]
    total_amount: float
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

class OrderController(Controller):
    """R2: Class-based Litestar Controller for Order operations."""
    path = "/api/v1/orders"
    guards = [PermissionGuard("order:read")]

    @post("/", guards=[])  # PUBLIC: Storefront Checkout
    async def create_order(self, request: Request, db_session: AsyncSession, data: OrderCreateRequest) -> dict[str, object]:
        """PUBLIC: Handle storefront checkout via OrderService."""
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "unknown")

        return await order_service.create_order(
            session=db_session,
            data=data.model_dump(),
            ip=ip,
            ua=ua
        )

    @get("/")
    async def list_orders(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict[str, object]:
        """List orders via OrderService."""
        return await order_service.list_orders(
            session=db_session,
            limit=limit,
            offset=offset,
            status=status,
            search=search
        )

    @get("/{order_id:str}")
    async def get_order(self, db_session: AsyncSession, order_id: str) -> dict[str, object]:
        """Get a single order via OrderService."""
        return await order_service.get_order(db_session, order_id)

    @patch("/{order_id:str}/status", guards=[PermissionGuard("order:write")])
    async def update_order_status(self, request: Request, db_session: AsyncSession, order_id: str, data: OrderStatusUpdate) -> dict[str, object]:
        """Update order status via OrderService."""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub", "System")

        return await order_service.update_status(
            session=db_session,
            order_id=order_id,
            new_status=data.status,
            actor=user_email
        )

    @patch("/{order_id:str}/cancel", guards=[PermissionGuard("order:write")])
    async def cancel_order(self, request: Request, db_session: AsyncSession, order_id: str, data: CancelOrderRequest) -> dict[str, object]:
        """Cancel an order via OrderService."""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub", "System")

        return await order_service.cancel_order(
            session=db_session,
            order_id=order_id,
            reason=data.reason,
            actor=user_email
        )

    @patch("/{order_id:str}/spam", guards=[PermissionGuard("order:write")])
    async def toggle_order_spam(self, request: Request, db_session: AsyncSession, order_id: str) -> dict[str, object]:
        """Toggle order spam status via OrderService."""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub", "System")

        return await order_service.toggle_spam(
            session=db_session,
            order_id=order_id,
            actor=user_email
        )
