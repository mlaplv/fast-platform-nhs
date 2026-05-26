import uuid
import logging
from typing import Optional, TypedDict, Dict, List
import sqlalchemy as sa
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.commerce import Order, ProductBase, ProductVariant, UserLoyalty, PointTransaction
from backend.database.models.promotion import Voucher, ComboDeal
from backend.database.models.auth import User
from backend.schemas.client.checkout import StealthCheckoutSchema
from litestar.exceptions import ValidationException, NotFoundException
from backend.database import current_tenant_id
from backend.services.event_bus import event_bus
from backend.utils.device import is_mobile_device
from backend.services.commerce.promotion import PromotionService
from backend.services.commerce.loyalty import LoyaltyService
from backend.services.commerce.logic.identity_shield import IdentityShield, LookupResult, VerifyResult, _mask_name, _mask_address
from backend.database.models.system import SystemSetting
from backend.constants.commerce import ShippingConfig, LoyaltyConfig, CheckoutConfig
from backend.services.anti_spam import anti_spam_service
from backend.services.commerce.logic.pricing_engine import PricingEngine
from backend.schemas.pricing import PricingInputItem


logger = logging.getLogger("api-gateway")


# Elite V2.2: Identity logic moved to identity_shield.py (R00 Compliance)


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
    name: str       
    variant_id: Optional[str]
    variant_name: Optional[str]
    qty: int        
    unit_price: float 
    total_price: float
    image: Optional[str]

class OrderMetadata(TypedDict, total=False):
    items: List[OrderItem]
    applied_deal: Optional[Dict[str, object]]
    is_mobile: bool
    payment_method: str
    shipping_fee: float
    combo_discount: float
    voucher_discount: float
    voucher_ids: List[str]
    customer_note: str
    custom_requests: List[Dict[str, object]]
    gift_info: Dict[str, object]
    points_redeemed: int
    point_discount_amount: float


class CheckoutService:
    @staticmethod
    async def create_stealth_order(
        db_session: AsyncSession,
        payload: StealthCheckoutSchema,
        customer_ip: str,
        user_agent: str,
        user_id: Optional[str] = None
    ) -> CheckoutResult:

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
            # [T-16] BLOCK Tier Enforcement: Nếu score >= 90 (BLOCK), từ chối ngay lập tức
            if score >= anti_spam_service.BLOCK_THRESHOLD_SCORE:
                logger.error(f"[SECURITY-BLOCK] Hard Blocked Spam Order: {reason} (Score: {score}) | Phone: {payload.customer_phone} | IP: {customer_ip}")
                raise ValidationException("Hệ thống phát hiện dấu hiệu bất thường. Vui lòng liên hệ quản trị viên để được hỗ trợ.")
            
            # Tier 1 & 2 (Audit/Challenge): Vẫn cho phép lưu đơn để tracking nhưng mark as spam
            logger.warning(f"[STRIKE] Spam Order Logged: {reason} (Score: {score}) | Phone: {payload.customer_phone} | IP: {customer_ip}")
            # R2026: Elite V2.2: We proceed to save but mark as spam to prevent 404 and allow tracking

        # ELITE V2.2: AUTH-AWARE IDENTITY RESOLUTION
        user = None
        
        # 1. First priority: Use the authenticated user ID passed from controller
        if user_id:
            user_stmt = select(User).where(User.id == user_id).limit(1)
            user_res = await db_session.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            if user:
                logger.info(f"[Checkout] Linking order to authenticated user: {user_id}")
                # Update phone if missing from profile but provided in checkout
                if not user.phone:
                    user.phone = payload.customer_phone

        # 2. Second priority: Fallback to phone-based lookup (Shadow accounts or returning guests)
        if not user:
            user_stmt = select(User).where(User.username == payload.customer_phone).limit(1)
            user_res = await db_session.execute(user_stmt)
            user = user_res.scalar_one_or_none()

            if not user:
                # 3. Create Shadow Account if absolutely no matching user found
                user = User(
                    id=str(uuid.uuid4()),
                    username=payload.customer_phone,
                    phone=payload.customer_phone,
                    email=f"{payload.customer_phone}{CheckoutConfig.SHADOW_EMAIL_DOMAIN}",
                    name=payload.customer_name,
                    status="ACTIVE",
                    tenant_id=current_tenant_id.get() or "default",
                    password=CheckoutConfig.SHADOW_PASSWORD_MARKER
                )
                db_session.add(user)
                logger.info(f"[Checkout] Created new shadow account for phone: {payload.customer_phone}")

        # Build items list with correct prices
        items_list: List[OrderItem] = []

        # [ELITE V2.2] Pre-calculate total quantity per product for tier resolution (Sync with Frontend)
        total_qty_by_product: Dict[str, int] = {}
        for item in payload.items:
            total_qty_by_product[item.product_id] = total_qty_by_product.get(item.product_id, 0) + item.quantity

        # [SECURITY M-01] BATCH LOAD — Xoá N+1: 1 query cho tất cả products + variants
        all_product_ids = list({item.product_id for item in payload.items})
        all_variant_ids = [item.variant_id for item in payload.items if item.variant_id]

        products_stmt = (
            select(ProductBase)
            .where(ProductBase.id.in_(all_product_ids))
            .options(sa.orm.selectinload(ProductBase.variants))
        )
        products_res = await db_session.execute(products_stmt)
        products_map: Dict[str, ProductBase] = {p.id: p for p in products_res.scalars().all()}

        # Batch load orphan variants (không nằm trong selectinload nếu product_id mismatch)
        variants_map: Dict[str, ProductVariant] = {}
        if all_variant_ids:
            variants_stmt = select(ProductVariant).where(ProductVariant.id.in_(all_variant_ids))
            variants_res = await db_session.execute(variants_stmt)
            variants_map = {v.id: v for v in variants_res.scalars().all()}

        # [ELITE V2.2] Price protection & tier resolution logic...
        original_subtotal = 0.0

        for item in payload.items:
            # Lấy từ map đã batch load — không cần thêm query
            product = products_map.get(item.product_id)
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
                    db_price = best_tier.discount_price or best_tier.price
                else:
                    # Fallback to base product price if quantity is below all combo tiers
                    db_price = product.discount_price or product.price
            else:
                # STANDARD PRODUCT (Isolation Mode)
                if item.variant_id:
                    # Lấy từ variants_map batch đã load — không query thêm
                    variant = (
                        next((v for v in product.variants if v.id == item.variant_id), None)
                        or variants_map.get(item.variant_id)
                    )
                    if not variant:
                        logger.error(f"[CHECKOUT] Variant {item.variant_id} not found")
                        raise NotFoundException(f"Biến thể {item.variant_id} không tồn tại")
                    db_price = variant.discount_price or variant.price
                else:
                    db_price = product.discount_price or product.price

            # [VIRAL 2026 SECURITY] Rigorous Item Price Check
            if db_price is None:
                db_price = 0.0
            if abs(item.price - db_price) > CheckoutConfig.PRICE_TOLERANCE_VND:
                logger.warning(f"[STRIKE-PRICE] Item price mismatch for {product.name} ({item.product_id}): ItemPayload={item.price}, ResolvedDB={db_price}. LineQty={item.quantity}, TotalQty={total_qty}")
                raise ValidationException("Giá sản phẩm đã thay đổi theo chương trình khuyến mãi. Vui lòng cập nhật lại giỏ hàng.")

            # Resolve readable variant name from attributes (if variant exists)
            variant_name = None
            v_obj = None
            if item.variant_id:
                v_obj = (
                    next((v for v in product.variants if v.id == item.variant_id), None)
                    or variants_map.get(item.variant_id)
                )
                if v_obj:
                    # Elite V2.2: Deterministic Variant Truth via Tier Index Mapping
                    tier_names = []
                    if getattr(v_obj, 'tier_index', None) and getattr(product, 'tier_variations', None):
                        for i, t_idx in enumerate(v_obj.tier_index):
                            if i < len(product.tier_variations):
                                tier = product.tier_variations[i]
                                options = tier.get("options", [])
                                if isinstance(options, list) and isinstance(t_idx, int) and t_idx < len(options):
                                    tier_names.append(str(options[t_idx]))

                    if tier_names:
                        variant_name = " - ".join(tier_names)
                    elif getattr(v_obj, 'attributes', None):
                        # Fallback for systems without tier_variations (Scalar values only)
                        filtered_attrs = [str(v) for k, v in v_obj.attributes.items()
                                          if str(k).lower() not in ["combo_qty", "comboqty", "gifts"]
                                          and isinstance(v, (str, int, float, bool))]
                        if filtered_attrs:
                            variant_name = " - ".join(filtered_attrs)

            # [M-03] Fix: Calculate Base Listed Price for audit — không dùng try/except silent-fail
            base_listed_price = product.price or 0.0
            if item.variant_id and v_obj:
                base_listed_price = v_obj.price or product.price or 0.0
            original_subtotal += base_listed_price * item.quantity

            # Resolve promotional gifts for order item (Elite V2.2)
            item_gifts = []
            if v_obj and getattr(v_obj, 'attributes', None) and isinstance(v_obj.attributes, dict):
                item_gifts = v_obj.attributes.get("gifts") or []
            
            if not item_gifts and getattr(product, 'gifts', None):
                item_gifts = product.gifts

            items_list.append({
                "id": item.product_id,
                "name": product.name,
                "slug": getattr(product, 'slug', ''),
                "variant_id": item.variant_id,
                "variant_name": variant_name,  # Elite V2.2: Include human readable name
                "qty": item.quantity,
                "unit_price": db_price,
                "total_price": db_price * item.quantity,
                "image": product.images[0] if product.images else None,
                "gifts": item_gifts
            })



        # 1. Fetch Vouchers and Combo Deals
        # [M-02] Batch fetch vouchers — xoá N+1 (giảm từ 3 query xuống 1 query/voucher)
        vouchers: List[Voucher] = []
        vouchers_map: Dict[str, Voucher] = {}
        if payload.voucher_ids:
            # [T-15] BATCH LOAD VOUCHERS
            vouchers_stmt = select(Voucher).where(
                and_(
                    Voucher.id.in_(payload.voucher_ids),
                    Voucher.is_active == True
                )
            )
            v_res = await db_session.execute(vouchers_stmt)
            for v in v_res.scalars().all():
                vouchers.append(v)
                vouchers_map[str(v.id)] = v

        # [ELITE V2.2] Chặn cấp độ backend cho phạm vi áp dụng (Product Scope Enforcement)
        for v in vouchers:
            applicable_product_ids = []
            if v.metadata_json and isinstance(v.metadata_json, dict):
                applicable_product_ids = v.metadata_json.get("applicable_product_ids") or []
            
            if applicable_product_ids:
                has_eligible = False
                eligible_raw_subtotal = 0.0
                # Normalize voucher applicable product list (lowercase, stripped)
                norm_applicable_ids = [str(x).strip().lower() for x in applicable_product_ids]

                for it in items_list:
                    p_id = str(it["id"]).strip().lower()
                    p_slug = str(it.get("slug") or "").strip().lower()
                    if p_id in norm_applicable_ids or p_slug in norm_applicable_ids:
                        has_eligible = True
                        eligible_raw_subtotal += it["total_price"]
                
                if not has_eligible:
                    raise ValidationException(f"Mã giảm giá {v.id} chỉ áp dụng cho một số sản phẩm nhất định trong danh sách quy định.")
                
                if eligible_raw_subtotal < v.min_spend:
                    raise ValidationException(
                        f"Mã giảm giá {v.id} yêu cầu đơn tối thiểu {v.min_spend:,.0f}đ cho các sản phẩm được áp dụng (hiện tại có {eligible_raw_subtotal:,.0f}đ)."
                    )
        
        combo_deals = await PromotionService.get_active_combo_deals(db_session)
        
        # 2. Get User Loyalty Context [ELITE V2.2]
        available_points = 0
        point_value = LoyaltyConfig.POINT_VALUE
        loyalty = None
        if user_id:
            # [SECURITY P-02] Chỉ lock row khi thực sự cần trừ điểm
            loyalty_query = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
            if payload.points_redeemed and payload.points_redeemed > 0:
                loyalty_query = loyalty_query.with_for_update()
            l_res = await db_session.execute(loyalty_query)
            loyalty = l_res.scalar_one_or_none()
            if loyalty:
                available_points = loyalty.available_points

        # 3. UNIFIED PRICING CALCULATION (Elite V2.2)
        
        pricing_input = [
            PricingInputItem(
                product_id=it["id"],
                name=it["name"],
                quantity=it["qty"],
                unit_price=it["unit_price"]
            ) for it in items_list
        ]
        
        pricing = PricingEngine.calculate(
            items=pricing_input,
            vouchers=vouchers,
            combo_deals=combo_deals,
            points_to_redeem=payload.points_redeemed,
            available_points=available_points,
            point_value_vnd=point_value,
            base_shipping_fee=payload.shipping_fee
        )

        expected_total = pricing.final_payable
        point_discount = pricing.point_discount_amount
        applied_voucher_ids = pricing.applied_voucher_ids
        # [SECURITY M-05] Dùng giá trị đã clamped từ engine, KHÔNG dùng payload raw để tránh balance âm
        points_actually_used = pricing.points_redeemed
        if user_id and loyalty and points_actually_used > 0:
            loyalty.available_points -= points_actually_used

        # 3. Final Manipulation Lock
        # [SECURITY C-03] Floor check — chặn near-zero dollar exploit
        if expected_total < CheckoutConfig.MIN_ORDER_AMOUNT:
            logger.error(f"[SECURITY-ALERT] Near-Zero Order Blocked. ExpectedTotal={expected_total}, MIN={CheckoutConfig.MIN_ORDER_AMOUNT}, Phone={payload.customer_phone}")
            raise ValidationException(f"Giá trị đơn hàng tối thiểu là {CheckoutConfig.MIN_ORDER_AMOUNT:,.0f}đ sau tất cả giảm giá.")

        if expected_total < (original_subtotal * 0.5):
            logger.error(f"[SECURITY-ALERT] Extreme Discount Blocked. Total={expected_total}, Original={original_subtotal}, Phone={payload.customer_phone}")
            raise ValidationException("Hệ thống từ chối đơn hàng: Tổng thanh toán không được thấp hơn 50% tổng giá niêm yết.")

        if abs(expected_total - payload.total_amount) > CheckoutConfig.TOTAL_TOLERANCE_VND:
            logger.error(f"[SECURITY-ALERT] Price Manipulation Attempt: Expected {expected_total}, Got {payload.total_amount}. Sub={pricing.subtotal}, Combo={pricing.combo_discount}, Vouchers={pricing.voucher_discount}, Points={point_discount}, Ship={payload.shipping_fee}. Phone: {payload.customer_phone}")
            raise ValidationException("Đơn hàng chưa được bảo vệ thành công do thay đổi về giá hoặc khuyến mãi. Vui lòng tải lại trang.")

        # 5. Prepare Order Metadata
        order_metadata: OrderMetadata = {
            "items": items_list,
            "is_mobile": is_mobile_device(user_agent),
            "payment_method": payload.payment_method,
            "shipping_fee": payload.shipping_fee,
            "combo_discount": pricing.combo_discount,
            "voucher_discount": pricing.voucher_discount,
            "voucher_ids": applied_voucher_ids,
            "points_redeemed": payload.points_redeemed,
            "point_discount_amount": point_discount
        }

        # 🚀 [ELITE V2.2] ACCOUNTING: Atomic increment & protect against abuse for ALL applied vouchers
        # [M-02] Truyền voucher object đã fetch — không SELECT lại lần 3
        for v_id in applied_voucher_ids:
            await PromotionService.validate_and_use_voucher(
                db_session, v_id, payload.customer_phone, voucher=vouchers_map.get(v_id)
            )
        
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
            # [SECURITY H-04] Chỉ restore PII khi user_id khớp — chặn PII harvest attack
            # Kẻ tấn công biết SĐT có thể gửi masked name để bẫy backend restore tên thật
            is_same_user = (user and prev_order.user_id == user.id)
            if is_same_user:
                if final_name == _mask_name(prev_order.customer_name):
                    final_name = prev_order.customer_name
                if final_address == _mask_address(prev_order.customer_address):
                    final_address = prev_order.customer_address
            else:
                logger.debug(f"[IdentityShield] Skipping PII restore: user_id mismatch (order.user={prev_order.user_id}, current={user.id if user else 'None'})")

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
            order_metadata=order_metadata,
            points_redeemed=payload.points_redeemed,
            point_discount_amount=point_discount
        )

        db_session.add(new_order)
        
        # 🚀 [ELITE V2.2] LOYALTY: Track pending points for immediate client feedback
        if pricing.points_to_earn > 0:
            await LoyaltyService.register_pending_points(db_session, user.id, pricing.points_to_earn)
        
        # 5.1 Ghi log trừ điểm nếu có — dùng points_actually_used đã validated bởi engine
        if points_actually_used > 0:
            pt = PointTransaction(
                user_id=user.id,
                order_id=new_order.id,
                amount=-points_actually_used,
                transaction_type="REDEEM_ORDER",
                notes=f"Thanh toán một phần đơn hàng bằng điểm. (Chiết khấu 1% - Giá trị: {point_discount}đ)"
            )
            pt.integrity_token = LoyaltyService._create_transaction_token(pt)
            db_session.add(pt)
            
            # Reseal the definitive balance after all operations
            loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)

        await db_session.commit()

        # 🚀 [ELITE V2.2] AUTO-SAVE ADDRESS PROTOCOL
        if user and payload.customer_address:
            try:
                # 1. Parse current address components
                addr_parts = [p.strip() for p in payload.customer_address.split(',')]
                if len(addr_parts) >= 3:
                    province = addr_parts[-1]
                    ward = addr_parts[-2]
                    street = ", ".join(addr_parts[:-2])
                    
                    new_addr = {
                        "id": str(uuid.uuid4()),
                        "name": payload.customer_name,
                        "phone": payload.customer_phone,
                        "city": province,
                        "ward": ward,
                        "address": street,
                        "isDefault": False
                    }
                    
                    # 2. Update User Metadata
                    if not user.extra_metadata:
                        user.extra_metadata = {}
                    
                    addresses = user.extra_metadata.get("addresses", [])
                    
                    # 3. Duplicate Check (Nomalized)
                    def norm(s): return str(s or "").lower().strip()
                    exists = any(
                        norm(a.get("city")) == norm(province) and 
                        norm(a.get("ward")) == norm(ward) and 
                        norm(a.get("address")) == norm(street)
                        for a in addresses
                    )
                    
                    if not exists:
                        # Limit to 10 addresses (Elite V2.2 Discipline)
                        if len(addresses) >= 10:
                            addresses.pop(0) # Remove oldest
                        
                        # If first address, make it default
                        if not addresses:
                            new_addr["isDefault"] = True
                            
                        addresses.append(new_addr)
                        user.extra_metadata["addresses"] = addresses
                        sa.orm.attributes.flag_modified(user, "extra_metadata")
                        await db_session.commit()
            except Exception as e:
                logging.error(f"[Checkout] Failed to auto-save address: {str(e)}")


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
        """Recognition with Identity Shield Cookie V3.0 (Proxy to IdentityShield)."""
        return await IdentityShield.lookup_customer(db_session, phone, ox_cookie, user_id)

    @staticmethod
    async def verify_identity(
        db_session: AsyncSession,
        phone: str,
        name: str
    ) -> VerifyResult:
        """Verify Identity (Proxy to IdentityShield)."""
        return await IdentityShield.verify_identity(db_session, phone, name)
