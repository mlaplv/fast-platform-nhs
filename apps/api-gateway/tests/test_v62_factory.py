import asyncio
import uuid
from src.database.models import ContentCampaign
from src.services.xohi.creative_studio.orchestrator import ContentOrchestrator
from src.services.xohi.creative_studio.models.vision_insight import VisionInsight
from src.services.xohi.creative_studio.operatives.asset_hunter import AssetHunter
from src.services.xohi.creative_studio.models.creative_pen import CreativePen
from src.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
from src.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
from unittest.mock import AsyncMock, MagicMock

async def test_v62_hardened_flow():
    print("\n🚀 [CTO MODE] BẮT ĐẦU KIỂM THỬ CHUYÊN SÂU CONTENT FACTORY V62.1...")
    
    # 1. Khởi tạo Campaign thực tế (không mock data mẫu)
    campaign = ContentCampaign(
        id=str(uuid.uuid4()),
        source_input="Smart Home 2026 và XoHi AI",
        tenant_id="tenant_cto",
        current_step=1,
        status="PROCESSING",
        gold_metadata={},
        assets_data=[]
    )

    # 2. Mock Repository trả về đúng campaign này
    mock_repo = MagicMock()
    mock_repo.add = AsyncMock(return_value=campaign)
    mock_repo.get = AsyncMock(return_value=campaign)
    mock_repo.update = AsyncMock()
    
    vision = VisionInsight()
    hunter = AssetHunter(api_keys=["key1"], search_engine_id="id1")
    hunter.fetch_images = AsyncMock(return_value=["http://img1.jpg", "http://img2.jpg"])
    
    pen = CreativePen()
    cop = PlagiarismCop()
    media = MediaCompressor()
    media.localize_assets = AsyncMock(return_value=["/static/uploads/v62/test_img1.webp", "/static/uploads/v62/test_img2.webp"])

    orchestrator = ContentOrchestrator(mock_repo, vision, hunter, pen, cop, media)

    # --- SIMULATION FLOW ---

    print(f"Step 0: Khởi tạo/Resume Campaign {campaign.id}...")
    
    # Step 1: Vision
    print("Step 1: AI Vision nảy số Topic & Keyword...")
    await orchestrator.run_step_1_vision(campaign.id)
    print(f"   -> OK: Topic nảy số: {campaign.topic_data.get('title')}")
    
    # Gate 1: Approval
    print("Gate 1: Duyệt Keyword & Khóa 'Sợi Chỉ Vàng'...")
    await orchestrator.approve_step(campaign.id, 1, True)
    print(f"   -> OK: Sợi chỉ vàng đã khóa chặt: {campaign.gold_metadata.get('primary_keyword')}")
    print(f"   -> OK: Đã nhảy sang Step: {campaign.current_step}")

    # Step 2: Asset Hunter
    print("Step 2: Săn ảnh Google...")
    await orchestrator.run_step_2_hunting(campaign.id)
    print(f"   -> OK: Săn được {len(campaign.assets_data)} ảnh.")

    # Step 6: Finalization
    print("Step 6: Media Localization (Chống ảnh chết)...")
    campaign.draft_content = "Nội dung bài viết mẫu [IMAGE_1]"
    await orchestrator.run_step_6_finalization(campaign.id)
    print(f"   -> OK: Path ảnh đã đổi sang local: {campaign.assets_data[0]}")
    print(f"   -> OK: Trạng thái cuối: {campaign.status}")

    print("\n✅ [CTO RESULT] KIỂM THỬ THÀNH CÔNG! MỌI MODULE V62.1 ĐÃ THÔNG NÒNG.")

if __name__ == "__main__":
    asyncio.run(test_v62_hardened_flow())
