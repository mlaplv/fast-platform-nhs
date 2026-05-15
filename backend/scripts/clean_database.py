import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text

# Fix python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker, engine
from backend.database.models import Base

async def clean_database(target_tables: list[str] = None):
    print("🧹 [CLEAN] Khởi động quy trình làm sạch Database (Elite V2.2)...")
    
    async with async_session_maker() as session:
        # [ELITE UPGRADE] Truy vấn trực tiếp từ DB để lấy toàn bộ bảng thực tế (không phụ thuộc Metadata)
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
              AND table_name != 'alembic_version'
            ORDER BY table_name;
        """)
        
        result = await session.execute(query)
        all_table_names = [row[0] for row in result.fetchall()]
        
        # Lấy thêm metadata để hỗ trợ sắp xếp theo phụ thuộc nếu cần
        tables_metadata = Base.metadata.sorted_tables
        metadata_names = {t.name for t in tables_metadata}
        
        if not all_table_names:
            print("⚠️ Không tìm thấy bảng nào trong Database.")
            return

        if not target_tables:
            try:
                import questionary
                from questionary import Style
                
                custom_style = Style([
                    ('qmark', 'fg:#673ab7 bold'),
                    ('question', 'bold'),
                    ('answer', 'fg:#f44336 bold'),
                    ('pointer', 'fg:#673ab7 bold'),
                    ('highlighted', 'fg:#673ab7 bold'),
                    ('selected', 'fg:#cc2722'),
                    ('separator', 'fg:#cc5454'),
                    ('instruction', 'fg:#858585 italic'),
                    ('text', ''),
                    ('disabled', 'fg:#858585 italic')
                ])

                choices = [questionary.Choice(title=f" {name}", value=name) for name in all_table_names]
                
                # [FIX] Use ask_async() since we are already in an async event loop
                target_tables = await questionary.checkbox(
                    "Sếp hãy chọn các bảng cần thanh tẩy (Space: chọn, Enter: xác nhận):",
                    choices=choices,
                    style=custom_style,
                    instruction="(Nhấn 'a': tất cả, 'i': đảo ngược)"
                ).ask_async()
                
            except Exception as e:
                # Fallback to manual input if questionary fails for any reason
                if not isinstance(e, ImportError):
                    print(f"⚠️ [UI DEBUG] Questionary failed: {e}")
                
                print("\nDanh sách các bảng khả dụng:")
                for i, name in enumerate(all_table_names, 1):
                    print(f"{i}) {name}")
                print("a) TẤT CẢ (ALL)")
                print("q) Hủy bỏ")
                
                choice = input("\nSếp muốn làm sạch bảng nào? (Nhập số, cách nhau bằng dấu phẩy, hoặc 'a'): ").strip().lower()
                
                if choice == 'q':
                    print("-> Đã hủy thao tác.")
                    return
                elif choice == 'a':
                    target_tables = all_table_names
                else:
                    try:
                        indices = [int(idx.strip()) - 1 for idx in choice.split(",") if idx.strip().isdigit()]
                        target_tables = [all_table_names[i] for i in indices if 0 <= i < len(all_table_names)]
                    except Exception as e:
                        print(f"❌ Lựa chọn không hợp lệ: {e}")
                        return

        if not target_tables:
            print("⚠️ Không có bảng nào được chọn.")
            return

        # [ELITE ORDERING] Sắp xếp bảng theo phụ thuộc (Metadata) + Bổ sung bảng lạ từ DB
        ordered_targets = [t.name for t in tables_metadata if t.name in target_tables]
        orphaned_tables = [t for t in target_tables if t not in metadata_names]
        
        # Bảng không có trong metadata sẽ được xử lý trước (vì thường là bảng độc lập hoặc rác)
        final_targets = orphaned_tables + ordered_targets

        print(f"-> Bắt đầu thanh tẩy {len(final_targets)} bảng đã chọn...")
        
        for table in reversed(final_targets):
            print(f"   [PURIFY] Đang làm sạch: {table}...")
            # Use a separate transaction for each table to handle errors gracefully
            try:
                # Start a nested transaction (SAVEPOINT)
                async with session.begin_nested():
                    await session.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE;'))
                print(f"   ✅ Xong: {table}")
            except Exception as e:
                # The nested transaction is automatically rolled back on error
                error_msg = str(e)
                if "undefined_table" in error_msg.lower() or "does not exist" in error_msg.lower():
                    print(f"   ⚠️ [SKIP] Bảng '{table}' không tồn tại trong Database thực tế.")
                else:
                    print(f"   ❌ Lỗi khi làm sạch {table}: {e}")
            
        await session.commit()
        print(f"✨ [SUCCESS] Đã hoàn tất quy trình xử lý {len(target_tables)} mục!")

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    asyncio.run(clean_database(args if args else None))
