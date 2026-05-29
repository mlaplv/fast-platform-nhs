import os
import sys
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
from backend.database.models import ProductBase, ProductVariant, ProductEmbedding
from backend.scripts.seed_data import PRODUCT_DEFS
from sqlalchemy import select, delete

TENANT_ID = os.getenv("APP_DOMAIN", "osmo")

async def fix_db():
    print("🚀 Fixing DB: Restoring old data & updating viral features...")
    async with async_session_maker() as session:
        # 1. Delete junk products created by mistake
        junk_slugs = [
            "miccosmo-beppin-body-virgin-white-serum-30g",
            "miccosmo-hurry-harry-premium-neck-cream-rich-40gr"
        ]
        
        for slug in junk_slugs:
            junk = (await session.execute(select(ProductBase).where(ProductBase.slug == slug))).scalar_one_or_none()
            if junk:
                # Delete dependencies
                await session.execute(delete(ProductEmbedding).where(ProductEmbedding.product_base_id == junk.id))
                await session.execute(delete(ProductVariant).where(ProductVariant.product_base_id == junk.id))
                await session.execute(delete(ProductBase).where(ProductBase.id == junk.id))
                print(f"🧹 Cleaned up junk product: {slug}")

        # 2. Recreate prod_miccosmo_virgin_white with exact old data + viral
        old_virgin_white = (await session.execute(select(ProductBase).where(ProductBase.id == "prod_miccosmo_virgin_white"))).scalar_one_or_none()
        
        if not old_virgin_white:
            # Find the original definition
            def_data = next(p for p in PRODUCT_DEFS if p["id"] == "prod_miccosmo_virgin_white")
            
            # Merge viral metadata
            metadata = def_data["product_metadata"].copy()
            metadata.update({
                "likes": 4820,
                "offer_sales_label": "ĐÃ BÁN",
                "offer_rating_label": "4.9/5 RATING",
                "share_promotion": {
                    "enabled": True,
                    "voucher_id": "VIRAL50K",
                    "voucher_label": "Giảm 50.000₫",
                    "voucher_condition": "Cho đơn hàng mua qua link chia sẻ",
                    "cta_text": "Chia sẻ để nhận mã",
                    "share_text": "Bí quyết trắng hồng tức thì từ Nhật Bản! Cùng chia sẻ để nhận giảm giá 50k nhé!"
                }
            })
            
            # Dynamic images fallback for tier variations
            images = def_data.get("images", [])
            mobile_images = def_data.get("mobile_images", images)
            first_image = images[0] if images else None
            
            pb = ProductBase(
                id=def_data["id"],
                name=def_data["name"],
                slug=def_data["slug"],
                sku=def_data["sku"],
                price=def_data["price"],
                discount_price=def_data.get("discount_price"),
                stock=sum(v["stock"] for v in def_data.get("variants", [])) if "variants" in def_data else 999,
                status="ACTIVE",
                category_id=def_data["category_id"],
                tenant_id=TENANT_ID,
                short_description=def_data.get("short_description", ""),
                description=def_data.get("description", ""),
                images=images,
                mobile_images=mobile_images,
                product_metadata=metadata,
                tier_variations=[{
                    **tv,
                    "image": first_image,
                    "mobile_images": [first_image] * len(tv["options"]) if first_image else [None] * len(tv["options"])
                } for tv in def_data.get("tier_variations", [])]
            )
            session.add(pb)
            
            # Recreate variants
            for v_data in def_data.get("variants", []):
                variant = ProductVariant(
                    id=v_data["id"],
                    product_base_id=pb.id,
                    tier_index=v_data["tier_index"],
                    sku=v_data["sku"],
                    price=v_data["price"],
                    discount_price=v_data.get("discount_price"),
                    stock=v_data["stock"],
                    attributes=v_data.get("attributes", {})
                )
                session.add(variant)
            print("✅ Restored original Virgin White Serum with Viral features")
        else:
            # Heal missing images from seed definition only if completely empty in real DB
            if not old_virgin_white.images:
                old_virgin_white.images = def_data.get("images", [])
            if not old_virgin_white.mobile_images:
                old_virgin_white.mobile_images = old_virgin_white.images
            
            # Dynamically heal empty tier variation image keys using actual product images
            if old_virgin_white.images:
                first_img = old_virgin_white.images[0]
                tvs = []
                for tv in (old_virgin_white.tier_variations or []):
                    tv_copy = dict(tv)
                    if not tv_copy.get("image"):
                        tv_copy["image"] = first_img
                    if not tv_copy.get("mobile_images") or all(x is None for x in tv_copy.get("mobile_images", [])):
                        tv_copy["mobile_images"] = [first_img] * len(tv.get("options", ["1", "2", "3"]))
                    tvs.append(tv_copy)
                old_virgin_white.tier_variations = tvs

            metadata = dict(old_virgin_white.product_metadata) if old_virgin_white.product_metadata else {}
            metadata.update({
                "likes": 4820,
                "offer_sales_label": "ĐÃ BÁN",
                "offer_rating_label": "4.9/5 RATING",
                "share_promotion": {
                    "enabled": True,
                    "voucher_id": "VIRAL50K",
                    "voucher_label": "Giảm 50.000₫",
                    "voucher_condition": "Cho đơn hàng mua qua link chia sẻ",
                    "cta_text": "Chia sẻ để nhận mã",
                    "share_text": "Bí quyết trắng hồng tức thì từ Nhật Bản! Cùng chia sẻ để nhận giảm giá 50k nhé!"
                }
            })
            old_virgin_white.product_metadata = metadata
            print("✅ Updated Virgin White Serum with Viral features")
 
         # 3. Update existing Hurry Harry Neck Cream
        neck_cream = (await session.execute(select(ProductBase).where(ProductBase.id == "prod_hurry_harry_neck_cream"))).scalar_one_or_none()
        if neck_cream:
            metadata = dict(neck_cream.product_metadata) if neck_cream.product_metadata else {}
            metadata.update({
                "likes": 5120,
                "offer_sales_label": "ĐÃ BÁN",
                "offer_rating_label": "4.9/5 RATING",
                "share_promotion": {
                    "enabled": True,
                    "voucher_id": "VIRAL50K",
                    "voucher_label": "Giảm 50.000₫",
                    "voucher_condition": "Áp dụng lập tức",
                    "cta_text": "Chia sẻ nhận khuyến mãi",
                    "share_text": "Xóa mờ nếp nhăn vùng cổ với Hurry Harry Premium! Giảm 50K khi chia sẻ."
                }
            })
            
            # Heal missing images from legacy seed or pos URL if completely empty in real DB
            if not neck_cream.images:
                neck_cream.images = ["https://pos.nvncdn.com/3a1578-211785/ps/20250716_t2xmZQtxvN.jpeg?v=1752656410"]
            if not neck_cream.mobile_images:
                neck_cream.mobile_images = neck_cream.images
                
            # Dynamically heal empty tier variation image keys using actual product images
            if neck_cream.images:
                first_img = neck_cream.images[0]
                tvs = []
                for tv in (neck_cream.tier_variations or []):
                    tv_copy = dict(tv)
                    if not tv_copy.get("image"):
                        tv_copy["image"] = first_img
                    if not tv_copy.get("mobile_images") or all(x is None for x in tv_copy.get("mobile_images", [])):
                        tv_copy["mobile_images"] = [first_img] * len(tv.get("options", ["1", "2", "3"]))
                    tvs.append(tv_copy)
                neck_cream.tier_variations = tvs

            neck_cream.product_metadata = metadata
            print("✅ Updated Hurry Harry Neck Cream with Viral features")
        else:
            print("❌ Could not find prod_hurry_harry_neck_cream to update!")

        await session.commit()
        print("✨ Database fixed and perfectly updated!")

if __name__ == "__main__":
    asyncio.run(fix_db())
