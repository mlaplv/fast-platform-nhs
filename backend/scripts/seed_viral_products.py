import os
import sys
import uuid
import asyncio
from pathlib import Path

# Fix python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker
from backend.database.models import ProductBase, ProductVariant, Voucher, Category, ProductEmbedding
from backend.utils.text import slugify

TENANT_ID = os.getenv("APP_DOMAIN", "osmo")

async def seed_viral_products():
    print("🚀 Seeding Viral Products...")
    async with async_session_maker() as session:
        # 0. Ensure category exists
        from sqlalchemy import select, delete
        cat_id = "cat_skincare"
        cat_exists = (await session.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()
        if not cat_exists:
            c = Category(id=cat_id, name="Skincare", slug="skincare", tenant_id=TENANT_ID)
            session.add(c)
            await session.flush()

        # 1. Create a viral voucher if it doesn't exist
        voucher_id = "VIRAL50K"
        v_stmt = select(Voucher).where(Voucher.id == voucher_id, Voucher.tenant_id == TENANT_ID)
        v_exists = (await session.execute(v_stmt)).scalar_one_or_none()
        if not v_exists:
            v = Voucher(
                id=voucher_id,
                type="FIXED",
                title="Giảm 50K",
                subtitle="Dành cho khách hàng chia sẻ",
                value=50000.0,
                min_spend=0.0,
                is_active=True,
                tenant_id=TENANT_ID
            )
            session.add(v)
            print(f"✅ Created Voucher: {voucher_id}")

        # 2. Define the two products
        products_data = [
            {
                "name": "Miccosmo Beppin Body Virgin White Serum 30g",
                "price": 290000,
                "discount_price": 249000,
                "short_description": "Serum dưỡng trắng da cơ thể, đặc trị vùng thâm nách, bẹn, nhũ hoa hiệu quả từ Nhật Bản.",
                "images": ["https://pub-f5d606138dc343bfa993eeb116812850.r2.dev/products/miccosmo/beppin_serum.webp"],
                "metadata": {
                    "likes": 4820,
                    "offer_sales_label": "ĐÃ BÁN",
                    "offer_rating_label": "4.9/5 RATING",
                    "share_promotion": {
                        "enabled": True,
                        "voucher_id": voucher_id,
                        "voucher_label": "Giảm 50.000₫",
                        "voucher_condition": "Cho đơn hàng mua qua link chia sẻ",
                        "cta_text": "Chia sẻ để nhận mã",
                        "share_text": "Bí quyết trắng hồng tức thì từ Nhật Bản! Cùng chia sẻ để nhận giảm giá 50k nhé!"
                    }
                }
            },
            {
                "name": "Miccosmo Hurry Harry Premium Neck Cream Rich 40gr",
                "price": 350000,
                "discount_price": 299000,
                "short_description": "Kem dưỡng chống lão hóa, mờ nếp nhăn và làm sáng vùng da cổ cao cấp.",
                "images": ["https://pub-f5d606138dc343bfa993eeb116812850.r2.dev/products/miccosmo/hurry_harry_neck.webp"],
                "metadata": {
                    "likes": 5120,
                    "offer_sales_label": "ĐÃ BÁN",
                    "offer_rating_label": "4.9/5 RATING",
                    "share_promotion": {
                        "enabled": True,
                        "voucher_id": voucher_id,
                        "voucher_label": "Giảm 50.000₫",
                        "voucher_condition": "Áp dụng lập tức",
                        "cta_text": "Chia sẻ nhận khuyến mãi",
                        "share_text": "Xóa mờ nếp nhăn vùng cổ với Hurry Harry Premium! Giảm 50K khi chia sẻ."
                    }
                }
            }
        ]

        # 3. Add products safely
        for data in products_data:
            slug = slugify(data["name"])
            
            # Remove old if exists so we can re-seed cleanly without breaking constraints
            old_p_stmt = select(ProductBase).where(ProductBase.slug == slug, ProductBase.tenant_id == TENANT_ID)
            old_p = (await session.execute(old_p_stmt)).scalar_one_or_none()
            if old_p:
                await session.execute(delete(ProductEmbedding).where(ProductEmbedding.product_base_id == old_p.id))
                await session.execute(delete(ProductVariant).where(ProductVariant.product_base_id == old_p.id))
                await session.execute(delete(ProductBase).where(ProductBase.id == old_p.id))
                print(f"♻️ Replaced old product: {slug}")

            p_id = f"prod_{uuid.uuid4().hex[:12]}"
            pb = ProductBase(
                id=p_id,
                name=data["name"],
                slug=slug,
                sku=f"SKU-{uuid.uuid4().hex[:8].upper()}",
                price=data["price"],
                discount_price=data["discount_price"],
                stock=100,
                status="ACTIVE",
                category_id=cat_id,
                tenant_id=TENANT_ID,
                short_description=data["short_description"],
                description=f"<p>{data['short_description']}</p>",
                images=data["images"],
                product_metadata=data["metadata"]
            )
            session.add(pb)
            
            # Add one variant
            v = ProductVariant(
                id=f"var_{uuid.uuid4().hex[:12]}",
                product_base_id=p_id,
                sku=f"VAR-{uuid.uuid4().hex[:8].upper()}",
                price=data["price"],
                discount_price=data["discount_price"],
                stock=100
            )
            session.add(v)
            print(f"✅ Created Product: {data['name']}")

        await session.commit()
        print("✨ Done seeding viral products!")

if __name__ == "__main__":
    asyncio.run(seed_viral_products())
