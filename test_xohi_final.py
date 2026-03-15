import asyncio
import os
import json
import logging
import time
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.database.repositories import ContentCampaignRepository, ArticleRepository
from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.key_rotator import key_rotator
from sqlalchemy import select
from backend.database.models import ContentCampaign, Article

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xohi-final")

async def run_xohi_mission():
    print("🚀 [XOHI MISSION] Bắt đầu chu trình nội dung thế hệ mới...")

    # 1. Khởi tạo AI & Clear Health
    await trinity_bridge.initialize()
    await key_rotator.load_keys()
    await key_rotator.reset_health()

    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)

        # Chủ đề: Quiet Luxury
        transcript = f"Phong cách Quiet Luxury 2026 {int(time.time())}"

        print(f"\n--- [BƯỚC 1: PHÂN TÍCH CHIẾN LƯỢC] ---")
        response = await content_factory.handle_voice_request(transcript, repo)
        campaign_id = response.data.get("campaign_id")
        if not campaign_id:
            print("❌ Lỗi khởi tạo Campaign.")
            return

        campaign = await repo.get(campaign_id)

        async def execute_and_wait(step_num, message):
            print(f"\n--- [BƯỚC {step_num}: {message}] ---")
            # Kích hoạt bước tiếp theo (Approve bước trước đó)
            # Lưu ý: approve_step của XoHi trigger bước kế tiếp trong background task
            await content_factory.approve_step(campaign_id, {"approved": True, "step": step_num - 1}, repo)

            # Polling chờ AI hoàn tất
            for i in range(120): # Tăng timeout cho các bước AI nặng
                await session.refresh(campaign)
                if step_num == 6 and campaign.status == "COMPLETED":
                    print(f"✅ HỆ THỐNG ĐÃ XUẤT BẢN THÀNH CÔNG.")
                    return True
                if campaign.status == "WAITING_FOR_REVIEW":
                    print(f"✅ AI đã xong Bước {step_num}. Đang chuyển tiếp...")
                    return True
                if campaign.status == "ERROR":
                    print(f"❌ AI gặp lỗi ở Bước {step_num}.")
                    return False
                if i % 10 == 0 and i > 0:
                    print(f"⏳ Đang xử lý... ({i}s)")
                await asyncio.sleep(1)
            return False

        # Chạy chuỗi logic (Từ bước 2 đến bước 6)
        steps = [
            (2, "SĂN TÌM TÀI NGUYÊN HÌNH ẢNH"),
            (3, "PHÁC THẢO DÀN Ý VIRAL"),
            (4, "VIẾT BÀI CHI TIẾT (CREATIVE PEN)"),
            (5, "KIỂM ĐỊNH & CHỨNG NHẬN"),
            (6, "LOCALIZE MEDIA & XUẤT BẢN")
        ]

        # Lưu lại title mục tiêu từ Campaign trước khi bị cleanup ở Step 6
        target_title = None

        for num, msg in steps:
            success = await execute_and_wait(num, msg)
            if not success: break

            # Sau bước 1 hoặc bất kỳ bước nào có topic_data, lấy title để verify sau này
            if not target_title and campaign.topic_data:
                target_title = campaign.topic_data.get("title")

        # --- BƯỚC CHỐT: DUYỆT BƯỚC 6 ĐỂ XUẤT BẢN ---
        if success:
            print(f"\n--- [BƯỚC 7: DUYỆT XUẤT BẢN CUỐI CÙNG] ---")
            await content_factory.approve_step(campaign_id, {"approved": True, "step": 6}, repo)

            # Chờ một chút để hệ thống thực hiện publish & cleanup
            for i in range(10):
                await session.refresh(campaign)
                if campaign.status == "COMPLETED":
                    print("✅ CHIẾN DỊCH ĐÃ HOÀN TẤT VÀ XUẤT BẢN.")
                    break
                await asyncio.sleep(1)

        print(f"\n--- [KIỂM TRA THÀNH PHẨM] ---")
        # Truy vấn bài viết vừa tạo dựa trên title và user_id (để tránh lấy nhầm bài cũ)
        if target_title:
            print(f"🔍 Đang tìm bài viết có tiêu đề: {target_title}")
            stmt = select(Article).where(Article.title == target_title).order_by(Article.created_at.desc())
        else:
            print("⚠️ Không xác định được title, fallback lấy bài mới nhất...")
            stmt = select(Article).order_by(Article.created_at.desc())

        res = await session.execute(stmt)
        article = res.scalars().first()

        if article:
            print(f"✅ TIÊU ĐỀ: {article.title}")
            print(f"🔗 SLUG: {article.slug}")

            # Kiểm tra Media Localization kỹ hơn
            import re
            img_urls = re.findall(r'src=["\'](.*?)["\']', article.content)
            external_imgs = [url for url in img_urls if url.startswith("http")]
            local_imgs = [url for url in img_urls if "/v65_assets/" in url]

            print(f"🖼️ MEDIA REPORT:")
            print(f"   - Tổng số ảnh: {len(img_urls)}")
            print(f"   - Đã nội địa hóa: {len(local_imgs)}")
            if external_imgs:
                print(f"   - ⚠️ CÒN LINK NGOÀI ({len(external_imgs)}):")
                for url in external_imgs[:3]: print(f"     -> {url}")
            else:
                print(f"   - ✅ 100% Localized (Chuẩn R115)")

            print(f"📊 NỘI DUNG: {len(article.content)} ký tự.")
            if len(article.content) < 500:
                print(f"⚠️ CẢNH BÁO: Nội dung quá ngắn ({len(article.content)} ký tự).")
        else:
            print("❌ Không tìm thấy bài viết trong Database.")

if __name__ == "__main__":
    asyncio.run(run_xohi_mission())
