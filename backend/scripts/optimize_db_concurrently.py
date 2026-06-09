import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text

# Add project root to python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import engine

async def optimize_db_concurrently():
    print("🚀 [CONCURRENT OPTIMIZE] Bắt đầu tối ưu hóa cơ sở dữ liệu không gây khóa (Zero-Locking)...")
    
    # Thiết lập AUTOCOMMIT từ Engine level để tương thích tốt nhất với mọi phiên bản SQLAlchemy
    autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")
    
    async with autocommit_engine.connect() as conn:
        # 1. Chạy VACUUM ANALYZE (Không khóa bảng)
        print("⏳ 1. Đang chạy VACUUM ANALYZE để dọn dẹp hàng thừa và cập nhật thống kê...")
        try:
            await conn.execute(text("VACUUM VERBOSE ANALYZE;"))
            print("   ✅ Hoàn tất VACUUM ANALYZE.")
        except Exception as e:
            print(f"   ❌ Lỗi khi chạy VACUUM: {e}")

        # 2. Lấy danh sách tất cả các bảng trong schema public
        print("⏳ 2. Đang truy vấn danh sách bảng...")
        try:
            tables_res = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
            ))
            tables = [row[0] for row in tables_res.fetchall()]
            print(f"   Found {len(tables)} tables to reindex concurrently.")
        except Exception as e:
            print(f"   ❌ Lỗi khi truy vấn danh sách bảng: {e}")
            return

        # 3. Chạy REINDEX TABLE CONCURRENTLY cho từng bảng
        # REINDEX CONCURRENTLY chỉ dùng khóa SHARE UPDATE EXCLUSIVE, cho phép các tiến trình đọc/ghi khác chạy bình thường
        print("⏳ 3. Đang xây dựng lại chỉ mục không gây khóa (REINDEX CONCURRENTLY)...")
        for table in tables:
            print(f"   [REINDEX] Tiến hành reindex table: {table}...")
            try:
                await conn.execute(text(f'REINDEX TABLE CONCURRENTLY "{table}";'))
                print(f"   ✅ Hoàn tất reindex table: {table}")
            except Exception as e:
                # PostgreSQL không hỗ trợ REINDEX CONCURRENTLY trên bảng tạm hoặc một số index hệ thống
                print(f"   ⚠️  Không thể reindex table {table}: {e}")

    print("🎉 [SUCCESS] Đã tối ưu hóa database hoàn tất với cơ chế Zero-Locking!")

if __name__ == "__main__":
    asyncio.run(optimize_db_concurrently())
