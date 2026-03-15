import asyncio
import json
import time
import logging
import httpx
import os
from dotenv import load_dotenv

# R00: PHẢI load env và set biến môi trường TRƯỚC khi import module backend
load_dotenv()
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.key_rotator import key_rotator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-stream")

# R00: Use official domain via Caddy (HTTPS)
BASE_URL = "https://api.smartshop.test/api/v1/content"

async def test_streaming_waterfall():
    print("🚀 [TEST STREAMING] Khởi chạy Neural Streaming Waterfall qua HTTP API...")

    # 1. Khởi tạo
    await trinity_bridge.initialize()
    await key_rotator.load_keys()

    # Tăng timeout lên 60s để AI kịp phản hồi các bước nặng
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        # 2. Tạo Campaign (Giả lập Bước 1 bằng cách gửi voice request qua handler hoặc ở đây ta dùng repo để tạo base)
        # Để đơn giản và nhanh, ta dùng chính logic cũ để tạo campaign trong DB
        from backend.database.alchemy_config import alchemy_config
        from backend.database.repositories import ContentCampaignRepository
        from backend.services.xohi.creative_studio.orchestrator import content_factory

        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            repo = ContentCampaignRepository(session=session)
            transcript = f"Quiet Luxury Interior 2026 {int(time.time())}"
            print(f"BƯỚC 1: Phân tích giọng nói...")
            resp = await content_factory.handle_voice_request(transcript, repo)
            campaign_id = resp.data.get("campaign_id")
            await session.commit()

        print(f"Campaign ID: {campaign_id}")

        # 3. Chạy qua Bước 2 và 3 qua HTTP API
        print(f"BƯỚC 2: Săn ảnh (gửi lệnh qua API)...")
        await client.post(f"{BASE_URL}/campaigns/{campaign_id}/approve", json={"approved": True, "step": 1})
        await asyncio.sleep(5) # Đợi AI săn ảnh xong

        print(f"BƯỚC 3: Lập dàn ý (gửi lệnh qua API)...")
        await client.post(f"{BASE_URL}/campaigns/{campaign_id}/approve", json={"approved": True, "step": 2})
        await asyncio.sleep(5) # Đợi AI lập dàn ý xong

        # 4. Kết nối SSE Stream
        print(f"\n🔗 Đang kết nối tới SSE Stream: {BASE_URL}/stream/{campaign_id}")

        async def listen_sse():
            print("👂 Đang lắng nghe Neural Chunks qua HTTP SSE...")
            chunks_received = 0
            start_stream = time.time()

            try:
                async with httpx.AsyncClient(timeout=None) as stream_client:
                    async with stream_client.stream("GET", f"{BASE_URL}/stream/{campaign_id}") as response:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                payload = json.loads(line[6:])

                                if "text" in payload:
                                    chunks_received += 1
                                    if chunks_received == 1:
                                        print(f"\n⚡ [FIRST CHUNK] Nhận được chunk đầu tiên sau {time.time() - start_stream:.2f}s!")

                                    # In ra chunk để verify
                                    print(payload["text"], end="", flush=True)

                                if payload.get("step") == 4 and payload.get("status") == "WAITING_FOR_REVIEW":
                                    print(f"\n\n✅ AI đã viết xong bài. Tổng cộng {chunks_received} chunks.")
                                    return
            except Exception as e:
                print(f"\n❌ Lỗi Stream: {e}")

        # 5. Kích hoạt Bước 4 qua HTTP API
        print(f"BƯỚC 4: Duyệt dàn ý -> Kích hoạt Neural Writing (gửi lệnh qua API)...")

        # Chạy đồng thời lắng nghe và kích hoạt
        listener = asyncio.create_task(listen_sse())
        await asyncio.sleep(2) # Đợi client kết nối SSE ổn định

        # Trigger Bước 4 qua API
        await client.post(f"{BASE_URL}/campaigns/{campaign_id}/approve", json={"approved": True, "step": 3})

        await listener
        print("\n🎉 TEST HOÀN TẤT THÀNH CÔNG.")

if __name__ == "__main__":
    asyncio.run(test_streaming_waterfall())
