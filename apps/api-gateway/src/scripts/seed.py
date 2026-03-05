import asyncio
import os
import bcrypt
import hashlib
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete, text
from sqlalchemy.orm import selectinload

from src.database import async_session_maker
from src.database.models import (
    User, Role, Permission, Category, ProductBase, 
    Article, Order, VoiceProfile, Notification, 
    Draft, AgentTelemetryLog, ChatMessage
)

# Domain SSOT
TENANT_ID = "smartshop"

def utcnow():
    return datetime.now(timezone.utc)

async def clear_data(session):
    """Clear old data (Rule R38 - Hard delete for seeding)."""
    print(f"🧹 Clearing old data for tenant: {TENANT_ID}...")
    
    # 1. Identify users to be cleared (to handle FKs correctly)
    stmt_user_ids = select(User.id).where((User.tenant_id == TENANT_ID) | (User.id == "user_admin"))
    res_user_ids = await session.execute(stmt_user_ids)
    user_ids = [u for u in res_user_ids.scalars().all()]
    
    # 2. Clear related data by Tenant ID
    await session.execute(delete(Order).where(Order.tenant_id == TENANT_ID))
    await session.execute(delete(Article).where(Article.tenant_id == TENANT_ID))
    await session.execute(delete(Notification).where(Notification.tenant_id == TENANT_ID))
    await session.execute(delete(Draft).where(Draft.tenant_id == TENANT_ID))
    await session.execute(delete(ChatMessage).where(ChatMessage.tenant_id == TENANT_ID))
    await session.execute(delete(AgentTelemetryLog).where(AgentTelemetryLog.tenant_id == TENANT_ID))
    await session.execute(delete(ProductBase).where(ProductBase.tenant_id == TENANT_ID))
    await session.execute(delete(Category).where(Category.tenant_id == TENANT_ID))
    
    # 3. Clear related data by User IDs (to catch records with different tenant_id but referencing our users)
    if user_ids:
        await session.execute(delete(Notification).where(Notification.user_id.in_(user_ids)))
        await session.execute(delete(Draft).where(Draft.reviewer_id.in_(user_ids)))
        await session.execute(delete(ChatMessage).where(ChatMessage.user_id.in_(user_ids)))
        await session.execute(delete(Order).where(Order.user_id.in_(user_ids)))
        await session.execute(delete(VoiceProfile).where(VoiceProfile.user_id.in_(user_ids)))

    # 4. Clear RBAC and Users
    await session.execute(delete(User).where(User.id.in_(user_ids)))
    await session.execute(delete(Role).where((Role.tenant_id == TENANT_ID) | (Role.id.in_(["role_superadmin", "role_customer"]))))
    
    await session.flush()

async def seed_rbac(session):
    """Setup RBAC roles and permissions (Rule R34, R36)."""
    print("🔐 Setting up RBAC...")
    
    # 1. Permissions (Global-ish)
    permission_defs = [
        ("Full System Access", "system:all"),
        ("Product Read", "product:read"),
        ("Product Write", "product:write"),
        ("Order Read", "order:read"),
        ("Order Write", "order:write"),
        ("User Read", "user:read"),
        ("User Create", "user:create"),
    ]
    
    perms = {}
    for name, code in permission_defs:
        stmt = select(Permission).where(Permission.code == code)
        res = await session.execute(stmt)
        p = res.scalar_one_or_none()
        if not p:
            p = Permission(id=f"perm_{code.replace(':', '_')}", name=name, code=code)
            session.add(p)
        perms[code] = p
    
    await session.flush()

    # 2. Roles
    super_admin_role = Role(
        id=f"role_superadmin",
        name="Super Administrator",
        code="SUPER_ADMIN",
        tenant_id=TENANT_ID
    )
    super_admin_role.permissions = list(perms.values())
    
    customer_role = Role(
        id=f"role_customer",
        name="Customer",
        code="CUSTOMER",
        tenant_id=TENANT_ID
    )
    customer_role.permissions = [perms["product:read"], perms["order:read"]]
    
    session.add_all([super_admin_role, customer_role])
    await session.flush()
    return super_admin_role

async def seed_users(session, admin_role):
    """Create initial users (Rule R31, R32)."""
    print("👤 Creating users...")
    
    email = os.getenv("ADMIN_EMAIL", "admin@smartshop.test")
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin@123A3%StrongPassword")
    
    # Hash password correctly (Frontend: SHA256 -> Backend: bcrypt)
    sha256_hex = hashlib.sha256(password.encode('utf-8')).hexdigest()
    hashed_password = bcrypt.hashpw(sha256_hex.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    admin = User(
        id="user_admin",
        email=email,
        username=username,
        name="Xohi Administrator",
        password=hashed_password,
        status="ACTIVE",
        tenant_id=TENANT_ID
    )
    admin.roles.append(admin_role)
    session.add(admin)
    
    # Add Voice Profile for Admin (Rule R30)
    voice_profile = VoiceProfile(
        id=str(uuid.uuid4()),
        user_id=admin.id,
        wake_words=["hey so hi", "hay xo hi, hey so he"],
        sleep_words=["cút", "tạm biệt"],
        greeting_template="Tao là bố bé xô hi, mờ lập đây.",
        capabilities={
            "READ": True,
            "COUNT": True,
            "MUTATE": True,
            "ANALYZE": True
        }
    )
    session.add(voice_profile)
    
    await session.flush()
    return admin

async def seed_categories(session):
    """Build category tree."""
    print("📂 Seeding categories...")
    categories_data = [
        {"name": "Thời trang Nam", "slug": "nam", "id": "cat_nam"},
        {"name": "Thời trang Nữ", "slug": "nu", "id": "cat_nu"},
    ]
    
    cat_objs = []
    for d in categories_data:
        c = Category(id=d["id"], name=d["name"], slug=d["slug"], tenant_id=TENANT_ID)
        session.add(c)
        cat_objs.append(c)
    
    await session.flush()
    
    # Subcategories
    sub_cats = [
        {"name": "Áo Sơ Mi", "slug": "ao-so-mi", "parent": "cat_nam", "id": "cat_ao_so_mi"},
        {"name": "Quần Jean", "slug": "quan-jean", "parent": "cat_nam", "id": "cat_quan_jean"},
        {"name": "Đầm & Váy", "slug": "dam-vay", "parent": "cat_nu", "id": "cat_dam_vay"},
    ]
    
    for d in sub_cats:
        sc = Category(id=d["id"], name=d["name"], slug=d["slug"], parent_id=d["parent"], tenant_id=TENANT_ID)
        session.add(sc)
    
    await session.flush()

async def seed_products(session):
    """Seed 50 products across categories."""
    print("👕 Seeding 50 products...")
    cat_ids = ["cat_ao_so_mi", "cat_quan_jean", "cat_dam_vay"]
    names = [
        "Áo Thun Oversize", "Quần Jean Denim", "Đầm Hoa Vintage", "Áo Khoác Bomber",
        "Váy Midi Lụa", "Áo Polo Classic", "Quần Kaki Slim", "Đầm Maxi Boho",
        "Áo Sơ Mi Oxford", "Quần Short Cargo", "Chân Váy Xếp Ly", "Áo Blazer Oversized",
        "Quần Jogger", "Áo Croptop", "Váy Bodycon", "Áo Hoodie",
        "Quần Culottes", "Đầm Cocktail", "Áo Len Cổ Lọ", "Quần Ống Rộng",
    ]
    statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "DRAFT"]
    products = []
    for i in range(50):
        pid = f"prod_{i+1:03d}"
        name = f"{random.choice(names)} V{i+1}"
        sku = f"SKU-{i+1:04d}"
        price = random.randint(15, 200) * 10000
        p_data = {"id": pid, "name": name, "sku": sku, "price": price, "cat": random.choice(cat_ids)}
        products.append(p_data)
        pb = ProductBase(
            id=pid, name=name, sku=sku, price=price,
            stock=random.randint(10, 500),
            status=random.choice(statuses),
            category_id=p_data["cat"],
            tenant_id=TENANT_ID
        )
        session.add(pb)
    await session.flush()
    print(f"   → Created {len(products)} products")
    return products

async def seed_articles(session, author_id):
    """Seed 30 news articles."""
    print("📰 Seeding 30 articles...")
    titles = [
        "Xu hướng thời trang", "Bí quyết phối đồ", "Chính sách đổi trả",
        "Sale cuối mùa", "Lookbook mới nhất", "Hướng dẫn chọn size",
        "Chất liệu bền vững", "Tips bảo quản quần áo", "Street style",
        "Phong cách công sở", "Thời trang dạo phố", "Cập nhật BST mới",
    ]
    cats = ["Tin tức", "Chính sách"]
    statuses = ["PUBLISHED", "PUBLISHED", "DRAFT"]
    for i in range(30):
        title = f"{random.choice(titles)} #{i+1}"
        unique_id = f"{i+1}-{uuid.uuid4().hex[:6]}"
        slug = f"article-{unique_id}"
        art = Article(
            id=str(uuid.uuid4()), title=title, slug=slug,
            content=f"Nội dung bài viết {title}. Lorem ipsum dolor sit amet.",
            status=random.choice(statuses),
            category=random.choice(cats),
            author_id=author_id,
            tenant_id=TENANT_ID,
            created_at=utcnow() - timedelta(days=random.randint(0, 60))
        )
        session.add(art)
    await session.flush()
    print("   → Created 30 articles")

async def seed_orders(session, user_id, products_data):
    """Seed random orders for metrics testing (Rule R1.5)."""
    print("🛒 Seeding orders...")
    statuses = ["PENDING", "PAID", "SHIPPED", "COMPLETED"]
    
    for _ in range(100):
        # Pick 1-2 items
        items = []
        total = 0
        for _ in range(random.randint(1, 2)):
            p = random.choice(products_data)
            qty = random.randint(1, 3)
            subtotal = p["price"] * qty
            total += subtotal
            items.append({
                "sku": p["sku"],
                "name": p["name"],
                "quantity": qty,
                "price": p["price"],
                "total": subtotal
            })
        
        # Random date in last 30 days
        created = utcnow() - timedelta(days=random.randint(0, 30))
        
        ord_obj = Order(
            id=str(uuid.uuid4()),
            user_id=user_id,
            total_amount=total,
            status=random.choice(statuses),
            items=items,
            tenant_id=TENANT_ID,
            created_at=created
        )
        session.add(ord_obj)
    
    await session.flush()

async def main():
    print("🚀 Starting Modernized Seed Process...")
    async with async_session_maker() as session:
        try:
            await clear_data(session)
            admin_role = await seed_rbac(session)
            admin_user = await seed_users(session, admin_role)
            await seed_categories(session)
            prods = await seed_products(session)
            await seed_articles(session, admin_user.id)
            await seed_orders(session, admin_user.id, prods)
            
            await session.commit()
            print("✨ Seeding completed successfully!")
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main())
