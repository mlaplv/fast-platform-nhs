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

from backend.database import async_session_maker
from backend.database.models.commerce import UserLoyalty

# Table names to truncate (excluding config/campaign tables linked to media registry)
TABLES_TO_TRUNCATE = [
    "orders",
    "point_transactions",
    "user_loyalty",
    "commission_ledger",
    "withdrawal_requests",
    "affiliate_profiles",
    "chat_messages",
    "support_chat_history",
    "agent_telemetry_logs",
    "unified_agent_tasks",
    "audit_logs",
    "click_fraud_events",
    "google_ads_campaign_logs",
    "system_otps",
    "notifications",
    "appointments"
]

async def reset_database():
    print("🔥 [RESET] Khởi động quy trình dọn dẹp Database phục vụ Marketing...")
    
    async with async_session_maker() as session:
        try:
            async with session.begin():
                # 1. Truncate các bảng giao dịch & logs đồng loạt (Không CASCADE để bảo vệ bảng ảnh)
                print("⏳ 1. Đang làm sạch các bảng giao dịch, tích lũy điểm và logs...")
                tables_str = ", ".join(f'"{table}"' for table in TABLES_TO_TRUNCATE)
                await session.execute(text(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY;"))
                print(f"   ✅ Đã TRUNCATE {len(TABLES_TO_TRUNCATE)} bảng giao dịch thành công (Reset Auto-Increment).")
                
                # 2. Xóa voice_profiles của các tài khoản khác admin
                print("⏳ 2. Đang xóa cấu hình giọng nói của các tài khoản khách hàng...")
                voice_delete = await session.execute(text("DELETE FROM voice_profiles WHERE user_id != 'user_admin';"))
                print(f"   ✅ Đã xóa {voice_delete.rowcount} voice profiles.")

                # 3. Xóa tất cả user ngoại trừ 'user_admin' (mlap)
                print("⏳ 3. Đang xóa các tài khoản người dùng thử nghiệm...")
                user_delete = await session.execute(text("DELETE FROM users WHERE id != 'user_admin';"))
                print(f"   ✅ Đã xóa {user_delete.rowcount} tài khoản người dùng thử nghiệm.")
                
                # 4. Khởi tạo lại cấu hình Loyalty trống cho tài khoản 'user_admin'
                print("⏳ 4. Đang khởi tạo lại cấu hình tích điểm trống cho Admin 'mlap'...")
                admin_loyalty = UserLoyalty(
                    user_id="user_admin",
                    tier="STANDARD",
                    available_points=0,
                    pending_points=0,
                    total_spent=0,
                    current_checkin_streak=0
                )
                session.add(admin_loyalty)
                
                print("🎉 5. Thực thi ghi dữ liệu vào Database (Commit)...")
            
            print("✨ [SUCCESS] Đã hoàn tất quy trình reset database phục vụ Marketing thành công!")
            
        except Exception as e:
            print(f"❌ [ERROR] Lỗi trong quá trình reset, đã rollback: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(reset_database())
