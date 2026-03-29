from typing import Optional, List
from litestar import Controller, get, patch, post
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.order import OrderResponse
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
        db_session: AsyncSession,
        order_id: str,
        phone: Optional[str] = None
    ) -> OrderResponse:
        """PUBLIC: Get a single order by ID for the confirmation page.
        Security: optionally verify phone for tracking page lookups thưa sếp!
        """
        from litestar.exceptions import ValidationException
        
        if len(order_id) == 6 and not phone:
             raise ValidationException("Vui lòng cung cấp số điện thoại để tra cứu bằng mã rút gọn thưa sếp!")

        order_res = await order_service.get_order(db_session, order_id)
        
        if phone:
            # R2026: Elite Phone Normalization (Digits Only thưa sếp!)
            clean_search = "".join(filter(str.isdigit, phone))
            clean_order = "".join(filter(str.isdigit, order_res.customerPhone or ""))
            
            if not clean_search or clean_search != clean_order:
                raise ValidationException("Số điện thoại không khớp với hồ sơ đơn hàng thưa sếp!")
        
        return order_res

    @patch("/{order_id:str}", guards=[])
    async def update_public_order(
        self,
        db_session: AsyncSession,
        order_id: str,
        data: OrderUpdateSchema
    ) -> OrderResponse:
        """PUBLIC: Update shipping info for a pending order."""
        # Note: In a production Elite V2.2 system, we would verify IP/session here thưa sếp!
        from backend.database.models.commerce import Order
        from litestar.exceptions import NotFoundException, ValidationException
        from sqlalchemy import select

        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise NotFoundException("Order not found")
        
        if order.status != "PENDING":
            raise ValidationException("Only pending orders can be edited")

        if data.customer_name: order.customer_name = data.customer_name
        if data.customer_phone: order.customer_phone = data.customer_phone
        if data.customer_address: order.customer_address = data.customer_address

        await db_session.commit()
        return await order_service.get_order(db_session, order_id)

    @post("/{order_id:str}/cancel", guards=[], status_code=HTTP_200_OK)
    async def cancel_public_order(
        self,
        db_session: AsyncSession,
        order_id: str
    ) -> dict:
        """PUBLIC: Cancel a pending order."""
        await order_service.cancel_order(
            db_session, 
            order_id, 
            reason="Cancelled by customer via Success Page", 
            actor_email="customer@stealth.test"
        )
        await db_session.commit()
        return {"ok": True, "message": "Đơn hàng đã được hủy thành công thưa sếp!"}
