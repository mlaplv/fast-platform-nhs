import uuid
import hashlib
import unicodedata
import logging
from typing import Optional, TypedDict, Dict, List
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, ProductBase, ProductVariant
from backend.database.models.auth import User
from backend.schemas.client.checkout import StealthCheckoutSchema
from backend.database import current_tenant_id
from backend.services.event_bus import event_bus
from backend.utils.device import is_mobile_device
from litestar.exceptions import NotFoundException, ValidationException
from backend.services.commerce.promotion import PromotionService

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
    name: Optional[str]
    address: Optional[str]


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
    payment_method: str
    shipping_fee: float
    customer_note: str
    custom_requests: List[Dict[str, object]]
    gift_info: Dict[str, object]
    voucher_id: str

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
        
        # [ELITE V2.2] Pre-calculate total quantity per product for tier resolution (Sync with Frontend)
        total_qty_by_product: Dict[str, int] = {}
        for item in payload.items:
            total_qty_by_product[item.product_id] = total_qty_by_product.get(item.product_id, 0) + item.quantity

        # Ensure compatibility layer (Seed defaults if needed)
        await PromotionService.ensure_default_vouchers(db_session)

        for item in payload.items:
            product_stmt = select(ProductBase).where(ProductBase.id == item.product_id).options(sa.orm.selectinload(ProductBase.variants))
            product_res = await db_session.execute(product_stmt)
            product = product_res.scalar_one_or_none()
            if not product:
                logger.error(f"[CHECKOUT] Product {item.product_id} not found")
                raise NotFoundException(f"Sản phẩm {item.product_id} không tồn tại")
            
            # ELITE V2.2: DYNAMIC TIER PRICING ENGINE (Lazada/TikTok Style)
            # Find all potential combo variants
            combo_variants = [v for v in product.variants if v.attributes and v.attributes.get("combo_qty")]
            
            db_price = None
            resolved_variant_id = item.variant_id
            
            # Use total quantity of this product across all lines for tier resolution
            total_qty = total_qty_by_product.get(item.product_id, item.quantity)

            if combo_variants:
                # 1. Mandatory Qty Constraint Check (Security)
                selected_v = next((v for v in combo_variants if v.id == item.variant_id), None)
                if selected_v:
                    min_qty = int(selected_v.attributes.get("combo_qty", 1))
                    # Note: We check against total_qty because multiple lines can satisfy the combo
                    if total_qty < min_qty:
                        logger.error(f"[SECURITY-ALERT] Invalid Combo Qty: Total={total_qty} < Min={min_qty} for product {item.product_id}")
                        raise ValidationException(f"Gói này yêu cầu tổng tối thiểu {min_qty} sản phẩm cùng loại.")

                # 2. Dynamic Price Resolution (The "Reward" Logic)
                # Find the best tier matching total quantity (Highest combo_qty <= total_qty)
                sorted_tiers = sorted(combo_variants, key=lambda v: int(v.attributes.get("combo_qty", 0)), reverse=True)
                best_tier = next((v for v in sorted_tiers if int(v.attributes.get("combo_qty", 0)) <= total_qty), None)
                
                if best_tier:
                    db_price = best_tier.discount_price if best_tier.discount_price is not None else best_tier.price
                else:
                    # Fallback to base product price if quantity is below all combo tiers
                    db_price = product.discount_price if product.discount_price is not None else product.price
            else:
                # STANDARD PRODUCT (Isolation Mode)
                if item.variant_id:
                    variant_stmt = select(ProductVariant).where(ProductVariant.id == item.variant_id)
                    variant_res = await db_session.execute(variant_stmt)
                    variant = variant_res.scalar_one_or_none()
                    if not variant:
                        logger.error(f"[CHECKOUT] Variant {item.variant_id} not found")
                        raise NotFoundException(f"Biến thể {item.variant_id} không tồn tại")
                    db_price = variant.discount_price if variant.discount_price is not None else variant.price
                else:
                    db_price = product.discount_price if product.discount_price is not None else product.price

            # [VIRAL 2026 SECURITY] Rigorous Item Price Check
            if db_price is None: db_price = 0.0
            if abs(item.price - db_price) > 1.0: # Allow small rounding deltas
                 logger.warning(f"[STRIKE-PRICE] Item price mismatch for {product.name} ({item.product_id}): ItemPayload={item.price}, ResolvedDB={db_price}. LineQty={item.quantity}, TotalQty={total_qty}")
                 raise ValidationException("Giá sản phẩm đã thay đổi theo chương trình khuyến mãi. Vui lòng cập nhật lại giỏ hàng.")

            items_list.append({
                "id": item.product_id,
                "name": product.name,
                "variant_id": item.variant_id,
                "qty": item.quantity,
                "unit_price": db_price,
                "total_price": db_price * item.quantity
            })

        # [VIRAL 2026] RIGOROUS TOTAL VALIDATION
        base_subtotal = sum(it["total_price"] for it in items_list)
        
        # 1. Apply Combo Deals
        combo_deals = await PromotionService.get_active_combo_deals(db_session)
        combo_discount = PromotionService.calculate_combo_discount(items_list, combo_deals)
        
        # 2. Apply Voucher
        voucher_discount = 0.0
        if payload.voucher_id:
            voucher = await PromotionService.get_active_voucher(db_session, payload.voucher_id)
            if voucher:
                # Voucher applies on subtotal AFTER combo discount
                voucher_discount = PromotionService.calculate_voucher_discount(base_subtotal - combo_discount, voucher)
            else:
                logger.warning(f"[VOUCHER-FAIL] Voucher {payload.voucher_id} not found or inactive.")
                # We don't necessarily fail here if the price check passes, 
                # but the expected_total calculation below will fail if client gởi total đã trừ voucher ảo.

        expected_total = base_subtotal - combo_discount - voucher_discount + payload.shipping_fee
        
        # 3. Final Manipulation Lock
        if abs(expected_total - payload.total_amount) > 1.0:
            logger.error(f"[SECURITY-ALERT] Price Manipulation Attempt: Expected {expected_total}, Got {payload.total_amount}. Phone: {payload.customer_phone}")
            raise ValidationException("Đơn hàng chưa được bảo vệ thành công do thay đổi về giá hoặc khuyến mãi. Vui lòng tải lại trang.")


        # 5. Prepare Order Metadata
        order_metadata: OrderMetadata = {
            "items": items_list,
            "is_mobile": is_mobile_device(user_agent),
            "payment_method": payload.payment_method,
            "shipping_fee": payload.shipping_fee,
            "combo_discount": combo_discount,
            "voucher_discount": voucher_discount
        }

        if payload.voucher_id:
            order_metadata["voucher_id"] = payload.voucher_id
            # 🚀 [ELITE V2.2] ACCOUNTING: Increment voucher usage & protect against abuse
            await PromotionService.validate_and_use_voucher(db_session, payload.voucher_id, payload.customer_phone)
        
        if payload.note:
            order_metadata["customer_note"] = payload.note

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
            logger.info(f"[ELITE-V2.2] Custom product requests received: {len(custom_items_list)} items for phone {payload.customer_phone}")

        # 5.6 Handle Gift Info (Elite V2.2)
        if payload.gift_info:
            order_metadata["gift_info"] = {
                "sender_name": payload.gift_info.sender_name,
                "sender_phone": payload.gift_info.sender_phone,
                "message": payload.gift_info.message,
                "packaging": payload.gift_info.packaging,
                "scheduled_at": payload.gift_info.scheduled_at.isoformat() if payload.gift_info.scheduled_at else None,
                "recurring_type": payload.gift_info.recurring_type,
                "recurring_metadata": payload.gift_info.recurring_metadata
            }
            logger.info(f"[ELITE-V2.2] Gift info received for order phone {payload.customer_phone}")

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
        ox_cookie: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> LookupResult:
        """Recognition with Identity Shield Cookie V3.0."""
        last_order = None
        
        # ELITE V2.2: Phase A - Priority Lookup by User ID (Verified Identity)
        if user_id:
            stmt = (
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            res = await db_session.execute(stmt)
            last_order = res.scalar_one_or_none()
            if last_order:
                logger.info(f"[CheckoutService] Identity match found by user_id={user_id}")

        # Phase B - Fallback/Stealth Lookup by Phone (Identity Shield)
        if not last_order and phone:
            stmt = (
                select(Order)
                .where(Order.customer_phone == phone)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            res = await db_session.execute(stmt)
            last_order = res.scalar_one_or_none()

        # Identity Shield V3.0: Trust via secure HttpOnly Cookie __ox
        is_trusted = (last_order.id == ox_cookie) if last_order and ox_cookie else False
        
        # ELITE V2.2: Full data return if authenticated user matches search context
        # 1. Matches by direct user_id OR 2. Phone matches but we found an order with the same user_id
        is_authenticated_match = (last_order.user_id == user_id) if last_order and user_id else False

        if last_order:
            return LookupResult(
                is_recurring=True,
                is_trusted_device=is_trusted,
                name_masked=_mask_name(last_order.customer_name),
                address_masked=_mask_address(last_order.customer_address),
                name=last_order.customer_name if is_authenticated_match else None,
                address=last_order.customer_address if is_authenticated_match else None
            )

        user_res = await db_session.execute(
            select(User)
            .where(User.username == phone)
            .limit(1)
        )
        user = user_res.scalar_one_or_none()
        if user:
            is_match = (user.id == user_id) if user_id else False
            return LookupResult(
                is_recurring=True,
                is_trusted_device=False,
                name_masked=_mask_name(user.name),
                address_masked=None,
                name=user.name if is_match else None,
                address=None
            )

        return LookupResult(
            is_recurring=False, 
            is_trusted_device=False, 
            name_masked=None, 
            address_masked=None,
            name=None,
            address=None
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
