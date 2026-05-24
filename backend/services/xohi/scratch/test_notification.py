import asyncio
import logging
import sys
import uuid
from datetime import datetime, timezone

# Transparent Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(asctime)s - %(name)s - %(message)s",
    stream=sys.stdout
)

# Load env variables for testing Telegram Bot Token / Chat ID
from dotenv import load_dotenv
load_dotenv()

from backend.services.event_bus import event_bus
from backend.services.xohi_responder import setup_subscriptions

async def test_emit():
    print("🚀 [NotificationTest] Initializing test emitter...")
    
    # Start EventBus background loop
    await event_bus.start()
    
    # Register all callbacks (including xohi_responder.handle_system_signal)
    setup_subscriptions()
    
    # 1. Test SUPPORT_INBOX_UPDATE (Client Chat)
    session_id = str(uuid.uuid4())
    print(f"💬 Emitting SUPPORT_INBOX_UPDATE with role='user' for session {session_id}...")
    await event_bus.emit("SUPPORT_INBOX_UPDATE", {
        "session_id": session_id,
        "message": "Sếp ơi, hệ thống chuông báo thời gian thực đã hoạt động hoàn hảo! 🔔",
        "role": "user"
    })
    
    await asyncio.sleep(2)
    
    # 2. Test SYSTEM_SIGNAL (New Order with ACTION severity)
    notif_id = str(uuid.uuid4())
    print(f"🛒 Emitting SYSTEM_SIGNAL (New Order, ACTION) notification_id={notif_id}...")
    await event_bus.emit("SYSTEM_SIGNAL", {
        "notification_id": notif_id,
        "user_id": "user_admin",
        "message": "Đơn hàng mới từ chị Hà Vy: 1x Kem dưỡng sáng cổ Hurry Harry 40gr. 🛒",
        "severity": "ACTION",
        "signal_type": "ORDER",
        "payload": {
            "order_id": "ord_test_9999",
            "customer_name": "Hà Vy",
            "total_amount": 350000
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    await asyncio.sleep(2)
    
    # 3. Test SYSTEM_SIGNAL (Urgent Support with CRITICAL severity)
    urgent_id = str(uuid.uuid4())
    print(f"🚨 Emitting SYSTEM_SIGNAL (Urgent Support, CRITICAL) notification_id={urgent_id}...")
    await event_bus.emit("SYSTEM_SIGNAL", {
        "notification_id": urgent_id,
        "user_id": "user_admin",
        "message": "Khách VIP 091****888 yêu cầu gọi lại trong 30s! Nguồn: Trang chủ",
        "severity": "CRITICAL",
        "signal_type": "URGENT_SUPPORT",
        "payload": {
            "phone": "0912345888",
            "source_url": "https://smartshop.test/"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Sleep to let Telegram background task execute
    print("⏳ Waiting 3 seconds for background tasks to complete...")
    await asyncio.sleep(3)
    
    # Stop EventBus
    await event_bus.stop()
    print("✅ [NotificationTest] All test events emitted and processed successfully!")

if __name__ == "__main__":
    asyncio.run(test_emit())


