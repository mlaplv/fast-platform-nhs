import asyncio
import uuid
from sqlalchemy import delete
from backend.database import async_session_maker
from backend.database.models import Banner, ProductBase

async def seed_banners():
    print("🚀 [SEED] Starting Banner Seeding (Elite V2.2)...")
    async with async_session_maker() as session:
        # 1. Clean old banners
        await session.execute(delete(Banner))
        
        # 2. Get some real product slugs to link
        # Sếp muốn liên kết 99%, nên ta lấy các slug thực tế từ DB
        banners_data = [
            {
                "id": "m1",
                "title": "Bạn mới tặng 80k",
                "image_url": "/uploads/2026/04/713b7e0d-a566-48b0-8271-a5959b452090.webp",
                "link_url": "miccosmo-white-label-platinum-placenta-whitening-cream-20g-kem-duong-da-nam",
                "position": "home_main",
                "order_index": 1
            },
            {
                "id": "m2",
                "title": "osmo Live",
                "image_url": "/uploads/2026/04/0a761945-d9ca-4cf1-8cc5-c57bfa9727db.webp",
                "link_url": "miccosmo-white-label-premium-placenta-pack-130g-mat-na-rua-troi-ho-tro-duong-sang",
                "position": "home_main",
                "order_index": 2
            },
            {
                "id": "m3",
                "title": "Dyson Slide",
                "image_url": "/uploads/2026/04/713b7e0d-a566-48b0-8271-a5959b452090.webp",
                "link_url": "miccosmo-white-label-premium-placenta-rich-gold-eye-cream-25g-kem-mat-ho-tro-mo-tham-duong-sang",
                "position": "home_main",
                "order_index": 3
            },
            {
                "id": "s1",
                "title": "osmo Xử Lý",
                "image_url": "/uploads/2026/04/c6ba1a76-527b-4f06-9f16-a2883d526131.webp",
                "link_url": "miccosmo-white-label-premium-placenta-essence-180ml-tinh-chat-cap-am-lam-diu-da",
                "position": "home_side",
                "order_index": 4
            },
            {
                "id": "s2",
                "title": "Voucher 50%",
                "image_url": "/uploads/2026/04/bee054dc-7531-40cd-a56c-51e0f732cd4f.webp",
                "link_url": "miccosmo-white-label-placenta-rich-gold-cream-60g-kem-ho-tro-duong-sang-ngua-lao-hoa",
                "position": "home_side",
                "order_index": 5
            }
        ]

        for data in banners_data:
            banner = Banner(
                id=data["id"],
                title=data["title"],
                image_url=data["image_url"],
                link_url=data["link_url"],
                position=data["position"],
                order_index=data["order_index"],
                is_active=True,
                device_type="all"
            )
            session.add(banner)
        
        await session.commit()
        print("✅ [SEED] 5 Banners created successfully with Neural Links!")

if __name__ == "__main__":
    asyncio.run(seed_banners())
