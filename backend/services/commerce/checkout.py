import uuid
import hashlib
import logging
from typing import Optional, TypedDict, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, ProductBase, ProductVariant
from backend.database.models.auth import User
from backend.schemas.client.checkout import StealthCheckoutSchema
from backend.database import current_tenant_id
from backend.services.event_bus import event_bus
from litestar.exceptions import NotFoundException

logger = logging.getLogger("api-gateway")

class OrderBumpMetadata(TypedDict):
    name: str
    price: float
    original_price: float

class CheckoutResult(TypedDict):
    id: str
    ok: bool
    message: Optional[str]

class OrderItem(TypedDict, total=False):
    id: str         # Maps to product_id in schema
    name: str       # Product name for history
    variant_id: Optional[str]
    qty: int        # Maps to quantity in schema
    unit_price: float # Maps to price in schema
    total_price: float

class OrderMetadata(TypedDict, total=False):
    items: List[OrderItem]
    applied_deal: Dict[str, object] # Using Dict to avoid circular or complex TypedDict nesting for now

class CheckoutService:
    @staticmethod
    async def create_stealth_order(
        db_session: AsyncSession,
        payload: StealthCheckoutSchema,
        customer_ip: str,
        user_agent: str
    ) -> CheckoutResult:
        # 1. Fortress Mode: Real-time Anti-Spam Shield (Elite V2.2)
        from backend.services.anti_spam import anti_spam_service

        is_spam, reason, score, fingerprint = await anti_spam_service.check_order_spam(
            ip=customer_ip,
            user_agent=user_agent,
            tenant_id=current_tenant_id.get() or "default",
            order_data={
                "phone": payload.customer_phone,
                "address": payload.customer_address,
                "items": [{"product_id": payload.product_id, "quantity": payload.quantity}]
            },
            is_campaign_mode=True # Assassin Funnel usually runs on Ads
        )

        if is_spam:
            logger.warning(f"[STRIKE] Spam Order Detected: {reason} (Score: {score}) | IP: {customer_ip}")
            # R2026: Elite V2.2: We proceed to save but mark as spam to prevent 404 and allow tracking

        # 2. Auto-Registration / User Lookup (Elite V2.2)
        # Check if user exists by phone
        user_stmt = select(User).where(User.username == payload.customer_phone).limit(1)
        user_res = await db_session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            # Create new shadow user
            user = User(
                id=str(uuid.uuid4()),
                username=payload.customer_phone,
                email=f"{payload.customer_phone}@shadow.test",
                name=payload.customer_name,
                status="ACTIVE",
                tenant_id=current_tenant_id.get() or "default",
                # In 2026 Stealth flow, password is set via OTP later
                password="SHADOW_ACCOUNT_V2.2"
            )
            db_session.add(user)
            # We don't commit yet, we want the order and user in the same transaction

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

        # 4. Calculate Total with Promotion Engine (ELITE V2.2)
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
            "name": product.name, # SAVE NAME
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
            user_id=user.id, # Linked to auto-created user
            total_amount=total_amount,
            status="PENDING",
            items=items,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            customer_ip=customer_ip,
            tenant_id=current_tenant_id.get() or "default",
            fingerprint=fingerprint,
            is_spam=is_spam,
            spam_score=score,
            spam_reason=reason,
            order_metadata=order_metadata
        )

        db_session.add(new_order)
        await db_session.commit()

        # 6. Proactive Nerve System: Notify Zalo Intelligence (Elite V2.2)
        await event_bus.emit("ORDER_CREATED", {
            "id": new_order.id,
            "phone": payload.customer_phone,
            "customer": payload.customer_name,
            "total_amount": total_amount,
            "ip": customer_ip,
            "user_agent": user_agent,
            "tenant_id": current_tenant_id.get() or "default",
            "address": payload.customer_address,
            "items": items,
        })

        return {"id": new_order.id, "ok": True, "message": None}
