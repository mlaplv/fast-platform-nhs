import asyncio
import json
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
    print("🚀 Bắt đầu kiểm tra trực tiếp Redis Pub/Sub song song...")
    
    session_id = "test_takeover_session_123"
    channel_client = f"pulse:{session_id}"
    channel_admin = "admin:pulse"
    
    payload = {
        "event": "SUPPORT_INBOX_UPDATE",
        "payload": {
            "session_id": session_id,
            "message": "Xin chào song song từ Redis!",
            "role": "assistant"
        }
    }

    pubsub = xohi_memory.client.pubsub()
    await pubsub.subscribe(channel_client, channel_admin)
    
    # Khởi chạy receiver task
    recv_task = asyncio.create_task(receiver(pubsub))
    
    # Chờ 0.5s để đảm bảo subscribe hoàn tất trên Redis server
    await asyncio.sleep(0.5)

    # Publish
    str_payload = json.dumps(payload, ensure_ascii=False)
    await xohi_memory.client.publish(channel_client, str_payload)
    await xohi_memory.client.publish(channel_admin, str_payload)
    print("🔥 Đã publish trực tiếp lên Redis")

    # Chờ 1s để receiver nhận tin nhắn
    await asyncio.sleep(1.0)

    # Dừng receiver
    recv_task.cancel()
    await pubsub.unsubscribe()
    print("🏁 Kết thúc kiểm tra")

if __name__ == "__main__":
    asyncio.run(run_test())
