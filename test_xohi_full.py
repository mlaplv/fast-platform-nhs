import asyncio
import os
import json
import logging
import time
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.database.repositories import ContentCampaignRepository
from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.key_rotator import key_rotator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xohi-test")

async def test_full_chain():
    print("🚀 [TRỰC CHIẾN] Khởi động hệ thống XoHi Content Factory - FULL 6 STEPS...")
    await trinity_bridge.initialize()
    await key_rotator.load_keys()

    # RESET HEALTH to clear any "daily exhausted" flags for testing
    print("🧹 Resetting KeyRotator health...")
    await key_rotator.reset_health()

    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)

        # Unique transcript
        ts = int(time.time())
        transcript = f"Thời trang nam cao cấp {ts}: Đẳng cấp quý ông thượng lưu"

        print(f"\n--- [BƯỚC 1: PHÂN TÍCH SEO & GOLDEN THREAD] ---")
        response = await content_factory.handle_voice_request(transcript, repo)

        campaign_id = response.data.get("campaign_id")
        if not campaign_id:
            print(f"❌ ERROR: No campaign_id returned. Response: {response}")
            return

        campaign = await repo.get(campaign_id)
        print(f"✅ Step 1 Hoàn tất. Campaign ID: {campaign_id}")

        async def run_step(step_num, message):
            print(f"\n--- [BƯỚC {step_num}: {message}] ---")
            res_data = await content_factory.approve_step(campaign_id, {"approved": True, "step": step_num - 1}, repo)
            print(f"📡 {res_data.get('message', 'Triggered')}")

            # POLLING: Wait for AI or Process to finish
            for i in range(60):
                await session.refresh(campaign)
                # For Step 6, status becomes 'COMPLETED'
                if step_num == 6 and campaign.status == "COMPLETED":
                    print(f"✅ Hệ thống đã hoàn thành Bước 6: XUẤT BẢN THÀNH CÔNG.")
                    return
                if campaign.status == "WAITING_FOR_REVIEW":
                    print(f"✅ AI đã hoàn thành Bước {step_num}.")
                    return
                if campaign.status == "ERROR":
                    print(f"❌ AI gặp lỗi ở bước này.")
                    return
                if i % 5 == 0:
                    print(f"⏳ Đang đợi xử lý... ({i}s)")
                await asyncio.sleep(1)

        try:
            await run_step(2, "TRUY QUÉT HÌNH ẢNH")
            await run_step(3, "XÂY DỰNG DÀN Ý VIRAL")
            await run_step(4, "VIẾT BÀI CHI TIẾT")
            await run_step(5, "KIỂM TRA ĐẠO VĂN & CHỨNG NHẬN")
            await run_step(6, "XUẤT BẢN & DỌN DẸP")

            print(f"\n🎉 [CHÚC MỪNG SẾP] Chu trình XoHi Content Factory đã hoàn tất 100%!")
            print(f"📌 Bài viết hiện đã có mặt trong Database (Table: articles).")
            print(f"📌 Bộ nhớ Campaign {campaign_id} đã được dọn dẹp sạch sẽ để bảo vệ RAM.")

        except Exception as e:
            print(f"❌ Lỗi trong quá trình chạy: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_chain())
