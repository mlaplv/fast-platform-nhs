import logging
import httpx
import os

logger = logging.getLogger("api-gateway")


class TelegramService:
    _instance = None

    def __new__(cls) -> "TelegramService":
        if cls._instance is None:
            cls._instance = super(TelegramService, cls).__new__(cls)
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

            cls._instance.enabled = bool(token and chat_id)
            cls._instance.token = token
            cls._instance.chat_id = chat_id

            # Elite V2.2: Connection pooling & strict timeouts to avoid resource leakage
            if cls._instance.enabled:
                cls._instance.client = httpx.AsyncClient(
                    limits=httpx.Limits(max_keepalive_connections=3, max_connections=5),
                    timeout=httpx.Timeout(3.0)
                )
                logger.info("📡 [TelegramService] Active connection pool established.")
            else:
                logger.warning("⚠️ [TelegramService] Disabled. BOT_TOKEN or CHAT_ID is missing in environmental variables.")
        return cls._instance

    async def send_alert(self, message: str) -> bool:
        """
        Sends an alert message to Telegram channel asynchronously (Elite V2.2).
        Guarantees zero blocking of the event loop and extremely lightweight footprints.
        """
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            resp = await self.client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("✅ [TelegramService] Alert message dispatched successfully.")
                return True
            else:
                logger.warning(f"⚠️ [TelegramService] Failed to send Telegram alert: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"❌ [TelegramService] Network or connection timeout sending Telegram alert: {e}")
            return False


telegram_service = TelegramService()
