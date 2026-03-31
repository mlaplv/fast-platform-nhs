from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from backend.services.event_bus import event_bus
from backend.services.anti_spam import AntiSpamService

logger = logging.getLogger("api-gateway")
from litestar import Controller, get, patch, post, Request
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from typing import List, Dict, Optional, Union
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.orm import selectinload

from backend.database.repositories import OrderRepository, provide_order_repo
from backend.database.models import Order, User
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.utils.sql import escape_like
from backend.schemas.order import (
    OrderCreateRequest, OrderStatusUpdate, CancelOrderRequest, OrderPlanningRequest,
    OrderResponse, OrderListResponse
)
from backend.schemas.common import SuccessResponse
from backend.services.commerce.order import order_service

logger = logging.getLogger("api-gateway")

class OrderController(Controller):
    """R2: Class-based Litestar Controller for Order operations."""
    path = "/api/v1/orders"
    guards = [PermissionGuard(PermissionEnum.ORDER_READ)]
    dependencies = {"order_repo": Provide(provide_order_repo)}

    @post("/", guards=[])  # PUBLIC: Storefront Checkout
    async def create_order(self, request: Request, db_session: "AsyncSession", data: OrderCreateRequest) -> SuccessResponse:
        """PUBLIC: Handle storefront checkout with Anti-Spam Shield integration."""
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "unknown")

        res = await order_service.create_order(db_session, data, ip, ua)
        await db_session.commit()
        return res

    @get("/")
    async def list_orders(
        self,
        db_session: "AsyncSession",
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> OrderListResponse:
        """List orders (R76: Scalar Projection)."""
        return await order_service.list_orders(db_session, limit, offset, status, search)

    @get("/{order_id:str}")
    async def get_order(self, db_session: "AsyncSession", order_id: str) -> OrderResponse:
        """Get a single order (R76: Scalar Projection)."""
        return await order_service.get_order(db_session, order_id)

    @patch("/{order_id:str}/status", guards=[PermissionGuard(PermissionEnum.ORDER_WRITE)])
    async def update_order_status(self, request: Request, db_session: "AsyncSession", order_id: str, data: OrderStatusUpdate) -> SuccessResponse:
        """UPDATE order status with strict state machine validation and history."""
        user_state = request.scope.get("state", {}).get("user", {})
        user_email = user_state.get("sub", "System")

        res = await order_service.transition_status(db_session, order_id, data.status, user_email)
        await db_session.commit()
        return res

    @patch("/{order_id:str}/cancel", guards=[PermissionGuard(PermissionEnum.ORDER_WRITE)])
    async def cancel_order(self, request: Request, db_session: "AsyncSession", order_id: str, data: CancelOrderRequest) -> SuccessResponse:
        """Cancel an order with a reason."""
        user_state = request.scope.get("state", {}).get("user", {})
        user_email = user_state.get("sub", "System")

        res = await order_service.cancel_order(db_session, order_id, data.reason, user_email)
        await db_session.commit()
        return res

    @patch("/{order_id:str}/spam", guards=[PermissionGuard(PermissionEnum.ORDER_WRITE)])
    async def toggle_order_spam(self, request: Request, db_session: "AsyncSession", order_id: str) -> SuccessResponse:
        """Manually toggle the spam status of an order."""
        user_state = request.scope.get("state", {}).get("user", {})
        user_email = user_state.get("sub", "System")

        res = await order_service.toggle_spam(db_session, order_id, user_email)
        await db_session.commit()
        return res

    @patch("/{order_id:str}/planning", guards=[PermissionGuard(PermissionEnum.ORDER_WRITE)])
    async def update_order_planning(self, request: Request, db_session: "AsyncSession", order_id: str, data: OrderPlanningRequest) -> SuccessResponse:
        """Elite V2.2: Advanced Logistics Planning endpoint"""
        user_state = request.scope.get("state", {}).get("user", {})
        user_email = user_state.get("sub", "System")

        res = await order_service.update_planning(db_session, order_id, data, user_email)
        await db_session.commit()
        return res
