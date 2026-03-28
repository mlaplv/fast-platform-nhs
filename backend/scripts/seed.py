import asyncio
import os
import bcrypt
import hashlib
import uuid
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from dotenv import load_dotenv

import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path: sys.path.insert(0, project_root)

load_dotenv(os.path.realpath(os.path.join(os.path.dirname(__file__), "../../.env")))

from backend.database import async_session_maker
from backend.database.models import *
from backend.utils.security import GeminiSecurity
from backend.scripts.seed_data import GEMINI_KEYS, CATEGORY_DEFS, SUB_CATEGORY_DEFS, PRODUCT_DEFS, PRODUCT_NAMES, ARTICLE_TITLES
from backend.services.xohi.creative_studio.models.schemas import CategoryEnum

TENANT_ID = "smartshop"
def utcnow(): return datetime.now(timezone.utc)

async def clear_data(session):
    print(f"🧹 Clearing old data for tenant: {TENANT_ID}...")
    user_ids = (await session.execute(select(User.id).where((User.tenant_id == TENANT_ID) | (User.id == "user_admin")))).scalars().all()
    await session.execute(delete(ProductVariant))
    # Clear internal dependencies first thưa sếp!
    await session.execute(delete(ProductEmbedding).where(ProductEmbedding.product_base_id.in_(select(ProductBase.id).where(ProductBase.tenant_id == TENANT_ID))))
    for model in [Order, Article, Notification, Draft, ChatMessage, AgentTelemetryLog, CampaignEvent, ContentCampaign, ProductBase, Category, Appointment]:
        await session.execute(delete(model).where(model.tenant_id == TENANT_ID))
    if user_ids:
        for model in [Notification, Draft, CampaignEvent, ContentCampaign, ChatMessage, Order, VoiceProfile]:
            if hasattr(model, 'user_id'): await session.execute(delete(model).where(model.user_id.in_(user_ids)))
        await session.execute(delete(User).where(User.id.in_(user_ids)))
    await session.execute(delete(Role).where((Role.tenant_id == TENANT_ID) | (Role.id.in_(["role_superadmin", "role_customer"]))))
    await session.flush()

async def seed_rbac(session):
    print("🔐 Setting up RBAC...")
    perms = {}
    for name, code in [("Full Access", "system:all"), ("Product Read", "product:read"), ("Product Write", "product:write"), ("Order Read", "order:read"), ("Order Write", "order:write")]:
        p = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
        if not p: p = Permission(id=f"perm_{code.replace(':', '_')}", name=name, code=code); session.add(p)
        perms[code] = p
    await session.flush()
    s_role = Role(id="role_superadmin", name="Super Admin", code="SUPER_ADMIN", tenant_id=TENANT_ID, permissions=list(perms.values()))
    c_role = Role(id="role_customer", name="Customer", code="CUSTOMER", tenant_id=TENANT_ID, permissions=[perms["product:read"], perms["order:read"]])
    session.add_all([s_role, c_role]); await session.flush(); return s_role

async def seed_users(session, admin_role):
    print("👤 Creating users...")
    pwd = os.getenv("ADMIN_PASSWORD", "admin@123A3%StrongPassword")
    hpwd = bcrypt.hashpw(hashlib.sha256(pwd.encode()).hexdigest().encode(), bcrypt.gensalt()).decode()
    admin = User(id="user_admin", email=os.getenv("ADMIN_EMAIL", "admin@smartshop.test"), username=os.getenv("ADMIN_USERNAME", "admin"), name="Xohi", password=hpwd, status="ACTIVE", tenant_id=TENANT_ID)
    admin.roles.append(admin_role); session.add(admin)
    vp = VoiceProfile(id=str(uuid.uuid4()), user_id=admin.id, wake_words=["hey so hi"], sleep_words=["cút"], greeting_template="Bố đây.", capabilities={"READ":True,"COUNT":True,"MUTATE":True,"ANALYZE":True}, gemini_keys_enc=GeminiSecurity.encrypt_keys(GEMINI_KEYS), primary_model="gemini-2.5-flash", ai_models=["gemini-2.5-flash","gemini-1.5-pro","gemini-1.5-flash"])
    session.add(vp); await session.flush(); return admin

async def seed_categories(session):
    print("📂 Seeding categories...")
    for d in CATEGORY_DEFS: session.add(Category(id=d["id"], name=d["name"], slug=d["slug"], tenant_id=TENANT_ID))
    await session.flush()
    for d in SUB_CATEGORY_DEFS: session.add(Category(id=d["id"], name=d["name"], slug=d["slug"], parent_id=d["parent"], tenant_id=TENANT_ID))
    await session.flush()

async def seed_products(session):
    print(f"📦 Seeding {len(PRODUCT_DEFS)} products with variations...")
    products = []
    for d in PRODUCT_DEFS:
        pb = ProductBase(
            id=d["id"],
            name=d["name"],
            slug=d["slug"],
            sku=d["sku"],
            price=d["price"],
            discount_price=d.get("discount_price"),
            stock=sum(v["stock"] for v in d.get("variants", [])),
            status="ACTIVE",
            category_id=d["category_id"],
            tenant_id=TENANT_ID,
            short_description=d.get("short_description", ""),
            description=d.get("description", ""),
            images=d.get("images", []),
            tier_variations=d.get("tier_variations", [])
        )
        session.add(pb)
        
        # Seed variants if they exist
        if "variants" in d:
            for v_data in d["variants"]:
                variant = ProductVariant(
                    id=v_data["id"],
                    product_base_id=pb.id,
                    tier_index=v_data["tier_index"],
                    sku=v_data["sku"],
                    price=v_data["price"],
                    discount_price=v_data.get("discount_price"),
                    stock=v_data["stock"]
                )
                session.add(variant)
        
        products.append({"id": d["id"], "sku": d["sku"], "name": d["name"], "price": d["price"]})
    await session.flush()
    return products

async def seed_articles(session, author_id):
    print("📰 Seeding 3 articles...")
    for i in range(3):
        session.add(Article(
            id=str(uuid.uuid4()), 
            title=f"{random.choice(ARTICLE_TITLES)} #{i+1}", 
            slug=f"art-{i+1}-{uuid.uuid4().hex[:4]}", 
            content="<p>Dữ liệu mẫu từ hệ thống AI 2026. Công nghệ lõi đang được kích hoạt...</p>", 
            status="PUBLISHED", 
            category=random.choice([c.value for c in CategoryEnum]), 
            author_id=author_id, 
            tenant_id=TENANT_ID, 
            created_at=utcnow() - timedelta(days=random.randint(0, 30))
        ))
    await session.flush()

async def seed_orders(session, user_id, products):
    print("🛒 Seeding 15+ professional orders with 10-year history simulation...")
    
    # Configuration for identity-based history
    sep_tong_phone = "0988-888-888"
    vip_phone = "0909-999-999"
    guest_phone = "0123-456-789"

    # 1. Sếp Tổng: The VIP Elite (10 Orders History)
    for i in range(10):
        items, total = [], 0
        # Sếp Tổng always buys the deodorant + random items or multiple deodorants
        p_list = [random.choice(products)]
        for p in p_list:
            qty = random.randint(1, 3); sub = p["price"] * qty; total += sub
            items.append({"sku": p["sku"], "name": p["name"], "quantity": qty, "price": p["price"], "total": sub})
        
        status = "COMPLETED" if i % 4 != 0 else "CANCELLED" # 75% success rate
        
        session.add(Order(
            id=str(uuid.uuid4()), user_id=user_id, total_amount=total, 
            status=status, items=items, tenant_id=TENANT_ID,
            customer_name="Sếp Tổng (Elite)", customer_phone=sep_tong_phone,
            customer_address="Penthouse Bitexco, Q1, TP.HCM", customer_ip="1.1.1.1",
            fingerprint="elite_v2026_trace_001", order_metadata={"is_seeded": True},
            created_at=utcnow() - timedelta(days=i*45) # Every 1.5 months
        ))

    # 2. Khách VIP 2026: The Risky Customer (3+ Cancellations)
    reasons = ["Khách đổi ý", "Đặt thử cho vui", "Tìm thấy giá rẻ hơn", "Không nghe máy khi xác nhận"]
    for i in range(4):
        items, total = [], 0
        for _ in range(1):
            p = random.choice(products); qty = 1; sub = p["price"] * qty; total += sub
            items.append({"sku": p["sku"], "name": p["name"], "quantity": qty, "price": p["price"], "total": sub})
        
        status = "CANCELLED" if i < 3 else "COMPLETED"
        reason = random.choice(reasons) if status == "CANCELLED" else None
        
        session.add(Order(
            id=str(uuid.uuid4()), user_id=user_id, total_amount=total, 
            status=status, items=items, tenant_id=TENANT_ID,
            customer_name="Khách VIP 2026", customer_phone=vip_phone,
            customer_address="Landmark 81, Bình Thạnh, TP.HCM", customer_ip="8.8.8.8",
            fingerprint="viral_identity_fb_999", order_metadata={"is_seeded": True},
            cancellation_reason=reason,
            created_at=utcnow() - timedelta(days=i*5)
        ))

    # 3. Guest 2026: The New Customer (1 Pending)
    p = random.choice(products); total = p["price"]
    session.add(Order(
        id=str(uuid.uuid4()), user_id=user_id, total_amount=total, 
        status="PENDING", items=[{"sku": p["sku"], "name": p["name"], "quantity": 1, "price": p["price"], "total": total}], 
        tenant_id=TENANT_ID, customer_name="Guest 2026", customer_phone=guest_phone,
        customer_address="Chưa cập nhật", customer_ip="127.0.0.1",
        fingerprint="guest_fingerprint_abc123", order_metadata={"is_seeded": True},
        created_at=utcnow()
    ))

    await session.flush()

async def seed_system_settings(session):
    print("⚙️ Seeding system settings...")
    default_settings = {
        "basic_info": {
            "site_name": "SmartShop Xohi",
            "description": "Hệ thống bán hàng AI thế hệ mới 2026",
            "logo_desktop": None,
            "logo_mobile": None,
            "favicon": None
        },
        "contact_info": {
            "phone": "0901234567",
            "hotline": "1800-XOHI",
            "email": "contact@smartshop.test",
            "address": "Bitexco Financial Tower, Quận 1, TP.HCM",
            "working_hours": "8:00 - 22:00"
        },
        "social_media": [
            {"platform": "Facebook", "url": "https://facebook.com/xohi", "icon_url": None},
            {"platform": "Zalo", "url": "https://zalo.me/xohi", "icon_url": None},
            {"platform": "TikTok", "url": "https://tiktok.com/@xohi", "icon_url": None}
        ],
        "seo_analytics": {
            "meta_title": "SmartShop - Mua sắm thông minh cùng AI",
            "meta_description": "Trải nghiệm mua sắm cá nhân hóa với trợ lý ảo Xohi.",
            "meta_keywords": "AI, shopping, smartshop, xohi",
            "google_analytics_id": "G-XXXXXXXXXX",
            "facebook_pixel_id": "XXXXXXXXXXXXXXX"
        },
        "google_maps": {
            "map_iframe": "",
            "api_key": ""
        },
        "maintenance": {
            "is_enabled": False,
            "message": "Hệ thống đang bảo trì để nâng cấp Core AI. Vui lòng quay lại sau."
        }
    }
    
    # Check if exists
    stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
    existing = (await session.execute(stmt)).scalar_one_or_none()
    
    if not existing:
        session.add(SystemSetting(key="primary_config", value=default_settings))
    else:
        existing.value = default_settings
    
    await session.flush()

async def seed_appointments(session):
    print("📅 Seeding sample appointments...")
    now = utcnow()
    apps = [
        Appointment(
            id=str(uuid.uuid4()),
            title="Elite Strategic Planning",
            description="Phiên làm việc Neural đầu tiên để thiết lập lộ trình 2026.",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
            status="UPCOMING",
            tenant_id=TENANT_ID,
            recurring_type="none"
        ),
        Appointment(
            id=str(uuid.uuid4()),
            title="Neural Scout: Competitor Audit",
            description="Tự động quét và phân tích chiến lược của đối thủ hàng tuần.",
            start_time=now + timedelta(days=1, hours=10),
            end_time=now + timedelta(days=1, hours=11),
            status="UPCOMING",
            tenant_id=TENANT_ID,
            recurring_type="weekly",
            recurring_metadata={"days": [1]} # Monday
        )
    ]
    session.add_all(apps)
    await session.flush()

async def main():
    print("🚀 Starting Refactored Seed Process...")
    async with async_session_maker() as session:
        try:
            await clear_data(session); r = await seed_rbac(session); u = await seed_users(session, r)
            await seed_categories(session); p = await seed_products(session); await seed_articles(session, u.id); await seed_orders(session, u.id, p)
            await seed_appointments(session)
            await seed_system_settings(session)
            await session.commit(); print("✨ Successful!")
        except Exception as e: print(f"❌ Error: {e}"); await session.rollback(); raise

if __name__ == "__main__": asyncio.run(main())
