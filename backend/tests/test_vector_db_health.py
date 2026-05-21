import asyncio
import os
import sys
from sqlalchemy import text

# Thêm root vào path để import
sys.path.append(os.getcwd())

from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.encoder_singleton import warmup_encoder, get_shared_encoder

async def test_vector_db():
    print("=" * 60)
    print("🚀 POSTGRESQL PGVECTOR DATABASE HEALTH CHECK")
    print("=" * 60)
    
    # 1. Warmup encoder
    await warmup_encoder()
    encoder = get_shared_encoder()
    if not encoder:
        print("❌ LỖI: Encoder chưa sẵn sàng!")
        return
        
    # Tạo vector
    vecs = list(encoder.embed(["tư vấn sản phẩm"]))
    vec_str = f"[{','.join(map(str, vecs[0]))}]"
    
    # 2. Kết nối Database và chạy truy vấn vector
    print("\n⏳ Đang kết nối Database và chạy truy vấn pgvector...")
    t0 = asyncio.get_event_loop().time()
    try:
        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as db:
            sql = text("""
                SELECT p.id, p.name, p.price, p.slug,
                       pe.embedding <=> CAST(:v AS vector) AS dist
                FROM product_bases p
                JOIN product_embeddings pe ON p.id = pe.product_base_id
                WHERE p.deleted_at IS NULL
                  AND p.status = 'ACTIVE'
                  AND p.tenant_id = :tid
                ORDER BY dist ASC
                LIMIT 5
            """)
            res = await db.execute(sql, {"v": vec_str, "tid": "default"})
            rows = res.fetchall()
            t1 = asyncio.get_event_loop().time()
            
            print(f"✅ Truy vấn DB hoàn thành xuất sắc trong {t1 - t0:.3f}s!")
            print(f"📊 Tìm thấy {len(rows)} sản phẩm tương đồng:")
            for idx, r in enumerate(rows):
                print(f"  {idx+1}. ID: {r.id} | Name: {r.name} | Price: {r.price} | Slug: {r.slug} | Distance: {r.dist:.4f}")
                
    except Exception as e:
        print(f"❌ LỖI TRUY VẤN VECTOR DATABASE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vector_db())
