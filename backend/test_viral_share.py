import asyncio
import httpx
import json
import time

API_URL = "http://localhost:8000"
PRODUCT_ID = "prod_miccosmo_eye_cream_basic" # Thay đổi nếu cần

async def test_viral_flow(scenario: str, telemetry: dict):
    print(f"\n[{scenario}] Đang test...")
    async with httpx.AsyncClient() as client:
        # 1. Share Intent
        res = await client.post(f"{API_URL}/api/v1/client/viral/share-intent", json={"product_id": PRODUCT_ID})
        if res.status_code != 201:
            print(f"❌ Failed to get share intent: {res.status_code} {res.text}")
            return
        
        data = res.json()
        print(f"✅ Lấy Token thành công: {data['token'][:10]}...")

        # Giả lập thời gian chia sẻ
        await asyncio.sleep(1)

        # 2. Verify Share
        verify_payload = {
            "product_id": PRODUCT_ID,
            "fingerprint": data["fingerprint"],
            "token": data["token"],
            "voucher_id": "VOUCHER-TEST", # Fake ID for testing if needed
            "telemetry": telemetry
        }
        
        verify_res = await client.post(f"{API_URL}/api/v1/client/viral/verify-share", json=verify_payload)
        
        if verify_res.status_code == 200:
            print(f"✅ Xác minh THÀNH CÔNG! {verify_res.json()}")
        else:
            print(f"❌ Xác minh THẤT BẠI ({verify_res.status_code}): {verify_res.json()}")

async def main():
    print("🚀 Bắt đầu test Viral Share AI Engine")
    
    # Kịch bản 1: Bot (Click nhanh, không tab, không scroll) -> Sẽ bị DENY
    bot_telemetry = {
        "time_on_page_ms": 500,
        "share_duration_ms": 200,
        "visibility_changes": 0,
        "scroll_depth_pct": 0,
        "interaction_count": 1,
        "share_method": "clipboard",
        "popup_was_blocked": True
    }
    await test_viral_flow("Bot Spam", bot_telemetry)

    # Kịch bản 2: Người dùng thật (Đọc lâu, có scroll, có chuyển tab qua lại) -> Sẽ được APPROVE
    real_telemetry = {
        "time_on_page_ms": 12000,
        "share_duration_ms": 8500,
        "visibility_changes": 2,
        "scroll_depth_pct": 80,
        "interaction_count": 5,
        "share_method": "native",
        "popup_was_blocked": False
    }
    await test_viral_flow("Người dùng chân chính", real_telemetry)

    # Kịch bản 3: Bị chặn popup nhưng vẫn đọc trang đàng hoàng -> AI sẽ phân tích (APPROVE hoặc SUSPICIOUS)
    blocked_telemetry = {
        "time_on_page_ms": 8000,
        "share_duration_ms": 2500,
        "visibility_changes": 0,
        "scroll_depth_pct": 45,
        "interaction_count": 3,
        "share_method": "popup",
        "popup_was_blocked": True
    }
    await test_viral_flow("Popup bị chặn (Test Frontend)", blocked_telemetry)

if __name__ == "__main__":
    asyncio.run(main())
