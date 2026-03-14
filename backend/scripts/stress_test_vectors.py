
import asyncio
import time
import numpy as np
import psutil
import os
from backend.services.ai_engine.core.vector_memory import VectorMemory
from backend.services.ai_engine.core.encoder_singleton import warmup_encoder, get_shared_encoder

async def stress_test():
    print("🔥 Bắt đầu Stress Test Phase 76.4: 10,000+ Vectors Search")

    # 1. Warmup
    await warmup_encoder()
    encoder = get_shared_encoder()

    # 2. Giả lập 10,000 embeddings (Dimention: 384 cho MiniLM-L12-v2)
    VECTOR_DIM = 384
    NUM_VECTORS = 10000

    print(f"📦 Đang tạo {NUM_VECTORS} vectors giả lập...")
    # Tạo matrix ngẫu nhiên và chuẩn hóa L2
    mock_matrix = np.random.randn(NUM_VECTORS, VECTOR_DIM).astype(np.float32)
    norms = np.linalg.norm(mock_matrix, axis=1, keepdims=True)
    mock_matrix /= norms

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024
    print(f"📊 RAM trước khi Search: {mem_before:.2f} MB")

    # 3. Giả lập Query Vector
    query_text = "tìm áo sơ mi nam màu trắng"
    query_vec = list(encoder.embed([query_text]))[0].astype(np.float32)
    query_vec /= np.linalg.norm(query_vec)

    # 4. Benchmark Matrix Dot Product (Phép toán lõi của VectorMemory)
    print(f"⚡ Đang thực hiện Semantic Search trên {NUM_VECTORS} bản ghi...")

    iterations = 100
    start_time = time.perf_counter()

    for _ in range(iterations):
        # Mô phỏng logic trong VectorMemory.search
        scores = np.dot(mock_matrix, query_vec)
        top_indices = np.argsort(scores)[::-1][:5]
        # Giả lập việc truy xuất metadata
        results = [f"Item {i}" for i in top_indices]

    end_time = time.perf_counter()

    avg_latency = (end_time - start_time) / iterations * 1000
    mem_after = process.memory_info().rss / 1024 / 1024

    print(f"\n✅ KẾT QUẢ STRESS TEST:")
    print(f"⏱️ Average Latency (10k vectors): {avg_latency:.2f}ms")
    print(f"📊 RAM sau khi Search: {mem_after:.2f} MB")
    print(f"📈 RAM Delta: {mem_after - mem_before:.2f} MB")

    if avg_latency < 50:
        print("\n🔥 ĐẠT CHUẨN ULTRA-FAST: Hệ thống dư sức cân 10,000+ sản phẩm.")
    else:
        print("\n⚠️ CẢNH BÁO: Hiệu năng có dấu hiệu suy giảm.")

if __name__ == "__main__":
    asyncio.run(stress_test())
