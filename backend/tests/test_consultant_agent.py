import asyncio
import os
import sys
import logging
from typing import cast

# Thêm root vào path để import
sys.path.append(os.getcwd())

from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.commerce.operatives.handlers.consultant import _consultant_no_tool_agent, ConsultantDeps, ConsultantResponse

# Setup logging chi tiết để nhìn thấy từng cuộc gọi của Pydantic AI bao gồm cả tool calls
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test-consultant")

async def test_consultant():
    print("=" * 60)
    print("🚀 HELEN CONSULTANT AGENT DETAILED DIAGNOSTICS")
    print("=" * 60)
    
    # 1. Khởi tạo Bridge
    await trinity_bridge.initialize()
    
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # Giả lập dynamic prompt
        dynamic_prompt = (
            "You are Helen - Senior Beauty Architect tại osmo.\n"
            "Hãy trả lời câu hỏi của khách hàng một cách tự nhiên, trang nhã.\n"
            "Sử dụng định dạng ConsultantResponse (reply, intent, ui_component)."
        )
        deps = ConsultantDeps(db=db, dynamic_prompt=dynamic_prompt)
        
        prompt = "Shop có bán nước hoa vùng kín Beppin Bodhi không?"
        print(f"\n💬 Prompt: {prompt}")
        print("⏳ Đang chạy Consultant Agent qua Trinity Bridge...")
        
        t0 = asyncio.get_event_loop().time()
        try:
            res = await trinity_bridge.run(
                _consultant_no_tool_agent,
                prompt,
                deps=deps,
                role=trinity_bridge.ROLE_BRAIN,
                model="gemini-3.5-flash",
                timeout=15.0
            )
            t1 = asyncio.get_event_loop().time()
            print(f"\n✅ THÀNH CÔNG trong {t1 - t0:.2f} giây!")
            print("-" * 30)
            if res:
                data = cast(ConsultantResponse, res)
                print(f"Reply: {data.reply}")
                print(f"Intent: {data.intent}")
                print(f"UI Component: {data.ui_component}")
            else:
                print("Response is None!")
            print("-" * 30)
        except Exception as e:
            t1 = asyncio.get_event_loop().time()
            print(f"\n❌ THẤT BẠI sau {t1 - t0:.2f} giây!")
            print(f"Lỗi: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_consultant())
