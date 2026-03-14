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

        for num, msg in steps:
            success = await execute_and_wait(num, msg)
            if not success: break

        print(f"\n--- [KIỂM TRA THÀNH PHẨM] ---")
        # Truy vấn bài viết vừa tạo
        stmt = select(Article).where(Article.campaign_id == campaign_id) if hasattr(Article, 'campaign_id') else select(Article).order_by(Article.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        article = res.scalar_one_or_none()

        if article:
            print(f"✅ TIÊU ĐỀ: {article.title}")
            print(f"🔗 SLUG: {article.slug}")
            has_local = "/v65_assets/" in article.content
            print(f"🖼️ MEDIA: {'✅ ĐÃ LOCALIZED (v65_assets)' if has_local else '⚠️ VẪN DÙNG LINK NGOÀI'}")
            print(f"📊 NỘI DUNG: {len(article.content)} ký tự.")
        else:
            print("❌ Không tìm thấy bài viết trong Database.")

if __name__ == "__main__":
    asyncio.run(run_xohi_mission())
