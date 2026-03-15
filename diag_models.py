
import os
import httpx
import asyncio

async def check_models():
    api_key = "AIzaSyAsl3t1zInuOo8tskrz1_FzO9o8GOPrk4A" # Thử với key đầu tiên
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ CÁC MODEL KHẢ DỤNG:")
            for m in models:
                print(f" - {m['name']}")
        else:
            print(f"❌ Lỗi: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(check_models())
