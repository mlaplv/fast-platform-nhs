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
from backend.utils.device import is_mobile_device
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
    applied_deal: Dict[str, object]
    is_mobile: bool

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
                "items": [{"product_id": item.product_id, "quantity": item.quantity} for item in payload.items]
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

        # Build items list with correct prices
        items_list: List[OrderItem] = []

        for item in payload.items:
            product_stmt = select(ProductBase).where(ProductBase.id == item.product_id)
            product_res = await db_session.execute(product_stmt)
            product = product_res.scalar_one_or_none()
            if not product:
                raise NotFoundException(f"Sản phẩm {item.product_id} không tồn tại")

            # Trust the frontend-validated price in payload for efficiency
            items_list.append({
                "id": item.product_id,
                "name": product.name,
                "variant_id": item.variant_id,
                "qty": item.quantity,
                "unit_price": item.price,
                "total_price": item.price * item.quantity
            })

        # 5. Prepare Order Metadata
        order_metadata: OrderMetadata = {
            "items": items_list,
            "is_mobile": is_mobile_device(user_agent)
        }

        if payload.voucher_id:
            order_metadata["voucher_id"] = payload.voucher_id

        # 5.5 Handle Custom Item Requests (Elite V2.2)
        custom_items_list = []
        if payload.custom_items:
            for c_item in payload.custom_items:
                custom_items_list.append({
                    "name": c_item.name,
                    "image": c_item.image_url,
                    "qty": c_item.quantity,
                    "estimated_price": c_item.price,
                    "is_custom": True
                })
            order_metadata["custom_requests"] = custom_items_list

        # 6. Identity Shield v2.2: Restore original data if masked strings were submitted
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
            user_id=user.id,
            total_amount=payload.total_amount,
            status="PENDING",
            items=items_list,
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
            "total_amount": payload.total_amount,
            "ip": customer_ip,
            "user_agent": user_agent,
            "tenant_id": current_tenant_id.get() or "default",
            "address": payload.customer_address,
            "items": items_list,
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
