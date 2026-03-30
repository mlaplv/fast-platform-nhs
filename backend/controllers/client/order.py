from typing import Optional, List
from litestar import Controller, get, patch, post, Request
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.order import OrderResponse, PublicOrderResponse
from backend.services.commerce.order import order_service
from pydantic import BaseModel, Field

class OrderUpdateSchema(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    customer_address: Optional[str] = Field(None, min_length=5, max_length=500)

class PublicOrderController(Controller):
    """Elite V2.2: Public Order Controller for Client Success Page."""
    path = "/api/v1/client/orders"

    @get("/{order_id:str}", guards=[])  # PUBLIC access for success page
    async def get_public_order(
        self,
        request: Request,
        db_session: AsyncSession,
        order_id: str,
        phone: Optional[str] = None
    ) -> PublicOrderResponse:
        """PUBLIC: Get a single order by ID for the confirmation page.
        Security: MUST verify phone and Identity Shield Cookie (__ox).
        """
        from litestar.exceptions import ValidationException

        # R2026: Mandatory Phone Verification
        if not phone:
             raise ValidationException("Vui lòng cung cấp số điện thoại để tra cứu đơn hàng")

        # Identity Shield V3.0: Read HttpOnly Cookie
        ox_cookie = request.cookies.get("__ox")

        # Pass cookie down to service for trust evaluation
        order_res = await order_service.get_order(db_session, order_id, ox_cookie=ox_cookie)

        # R2026: Elite Phone Normalization (Digits Only)
        clean_search = "".join(filter(str.isdigit, phone))
        clean_order = "".join(filter(str.isdigit, order_res.customerPhone or ""))

        if not clean_search or clean_search != clean_order:
            raise ValidationException("Số điện thoại không khớp với hồ sơ đơn hàng")

        # Elite V3.0: Redact sensitive data if device is NOT trusted by Cookie
        if not order_res.is_trusted_device:
            order_res.customerName = order_res.name_masked
            order_res.customerAddress = order_res.address_masked

        return PublicOrderResponse.model_validate(order_res.model_dump())

    @patch("/{order_id:str}", guards=[])
    async def update_public_order(
        self,
        db_session: AsyncSession,
        order_id: str,
        data: OrderUpdateSchema,
        phone: Optional[str] = None # REQUIRE PHONE
    ) -> PublicOrderResponse:
        """PUBLIC: Update shipping info for a pending order."""
        from backend.database.models.commerce import Order
        from litestar.exceptions import NotFoundException, ValidationException
        from sqlalchemy import select

        if not phone:
            raise ValidationException("Vui lòng cung cấp số điện thoại để cập nhật đơn hàng")

        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException("Order not found")

        # Verify Phone for Update
        clean_search = "".join(filter(str.isdigit, phone))
        clean_order = "".join(filter(str.isdigit, order.customer_phone or ""))
        if clean_search != clean_order:
            raise ValidationException("Xác thực số điện thoại thất bại")

        if order.status != "PENDING":
            raise ValidationException("Only pending orders can be edited")

        if data.customer_name: order.customer_name = data.customer_name
        if data.customer_phone: order.customer_phone = data.customer_phone
        if data.customer_address: order.customer_address = data.customer_address

        await db_session.commit()
        # Return updated order via public schema
        updated_order = await order_service.get_order(db_session, order_id)
        return PublicOrderResponse.model_validate(updated_order.model_dump())

    @post("/{order_id:str}/cancel", guards=[], status_code=HTTP_200_OK)
    async def cancel_public_order(
        self,
        db_session: AsyncSession,
        order_id: str,
        phone: Optional[str] = None # REQUIRE PHONE
    ) -> dict:
        """PUBLIC: Cancel a pending order."""
        from litestar.exceptions import ValidationException
        if not phone:
            raise ValidationException("Vui lòng cung cấp số điện thoại để hủy đơn hàng")

        # Verify Phone via Service
        order_res = await order_service.get_order(db_session, order_id)
        clean_search = "".join(filter(str.isdigit, phone))
        clean_order = "".join(filter(str.isdigit, order_res.customerPhone or ""))
        if clean_search != clean_order:
            raise ValidationException("Xác thực số điện thoại thất bại")

        await order_service.cancel_order(
            db_session,
            order_id,
            reason="Cancelled by customer via Success Page",
            actor_email="customer@stealth.test"
        )
        await db_session.commit()
        return {"ok": True, "message": "Đơn hàng đã được hủy thành công"}
