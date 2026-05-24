import asyncio
import logging
import sys
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(asctime)s - %(name)s - %(message)s",
    stream=sys.stdout
)

load_dotenv()

from backend.services.telegram_service import telegram_service

async def test_telegram():
    print("🚀 Testing Telegram Direct Dispatch...")
    res = await telegram_service.send_alert("🔔 <b>[FAST-PLATFORM DIRECT TEST]</b>\nHello Sếp! Đây là tin nhắn thử nghiệm trực tiếp từ Agentic AI!")
    print(f"👉 Direct Send result: {res}")

if __name__ == "__main__":
    asyncio.run(test_telegram())
