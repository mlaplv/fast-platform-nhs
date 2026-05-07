import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone
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
from backend.database.models import ProductBase
from sqlalchemy import select

async def update_features():
    target_slug = "miccosmo-beppin-body-virgin-white-serum-30g"
    print(f"🚀 Updating FULL Viral features for: {target_slug}")
    
    async with async_session_maker() as session:
        # Find product by slug
        stmt = select(ProductBase).where(ProductBase.slug == target_slug)
        product = (await session.execute(stmt)).scalar_one_or_none()
        
        if not product:
            print(f"❌ Product not found: {target_slug}")
            return

        # Prepare metadata
        metadata = dict(product.product_metadata) if product.product_metadata else {}
        
        # 1. Flash Sale
        metadata["is_flash_sale"] = True
        # Set to end in 7 days
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        metadata["flash_sale_end"] = future_date.isoformat()
        
        # 2. Social Proof
        metadata["likes"] = 4820
        metadata["offer_sales_label"] = "ĐÃ BÁN"
        metadata["offer_rating_label"] = "4.9/5 RATING"
        
        # 3. Gamification
        metadata["share_count"] = 842
        metadata["share_target"] = 1000
        metadata["share_reward_label"] = "Đạt 1k share mở khóa đại tiệc quà tặng!"
        
        # 4. Share-to-Unlock Campaign (Elite Security)
        metadata["share_promotion"] = {
            "enabled": True,
            "voucher_id": "VIRAL50K",
            "voucher_label": "Giảm 50.000₫",
            "voucher_condition": "Áp dụng cho đơn mua qua link chia sẻ",
            "cta_text": "Chia sẻ để nhận mã",
            "share_text": "Bí quyết trắng hồng từ Nhật Bản! Cùng chia sẻ để nhận ưu đãi 50K nhé! 🌸"
        }
        
        product.product_metadata = metadata
        await session.commit()
        print(f"✨ Successfully updated {target_slug} with FULL Viral 2026 suite.")

if __name__ == "__main__":
    asyncio.run(update_features())
