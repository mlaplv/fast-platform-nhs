import asyncio
import os
import sys
import logging
from typing import cast
from pydantic import BaseModel, Field

# Thêm root vào path để import
sys.path.append(os.getcwd())

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.key_rotator import key_rotator
from pydantic_ai import Agent

# Setup logging tối giản để quan sát flow
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("test-ai")

class TestResponse(BaseModel):
    reply: str = Field(..., description="Phản hồi của AI")
    status: str = Field(..., description="Trạng thái hệ thống")

async def test_helen_connectivity():
    print("\n" + "="*60)
    print("🚀 HELEN TRINITY CONNECTIVITY TEST - ELITE V2.2")
    print("="*60 + "\n")
    
    # 1. Khởi tạo Bridge
    await trinity_bridge.initialize()
    primary = trinity_bridge.default_model_name
    key_count = key_rotator.get_count()
    
    print(f"🔹 Model mặc định (Primary): {primary}")
    print(f"🔹 Số lượng key trong Rotator: {key_count}")
    print(f"🔹 Danh sách model khám phá được: {len(trinity_bridge.discovered)}")
    
    # 2. Xây dựng Agent test
    test_agent = Agent(
        output_type=TestResponse,
        system_prompt=(
            "Bạn là Helen Support Agent. Hãy trả lời câu hỏi của khách một cách tự nhiên. "
            "Nếu bạn nhận được thông tin địa chỉ từ context, hãy cung cấp nó. "
            "Cấu trúc trả về phải là 'reply' và 'status'."
        )
    )
    
    prompt = "Địa chỉ nhà thuốc của mình ở đâu vậy Helen?"
    context = "[CONTEXT KNOWLEDGE] Địa chỉ nhà thuốc Hồng Sơn: 33 Ngô Thị Nhậm, Trung Sơn, Tam Điệp, Ninh Bình."
    
    print(f"\n💬 Question: {prompt}")
    print(f"📦 Context injected: True")
    
    try:
        # 3. Chạy qua Trinity Bridge
        print("\n⏳ Đang gọi Trinity Bridge (Rotating Key and Dynamic Chain)...")
        
        # Test direct mode to bypass semantic cache for this test
        res = await trinity_bridge.run(
            test_agent,
            f"{context}\nUser: {prompt}",
            role=trinity_bridge.ROLE_BRAIN,
            # Force model to ensure we test exactly what Sếp specified
            model=primary 
        )
        
        # Elite V2.2: Universal Data Extraction (Direct Access)
        # res is now the TestResponse object directly (thanks to TrinityBridge middleware)
        data = cast(TestResponse, res)
        
        print("\n✅ KẾT QUẢ PHẢN HỒI:")
        print("-" * 30)
        print(f"Helen says: {data.reply}")
        print(f"Status: {data.status}")
        print("-" * 30)
        
        # In logic verify: Nếu response về cực nhanh (vài ms) và nội dung đúng 
        # thì chứng tỏ đã trúng L0 Fast-Path.
        
        # Kiểm tra usage
        if hasattr(res, 'usage'):
            print(f"📊 Tokens used: {res.usage.total_tokens}")
            
    except Exception as e:
        print(f"\n❌ LỖI KẾT NỐI: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_helen_connectivity())
