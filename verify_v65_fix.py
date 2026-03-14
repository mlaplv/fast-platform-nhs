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
logger = logging.getLogger("xohi-verify")

async def verify_v65_fix():
    print("🚀 [KIỂM CHỨNG V65] Khởi động hệ thống với kho ảnh mới...")
    await trinity_bridge.initialize()
    await key_rotator.load_keys()
    await key_rotator.reset_health()

    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)

        ts = int(time.time())
        transcript = f"Đồng hồ xa xỉ nam {ts}: Thước đo bản lĩnh thượng lưu"

        print(f"\n--- [BƯỚC 1: SEO ANALYSIS] ---")
        response = await content_factory.handle_voice_request(transcript, repo)
        campaign_id = response.data.get("campaign_id")

        if not campaign_id:
            print(f"❌ ERROR: No campaign_id. {response}")
            return

        campaign = await repo.get(campaign_id)

        async def run_step(step_num, message):
            print(f"\n--- [BƯỚC {step_num}: {message}] ---")
            # Auto-approve previous step to trigger current
            await content_factory.approve_step(campaign_id, {"approved": True, "step": step_num - 1}, repo)

            # Polling
            for i in range(60):
                await session.refresh(campaign)
                if step_num == 6 and campaign.status == "COMPLETED":
                    print(f"✅ BƯỚC 6 HOÀN TẤT: XUẤT BẢN THÀNH CÔNG.")
                    return
                if campaign.status == "WAITING_FOR_REVIEW":
                    print(f"✅ AI xong Bước {step_num}.")
                    return
                if campaign.status == "ERROR":
                    print(f"❌ Lỗi tại bước {step_num}.")
                    return
                await asyncio.sleep(1)

        try:
            await run_step(2, "TRUY QUÉT HÌNH ẢNH")
            await run_step(3, "DÀN Ý")
            await run_step(4, "VIẾT BÀI")
            await run_step(5, "KIỂM TRA")
            await run_step(6, "LOCALIZE & PUBLISH")

            print(f"\n--- [KIỂM TRA KẾT QUẢ CUỐI CÙNG] ---")
            from backend.database.models import Article
            from sqlalchemy import select

            stmt = select(Article).where(Article.title.contains("Đồng hồ xa xỉ")).order_by(Article.created_at.desc())
            res = await session.execute(stmt)
            article = res.scalar_one_or_none()

            if article:
                print(f"✅ Bài viết: {article.title}")
                has_local = "/v65_assets/" in article.content
                print(f"🖼️ Trạng thái ảnh: {'✅ ĐÃ LOCALIZED' if has_local else '❌ VẪN LÀ REMOTE URL'}")

                # Check filesystem
                files = os.listdir("frontend/static/v65_assets")
                print(f"📂 Số lượng ảnh trong v65_assets: {len(files)}")
                for f in files[:3]: print(f"  - {f}")
            else:
                print("❌ Không tìm thấy bài viết sau khi chạy.")

        except Exception as e:
            print(f"❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_v65_fix())
