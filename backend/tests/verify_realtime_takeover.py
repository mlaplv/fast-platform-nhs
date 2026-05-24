import asyncio
import json
import logging
import sys
from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory

async def receiver(pubsub):
    print("📥 [Receiver] Bắt đầu lắng nghe...")
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                print(f"✅ [Receiver] Nhận thành công từ kênh {message['channel']}: {message['data']}")
    except asyncio.CancelledError:
        print("📥 [Receiver] Đã dừng.")

async def run_test():
    print("🚀 Bắt đầu kiểm tra PubSub Realtime Takeover song song...")
    
    session_id = "test_takeover_session_123"
    payload = {
        "session_id": session_id,
        "message": "Xin chào từ chuyên viên tư vấn qua EventBus!",
        "role": "assistant"
    }

    pubsub = xohi_memory.client.pubsub()
    await pubsub.subscribe(f"pulse:{session_id}", "admin:pulse")
    
    # Khởi chạy receiver
    recv_task = asyncio.create_task(receiver(pubsub))
    
    # Chờ 0.5s để đăng ký hoàn tất
    await asyncio.sleep(0.5)
    
    # Emit event SUPPORT_INBOX_UPDATE qua event_bus
    await event_bus.emit("SUPPORT_INBOX_UPDATE", payload)
    print("🔥 Đã phát sự kiện SUPPORT_INBOX_UPDATE qua EventBus")
    
    # Chờ 2.0s để background tasks của event_bus xử lý xong và receiver nhận được tin nhắn
    await asyncio.sleep(2.0)

    # Dừng receiver
    recv_task.cancel()
    await pubsub.unsubscribe()
    print("🏁 Kết thúc kiểm tra")

if __name__ == "__main__":
    asyncio.run(run_test())
