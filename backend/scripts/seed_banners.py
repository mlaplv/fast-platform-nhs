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
                "image_url": "/uploads/img/banner/vn-11134258-81ztc-mm7801vsbw94c6@resize_w797_nl.webp",
                "link_url": "miccosmo-white-label-platinum-placenta-whitening-cream-20g",
                "position": "home_main",
                "order_index": 1
            },
            {
                "id": "m2",
                "title": "Micsmo Live",
                "image_url": "/uploads/img/banner/vn-11134258-81ztc-mmiz6tc047peb7@resize_w797_nl.webp",
                "link_url": "miccosmo-white-label-premium-placenta-pack-130g",
                "position": "home_main",
                "order_index": 2
            },
            {
                "id": "m3",
                "title": "Dyson Slide",
                "image_url": "/uploads/img/banner/sg-11134258-81zu3-mmr6osj4nb41df@resize_w797_nl.webp",
                "link_url": "miccosmo-white-label-premium-placenta-rich-gold-eye-cream-25g",
                "position": "home_main",
                "order_index": 3
            },
            {
                "id": "s1",
                "title": "Micsmo Xử Lý",
                "image_url": "/uploads/img/banner/sg-11134258-81ztz-mmr7ei1zauiwc3@resize_w398_nl.webp",
                "link_url": "miccosmo-white-label-premium-placenta-essence-180ml",
                "position": "home_main",
                "order_index": 4
            },
            {
                "id": "s2",
                "title": "Voucher 50%",
                "image_url": "/uploads/img/banner/sg-11134258-81zw1-mmr7ejh867lucb@resize_w398_nl.webp",
                "link_url": "miccosmo-white-label-placenta-rich-gold-cream-60g",
                "position": "home_main",
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
