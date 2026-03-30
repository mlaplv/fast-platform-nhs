import uuid
import hashlib
import unicodedata
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


def _normalize_name(s: str) -> str:
    """Normalize VN name for comparison: lowercase, strip accents/whitespace."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower().strip())
        if unicodedata.category(c) != "Mn"
    )

def _mask_name(name: str) -> str:
    if not name: return ""
    parts = name.split()
    if len(parts) == 1:
        return f"{name[0]}***"
    return f"{parts[0][0]}*** {' '.join([p[0]+'**' for p in parts[1:-1]])} {parts[-1]}".replace("  ", " ")

def _mask_address(addr: str) -> str:
    if not addr: return ""
    # Che phần giữa, giữ lại đầu và cuối (tỉnh/thành)
    parts = addr.split(",")
    if len(parts) < 2:
        return f"{addr[:5]}*******"
    street = parts[0].strip()
    masked_street = f"{street[:4]}*******"
    return f"{masked_street}, {', '.join(parts[1:])}"


class LookupResult(TypedDict):
    is_recurring: bool
    is_trusted_device: bool
    name_masked: Optional[str]
    address_masked: Optional[str]


class VerifyResult(TypedDict):
    verified: bool
    address: Optional[str]


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
        from backend.services.anti_spam import anti_spam_service

        is_spam, reason, score, device_hash = await anti_spam_service.check_order_spam(
            ip=customer_ip,
            user_agent=user_agent,
            tenant_id=current_tenant_id.get() or "default",
            order_data={
                "phone": payload.customer_phone,
                "name": payload.customer_name,
                "address": payload.customer_address,
                "items": [{"product_id": payload.product_id, "quantity": payload.quantity}]
            },
            is_campaign_mode=True # Assassin Funnel usually runs on Ads
        )

        if is_spam:
            logger.warning(f"[STRIKE] Spam Order Detected: {reason} (Score: {score}) | IP: {customer_ip}")
            # R2026: Elite V2.2: We proceed to save but mark as spam to prevent 404 and allow tracking

        user_stmt = select(User).where(User.username == payload.customer_phone).limit(1)
        user_res = await db_session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                username=payload.customer_phone,
                email=f"{payload.customer_phone}@shadow.test",
                name=payload.customer_name,
                status="ACTIVE",
                tenant_id=current_tenant_id.get() or "default",
                password="SHADOW_ACCOUNT"
            )
            db_session.add(user)

        product_stmt = select(ProductBase).where(ProductBase.id == payload.product_id)
        product_res = await db_session.execute(product_stmt)
        product = product_res.scalar_one_or_none()
        if not product:
            raise NotFoundException(f"Sản phẩm {payload.product_id} không tồn tại")

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

        # 6. Identity Shield v2.2: Restore original data if masked strings were submitted
        # This prevents the UI from ever seeing the clear text, but saving it correctly.
        final_name = payload.customer_name
        final_address = payload.customer_address
        
        # Look up most recent order to compare masked values
        restore_stmt = select(Order).where(Order.customer_phone == payload.customer_phone).order_by(Order.created_at.desc()).limit(1)
        restore_res = await db_session.execute(restore_stmt)
        prev_order = restore_res.scalar_one_or_none()
        
        if prev_order:
            if final_name == _mask_name(prev_order.customer_name):
                final_name = prev_order.customer_name
            if final_address == _mask_address(prev_order.customer_address):
                final_address = prev_order.customer_address

        # 5. Save Order
        new_order = Order(
            id=str(uuid.uuid4()),
            user_id=user.id, # Linked to auto-created user
            total_amount=total_amount,
            status="PENDING",
            items=items,
            customer_name=final_name,
            customer_phone=payload.customer_phone,
            customer_address=final_address,
            customer_ip=customer_ip,
            tenant_id=current_tenant_id.get() or "default",
            device_hash=device_hash,
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

    @staticmethod
    async def lookup_customer(
        db_session: AsyncSession,
        phone: str,
        ox_cookie: Optional[str] = None
    ) -> LookupResult:
        """Recognition with Identity Shield Cookie V3.0."""
        stmt = (
            select(Order)
            .where(Order.customer_phone == phone)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        res = await db_session.execute(stmt)
        last_order = res.scalar_one_or_none()

        if last_order:
            # Identity Shield V3.0: Trust via secure HttpOnly Cookie __ox
            is_trusted = (last_order.id == ox_cookie) if ox_cookie else False
            return LookupResult(
                is_recurring=True,
                is_trusted_device=is_trusted,
                name_masked=_mask_name(last_order.customer_name),
                address_masked=_mask_address(last_order.customer_address)
            )

        user_res = await db_session.execute(
            select(User).where(User.username == phone).limit(1)
        )
        user = user_res.scalar_one_or_none()
        if user:
            return LookupResult(
                is_recurring=True,
                is_trusted_device=False,
                name_masked=_mask_name(user.name),
                address_masked=None
            )

        return LookupResult(
            is_recurring=False, 
            is_trusted_device=False, 
            name_masked=None, 
            address_masked=None
        )

    @staticmethod
    async def verify_identity(
        db_session: AsyncSession,
        phone: str,
        name: str
    ) -> VerifyResult:
        """Verify Phone + Name match to unlock Address (Identity Shield)."""
        res = await db_session.execute(
            select(Order)
            .where(Order.customer_phone == phone)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        last_order = res.scalar_one_or_none()

        if not last_order:
            return VerifyResult(verified=False, address=None)

        stored_name = _normalize_name(last_order.customer_name or "")
        input_name = _normalize_name(name)

        if input_name == stored_name:
            return VerifyResult(verified=True, address=last_order.customer_address)

        return VerifyResult(verified=False, address=None)
