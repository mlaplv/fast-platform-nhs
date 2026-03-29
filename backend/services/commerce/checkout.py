import uuid
import hashlib
from typing import Optional, TypedDict, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, ProductBase, ProductVariant
from backend.schemas.client.checkout import StealthCheckoutSchema
from litestar.exceptions import NotFoundException

class OrderBumpMetadata(TypedDict):
    name: str
    price: float
    original_price: float

class CheckoutResult(TypedDict):
    id: str
    ok: bool
    message: Optional[str]

class OrderItem(TypedDict):
    id: str
    qty: int
    price: float

class OrderMetadata(TypedDict, total=False):
    items: List[OrderItem]
    order_bump: OrderBumpMetadata

class CheckoutService:
    @staticmethod
    async def create_stealth_order(
        db_session: AsyncSession,
        payload: StealthCheckoutSchema,
        customer_ip: str,
        user_agent: str
    ) -> CheckoutResult:
        # 1. Anti-Fraud Logic (Simple Hash Device/IP)
        fingerprint = hashlib.sha256(f"{customer_ip}|{user_agent}".encode()).hexdigest()

        # Check for recent identical orders (Simple spam protection)
        stmt = select(Order).where(
            Order.customer_ip == customer_ip,
            Order.fingerprint == fingerprint,
            Order.status == "PENDING"
        ).limit(1)

        result = await db_session.execute(stmt)
        existing_order = result.scalar_one_or_none()

        # 2. Fake Success for Bot/Spam (Rule R03)
        if existing_order:
            return {"id": str(uuid.uuid4()), "ok": True, "message": "Order processed (Cached)"}

        # 3. Fetch Product Price
        product_stmt = select(ProductBase).where(ProductBase.id == payload.product_id)
        product_res = await db_session.execute(product_stmt)
        product = product_res.scalar_one_or_none()

        if not product:
            raise NotFoundException(f"Sản phẩm {payload.product_id} không tồn tại")

        price = product.price

        # Handle Variant Price if applicable
        if payload.variant_id:
            variant_stmt = select(ProductVariant).where(ProductVariant.id == payload.variant_id)
            variant_res = await db_session.execute(variant_stmt)
            variant = variant_res.scalar_one_or_none()
            if variant:
                price = variant.price

        # 4. Calculate Total + Order Bump
        total_amount = float(price * payload.quantity)
        
        items: List[OrderItem] = [{"id": payload.product_id, "qty": payload.quantity, "price": float(price)}]
        order_metadata: OrderMetadata = {"items": items}

        if payload.has_order_bump:
            # R00 Compliance: Get price from metadata (Dynamic), fallback to CTO base if missing
            metadata = product.product_metadata or {}
            order_bump_price = float(metadata.get("order_bump_price", 99000.0))

            total_amount += order_bump_price
            order_metadata["order_bump"] = OrderBumpMetadata(
                name=str(metadata.get("order_bump_name", "Xịt Khử Mùi Giày Nano")),
                price=order_bump_price,
                original_price=float(metadata.get("order_bump_original_price", 250000.0))
            )

        # 5. Save Order
        new_order = Order(
            id=str(uuid.uuid4()),
            user_id="SYSTEM_CLIENT", # Anonymous client order
            total_amount=total_amount,
            status="PENDING",
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            customer_ip=customer_ip,
            fingerprint=fingerprint,
            order_metadata=order_metadata
        )

        db_session.add(new_order)
        await db_session.commit()

        return {"id": new_order.id, "ok": True, "message": None}
