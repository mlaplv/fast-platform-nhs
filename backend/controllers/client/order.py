from datetime import datetime, timezone
from typing import Optional, List
from litestar import Controller, get, patch, post, Request, Response
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.order import OrderResponse, PublicOrderResponse
from backend.services.commerce.order import order_service
from pydantic import BaseModel, Field
from litestar.datastructures import Cookie
from sqlalchemy import select
from backend.database.models.commerce import Order

class OrderUpdateSchema(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    customer_address: Optional[str] = Field(None, min_length=5, max_length=500)
    note: Optional[str] = Field(None, max_length=1000)

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
    ) -> Response:
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

        # Elite V4.0: Anti-Poaching Identity Shield
        # Only return full data if Device Fingerprint (__ox) matches or is recently verified
        is_trusted = False
        if ox_cookie:
            # Check if cookie matches order metadata fingerprint
            stored_ox = (order_res.orderMetadata or {}).get("ox_fingerprint")
            if stored_ox == ox_cookie:
                is_trusted = True

        response_data = PublicOrderResponse.model_validate(order_res, from_attributes=True)
        response_data = self._mask_pii(response_data, is_trusted)
                    
        # Elite V4.1: Cache-Busting Response
        return Response(
            content=response_data,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    def _mask_pii(self, response_data: PublicOrderResponse, is_trusted: bool) -> PublicOrderResponse:
        """Centralized Elite V4.0 Masking Engine."""
        response_data.is_trusted_device = is_trusted
        if not is_trusted:
            if response_data.customerName:
                parts = response_data.customerName.split()
                if len(parts) > 1:
                    response_data.customerName = f"{parts[0]} {' '.join(['*' for _ in parts[1:]])}"
                else:
                    response_data.customerName = response_data.customerName[0] + "***"
            
            if response_data.customerAddress:
                # Mask street but keep Ward/Province for recognition
                addr_parts = [p.strip() for p in response_data.customerAddress.split(",")]
                if len(addr_parts) >= 3:
                    masked_street = addr_parts[0][:4] + " ***"
                    response_data.customerAddress = f"{masked_street}, {', '.join(addr_parts[1:])}"
                else:
                    response_data.customerAddress = response_data.customerAddress[:10] + " ***"
                    
        return response_data

    @patch("/{order_id:str}", guards=[])
    async def update_public_order(
        self,
        request: Request,
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

        from backend.services.commerce.order import order_service
        
        # Support Suffix Lookup (Elite V2.2)
        try:
            order_res = await order_service.get_order(db_session, order_id)
            full_id = order_res.id
        except NotFoundException:
            raise NotFoundException(f"Order {order_id} not found")

        stmt = select(Order).where(Order.id == full_id)
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

        # Forensic Audit Log (Elite V2.2 Protocol)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        history = list(order.history or [])
        history.append({
            "status": order.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": f"Customer ({client_ip})",
            "note": f"Thông tin đơn hàng được cập nhật. IP: {client_ip}. Device: {user_agent[:50]}..."
        })
        order.history = history

        # Identity Fingerprinting (Security SOC)
        original_ua = (order.order_metadata or {}).get("user_agent")
        if original_ua and original_ua != user_agent:
            # Log as potential session hijacking / device switch
            from backend.services.commerce.order import logger
            logger.warning(f"🛡️ [SOC-ALERT] Order {order_id} edited from different device. Original: {original_ua[:30]}... Current: {user_agent[:30]}...")

        if data.customer_name: order.customer_name = data.customer_name
        if data.customer_phone: order.customer_phone = data.customer_phone
        if data.customer_address: order.customer_address = data.customer_address
        
        if data.note is not None:
            meta = dict(order.order_metadata or {})
            meta["customer_note"] = data.note
            order.order_metadata = meta

        # Atomic Sync: Flush then Commit
        await db_session.flush()
        
        # Preserve ID before session expiration
        order_uuid = order.id
        from backend.services.commerce.order import logger
        logger.info(f"🛡️ [DEEP-SYNC] Committing PII Update for {order_uuid}: {order.customer_name}")
        
        await db_session.commit()
        db_session.expire_all() # Force purge of identity map for Quantum Sync
        
        # Return updated order via public schema (Deep Sync from DB)
        updated_order = await order_service.get_order(db_session, order_uuid)
        response_data = PublicOrderResponse.model_validate(updated_order, from_attributes=True)
        
        # Persist trusted state (Elite V4.2 Unified)
        ox_cookie = request.cookies.get("__ox")
        is_trusted = bool(ox_cookie and (updated_order.orderMetadata or {}).get("ox_fingerprint") == ox_cookie)
        return self._mask_pii(response_data, is_trusted)

    @post("/{order_id:str}/cancel", guards=[], status_code=HTTP_200_OK)
    async def cancel_public_order(
        self,
        request: Request,
        db_session: AsyncSession,
        order_id: str,
        phone: Optional[str] = None # REQUIRE PHONE
    ) -> PublicOrderResponse:
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

        # Forensic Audit Log for Cancellation (Elite V2.2)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        await order_service.cancel_order(
            db_session,
            order_res.id, # Use full ID
            reason=f"Khách chủ động hủy qua trang Thành công. IP: {client_ip}. UA: {user_agent[:50]}...",
            actor_email=f"customer@{client_ip}"
        )
        # Preserve ID before session expiration
        order_uuid = order_res.id
        await db_session.commit()
        db_session.expire_all()
        
        # Deep Sync: Return the freshly cancelled order state
        cancelled_order = await order_service.get_order(db_session, order_uuid)
        response_data = PublicOrderResponse.model_validate(cancelled_order, from_attributes=True)

        # Persist trusted state
        ox_cookie = request.cookies.get("__ox")
        is_trusted = bool(ox_cookie and (cancelled_order.orderMetadata or {}).get("ox_fingerprint") == ox_cookie)
        return self._mask_pii(response_data, is_trusted)

    @post("/{order_id:str}/verify-full", guards=[], status_code=HTTP_200_OK)
    async def verify_full_identity(
        self,
        db_session: AsyncSession,
        order_id: str,
        data: dict # Ingest JSON Body
    ) -> Response:
        """PUBLIC: Verify full identity to unlock unmasked data and editing."""
        from litestar.exceptions import ValidationException
        from litestar.response import Response
        import uuid

        phone = data.get("phone")
        if not phone:
            raise ValidationException("Vui lòng cung cấp số điện thoại")

        # 1. Get Order (Suffix Support)
        try:
            order_res = await order_service.get_order(db_session, order_id)
        except:
            raise ValidationException("Đơn hàng không tồn tại")

        # 2. Verify Phone
        clean_search = "".join(filter(str.isdigit, phone))
        # Support both camelCase and snake_case from service result
        raw_order_phone = getattr(order_res, "customerPhone", None) or getattr(order_res, "customer_phone", "")
        clean_order = "".join(filter(str.isdigit, str(raw_order_phone or "")))
        
        if not clean_search or clean_search != clean_order:
            raise ValidationException("Số điện thoại không khớp với hồ sơ đơn hàng")

        # 3. Generate Fingerprint if missing or rotating
        new_fingerprint = str(uuid.uuid4())
        
        # 4. Bind Fingerprint to Order Metadata
        from backend.database.models.commerce import Order
        from sqlalchemy import select
        stmt = select(Order).where(Order.id == order_res.id)
        res = await db_session.execute(stmt)
        order = res.scalar_one()
        
        meta = dict(order.order_metadata or {})
        meta["ox_fingerprint"] = new_fingerprint
        order.order_metadata = meta
        
        await db_session.commit()

        # 5. Return response with HttpOnly cookie (Elite V4.0)
        from litestar.response import Response
        return Response(
            content={"ok": True, "message": "Xác thực danh tính thành công"},
            cookies=[
                Cookie(
                    key="__ox",
                    value=new_fingerprint,
                    httponly=True,
                    samesite="lax",
                    max_age=3600 * 24 * 7, # 7 days
                    path="/"
                )
            ]
        )
