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

from backend.services.event_bus import event_bus

async def test_emit():
    print("🚀 [NotificationTest] Initializing test emitter...")
    
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
    
    print("✅ [NotificationTest] All test events emitted successfully!")

if __name__ == "__main__":
    asyncio.run(test_emit())
