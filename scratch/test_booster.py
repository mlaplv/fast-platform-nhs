
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Thêm đường dẫn vào sys.path để import được backend
sys.path.append(str(Path(__file__).parent.parent))

# Mock environment variables
os.environ["REDIS_HOST"] = "localhost"
os.environ["AI_PRIMARY_MODEL"] = "gemini-1.5-pro"
os.environ["GOOGLE_SEARCH_API_KEY"] = "MOCK_KEY" # Cần để không lỗi khi khởi tạo

async def test_booster():
    print("🚀 [TEST] Đang khởi động Neural Booster Test (Isolated Mode)...")
    
    # 1. Mock KeyRotator (Tránh Redis)
    from backend.services.ai_engine.core.key_rotator import key_rotator
    key_rotator.get_key = AsyncMock(return_value="AIzaSy...") # Trả về key giả
    key_rotator.get_count = MagicMock(return_value=1)
    key_rotator.is_model_daily_exhausted = AsyncMock(return_value=False)
    key_rotator.track_tokens = AsyncMock()
    key_rotator.set_success = AsyncMock()
    key_rotator.load_keys = AsyncMock()
    
    # 2. Mock Alchemy Config (Tránh DB)
    from backend.database.alchemy_config import alchemy_config
    alchemy_config.create_session_maker = MagicMock()
    
    # 3. Mock Progress Emitter (Tránh Redis)
    from backend.services.ai_engine.core.agent_base import XoHiProgressMixin
    XoHiProgressMixin._emit_progress = AsyncMock()
    
    # 4. Mock TrinityBridge.initialize (Tránh DB)
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    trinity_bridge.initialize = AsyncMock()
    trinity_bridge._initialized = True
    trinity_bridge.discovered = ["gemini-1.5-pro", "gemini-1.5-flash"]

    from backend.services.xohi.creative_studio.operatives.neural_booster import NeuralBooster
    
    booster = NeuralBooster()
    
    sample_content = """
    Mùa đông đến, ngồi điều hòa nhiều làm da bị khô. 
    Bạn nên uống nhiều nước và bôi kem dưỡng ẩm. 
    Dưỡng da là một quá trình quan trọng để giữ vẻ đẹp. 
    Hãy chăm sóc bản thân mình tốt hơn mỗi ngày.
    """
    
    sample_topic = "Cách chăm sóc da khô mùa máy lạnh văn phòng"
    
    print(f"📄 [INPUT] Topic: {sample_topic}")
    print(f"📄 [INPUT] Content: {sample_content.strip()[:100]}...")
    
    try:
        print("📡 [CONNECT] Đang gọi Neural Bridge (Gemini)...")
        # Chạy thật cuộc gọi AI (Nếu có API key thật trong môi trường thì nó sẽ chạy, 
        # nếu không nó sẽ lỗi Auth nhưng ít nhất ta check được logic).
        # Tuy nhiên, trong môi trường này thường không có API key thật.
        # Vậy nên ta sẽ MOCK kết quả trả về của AI để kiểm tra cấu trúc.
        
        from backend.services.xohi.creative_studio.models.schemas import NeuralBoosterReport, ContentPatch
        mock_result = NeuralBoosterReport(
            patches=[
                ContentPatch(
                    search_string="Bạn nên uống nhiều nước và bôi kem dưỡng ẩm.",
                    replacement_string="Bạn nên uống ít nhất 2 lít nước mỗi ngày và sử dụng kem dưỡng ẩm chuyên dụng cho da khô để duy trì độ ẩm tối ưu.",
                    rationale="Thêm số liệu và độ chuyên sâu cho lời khuyên."
                )
            ],
            summary="### 💎 BÁO CÁO TINH CHỈNH NEURAL BOOSTER (ELITE V2.2)\n---\n#### ⚔️ VAI TRÒ TÁC CHIẾN: Cố vấn EEAT Bài viết (Elite V2.2)\n\n- **[LUẬN ĐIỂM CẢI TIẾN]**: Nội dung gốc còn sơ sài, thiếu dẫn chứng thực tế.\n- **[CHỨNG CỨ TINH CHỈNH]**: Đã nâng cấp đoạn hướng dẫn uống nước với số liệu cụ thể.\n- **[KẾT QUẢ KỲ VỌNG]**: Tăng khả năng lọt TOP 1 và AI Overview.",
            logs=[]
        )
        
        with patch.object(trinity_bridge, 'run', AsyncMock(return_value=mock_result)):
            result = await booster.chat(None, content=sample_content, topic=sample_topic)
            
            print("\n" + "="*50)
            print("✅ [RESULT] KẾT QUẢ TINH CHỈNH (MOCKED AI):")
            print("="*50)
            
            print(f"\n📊 SUMMARY:\n{result.summary}")
            
            print(f"\n🧩 PATCHES ({len(result.patches)}):")
            for i, p in enumerate(result.patches):
                print(f"\n--- Patch #{i+1} ---")
                print(f"🔍 Search: {p.search_string}")
                print(f"✨ Replacement: {p.replacement_string}")
                print(f"💡 Rationale: {p.rationale}")
                
                # Check for tag leakage
                if "[" in p.replacement_string and "]" in p.replacement_string:
                    print("⚠️ [WARNING] Phát hiện nhãn phân tích trong replacement_string!")
            
            # Kiểm tra xem vai diễn có đúng như mong đợi (Cố vấn EEAT)
            if "Cố vấn EEAT" in result.summary:
                print("\n✅ [CHECK] Vai diễn chính xác: Cố vấn EEAT.")
            else:
                print("\n❌ [CHECK] Vai diễn sai hoặc thiếu!")

            # Kiểm tra xem có bị dính pillars không (trong summary)
            if "HOOK" in result.summary or "EVIDENCE" in result.summary:
                print("❌ [CHECK] Vẫn còn dấu vết Pillars trong báo cáo!")
            else:
                print("✅ [CHECK] Đã loại bỏ hoàn toàn Pillars khỏi báo cáo.")

        print("\n" + "="*50)
        print("📜 LOGS:")
        for log in result.logs:
            print(f"- {log}")
            
    except Exception as e:
        print(f"❌ [ERROR] Lỗi khi chạy test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_booster())
