import asyncio
import os
import sys

# Thêm root vào path để import
sys.path.append(os.getcwd())

from backend.services.ai_engine.core.encoder_singleton import warmup_encoder, get_shared_encoder

async def test_encoder():
    print("=" * 60)
    print("🚀 FASTEMBED VECTOR ENCODER HEALTH CHECK")
    print("=" * 60)
    
    # In thông tin cache dir
    from backend.services.ai_engine.core.encoder_singleton import CACHE_DIR
    print(f"🔹 Cache Directory: {CACHE_DIR}")
    print(f"🔹 Writable: {os.access(CACHE_DIR, os.W_OK) if os.path.exists(CACHE_DIR) else 'Dir not exists yet'}")
    
    # 1. Khởi động / Warm up encoder
    print("\n⏳ Đang khởi tạo/warmup encoder (Tải model từ cache hoặc HuggingFace)...")
    t0 = asyncio.get_event_loop().time()
    await warmup_encoder()
    t1 = asyncio.get_event_loop().time()
    print(f"✅ Warmup hoàn thành sau {t1 - t0:.2f}s!")
    
    # 2. Lấy encoder
    encoder = get_shared_encoder()
    print(f"🔹 Shared encoder: {encoder}")
    
    if encoder:
        # 3. Chạy thử embedding câu truy vấn thực tế
        print("\n⏳ Đang thử nghiệm tạo Vector Embedding cho câu: 'tư vấn sản phẩm'...")
        t_embed_0 = asyncio.get_event_loop().time()
        try:
            loop = asyncio.get_running_loop()
            vecs = await loop.run_in_executor(None, lambda: list(encoder.embed(["tư vấn sản phẩm"])))
            t_embed_1 = asyncio.get_event_loop().time()
            print(f"✅ Tạo Embedding thành công sau {t_embed_1 - t_embed_0:.2f}s!")
            print(f"📊 Độ dài Vector: {len(vecs[0]) if vecs else 0}")
            print(f"📍 Mẫu vector (5 chiều đầu): {vecs[0][:5] if vecs else []}")
        except Exception as e:
            print(f"❌ LỖI KHI TẠO VECTOR EMBEDDING: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ LỖI: Encoder bị trả về None sau khi warmup!")

if __name__ == "__main__":
    asyncio.run(test_encoder())
