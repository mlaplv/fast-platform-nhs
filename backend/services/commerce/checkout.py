import uuid
import hashlib
from typing import Optional, TypedDict, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, ProductBase, ProductVariant
from backend.database.models.auth import User
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

class OrderItem(TypedDict, total=False):
    id: str
    variant_id: Optional[str]
    qty: int
    unit_price: float
    total_price: float

class OrderMetadata(TypedDict, total=False):
    items: List[OrderItem]
    applied_deal: Dict # Using Dict to avoid circular or complex TypedDict nesting for now

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

        # 2. Auto-Registration / User Lookup (Elite V2.2)
        # Check if user exists by phone
        user_stmt = select(User).where(User.username == payload.customer_phone).limit(1)
        user_res = await db_session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            # Create new shadow user thưa sếp!
            user = User(
                id=str(uuid.uuid4()),
                username=payload.customer_phone,
                full_name=payload.customer_name,
                role="CLIENT",
                is_active=True,
                # In 2026 Stealth flow, password is set via OTP later thưa sếp!
                password_hash="SHADOW_ACCOUNT_V2.2" 
            )
            db_session.add(user)
            # We don't commit yet, we want the order and user in the same transaction thưa sếp!

        # 2b. Fake Success for Bot/Spam (Rule R03)
        if existing_order:
            return {"id": str(uuid.uuid4()), "ok": True, "message": "Order processed (Cached)"}

        # 3. Fetch Product Pricing (Elite V2.2: Zero-Hardcode)
        product_stmt = select(ProductBase).where(ProductBase.id == payload.product_id)
        product_res = await db_session.execute(product_stmt)
        product = product_res.scalar_one_or_none()
        if not product:
            raise NotFoundException(f"Sản phẩm {payload.product_id} không tồn tại")

        # Determine base unit price: Priority to Variant Discount -> Variant Price -> Product Discount -> Product Price
        price = product.discount_price or product.price

        if payload.variant_id:
            variant_stmt = select(ProductVariant).where(ProductVariant.id == payload.variant_id)
            variant_res = await db_session.execute(variant_stmt)
            variant = variant_res.scalar_one_or_none()
            if variant:
                price = variant.discount_price or variant.price

        # 4. Calculate Total with Promotion Engine (ELITE V2.2 thưa sếp!)
        metadata = product.product_metadata or {}
        active_deals = metadata.get("active_deals", [])
        
        # Sort deals by total bundle size (descending) to apply the largest deal first
        sorted_deals = sorted(
            active_deals, 
            key=lambda d: int(d.get("buy_qty", 0)) + int(d.get("get_qty", 0)), 
            reverse=True
        )

        total_amount = 0.0
        applied_deal_info = None

        if sorted_deals:
            for deal in sorted_deals:
                buy_qty = int(deal.get("buy_qty", 0))
                get_qty = int(deal.get("get_qty", 0))
                fixed_price = float(deal.get("fixed_price", 0))
                total_in_bundle = buy_qty + get_qty

                if total_in_bundle > 0 and payload.quantity >= total_in_bundle:
                    bundle_count = payload.quantity // total_in_bundle
                    remainder = payload.quantity % total_in_bundle
                    
                    total_amount = (bundle_count * fixed_price) + (remainder * float(price))
                    applied_deal_info = {
                        "id": deal.get("id"),
                        "label": deal.get("label", "Ưu đãi Combo"),
                        "bundle_count": bundle_count,
                        "deal_price": fixed_price
                    }
                    break
            
        if not applied_deal_info:
            total_amount = float(price * payload.quantity)

        # 5. Prepare Order Metadata
        items: List[OrderItem] = [{
            "id": payload.product_id, 
            "variant_id": payload.variant_id,
            "qty": payload.quantity, 
            "unit_price": float(price),
            "total_price": total_amount
        }]
        order_metadata: OrderMetadata = {"items": items}
        if applied_deal_info:
            order_metadata["applied_deal"] = applied_deal_info

        # 5. Save Order
        new_order = Order(
            id=str(uuid.uuid4()),
            user_id=user.id, # Linked to auto-created user thưa sếp!
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
