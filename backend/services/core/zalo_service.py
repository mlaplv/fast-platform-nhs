import logging
import asyncio
import httpx
import os
from typing import Optional, Dict

logger = logging.getLogger("api-gateway")

class ZaloService:
    """
    Elite V2.2: Zalo Intelligence (Business OA Edition) thưa sếp!
    Hỗ trợ đồng bộ tin nhắn khách hàng trực tiếp về Zalo OA của Admin.
    Native Async I/O (Rule R01) implementation using httpx.
    """

    def __init__(self):
        self.api_base = "https://openapi.zalo.me/v2.0/oa"
        self.token_url = "https://oauth.zaloapp.com/v4/oa/access_token"

    async def check_existence(self, phone: str) -> bool:
        """Kiểm tra sự tồn tại của Zalo user (Native Async - R00)."""
        if not phone:
            return False
            
        try:
            # Format phone chuẩn Việt Nam (Bỏ dấu cách, dấu +)
            clean_phone = "".join(filter(str.isdigit, phone))
            if clean_phone.startswith("84"):
                clean_phone = "0" + clean_phone[2:]

            url = f"https://zalo.me/{clean_phone}"
            # Giả lập Mobile Browser để Zalo không chặn bot
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
            }

            async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                content = response.text.lower()
                final_url = str(response.url)

                # Dấu hiệu nhận diện tài khoản tồn tại
                if "nhắn tin cho" in content or "zalo -" in content or "zalo.me/" in final_url:
                    if final_url.strip("/") != "https://zalo.me":
                        return True

            return False
        except Exception as e:
            logger.error(f"[ZaloService] Check failed for {phone}: {e}")
            return False

    def generate_deep_link(self, phone: str, message: str) -> str:
        """Tạo link mở Zalo và điền sẵn tin nhắn thưa sếp!"""
        import urllib.parse
        clean_phone = "".join(filter(str.isdigit, phone))
        encoded_msg = urllib.parse.quote(message)
        return f"https://zalo.me/{clean_phone}?text={encoded_msg}"

    async def _get_access_token(self) -> Optional[str]:
        """
        Lấy Access Token từ Redis hoặc Refresh từ Zalo API thưa sếp!
        Native Async via httpx (Rule R102).
        """
        from backend.services.xohi_memory import xohi_memory
        
        # 1. Thử lấy từ Redis trước
        token = await xohi_memory.client.get("system:zalo_oa_access_token")
        if token:
            return token if isinstance(token, str) else token.decode("utf-8")

        # 2. Nếu không có, thực hiện Refresh
        refresh_token = os.getenv("ZALO_OA_REFRESH_TOKEN")
        client_id = os.getenv("OAUTH_ZALO_CLIENT_ID")
        client_secret = os.getenv("OAUTH_ZALO_CLIENT_SECRET")

        if not refresh_token or not client_id or not client_secret:
            logger.warning("[ZaloService] Missing Zalo OA Credentials in .env")
            return None

        try:
            payload = {
                "refresh_token": refresh_token,
                "app_id": client_id,
                "grant_type": "refresh_token"
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "secret_key": client_secret
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.token_url, data=payload, headers=headers)
                data = response.json()

            if "access_token" in data:
                new_token = data["access_token"]
                new_refresh = data.get("refresh_token")
                expires_in = int(data.get("expires_in", 3600)) - 60

                # Lưu Access Token vào Redis
                await xohi_memory.client.set("system:zalo_oa_access_token", new_token, ex=expires_in)
                
                # CẬP NHẬT REFRESH TOKEN MỚI (Zalo 2.0 xoay vòng refresh token)
                if new_refresh:
                    await xohi_memory.client.set("system:zalo_oa_refresh_token", new_refresh)
                    logger.info("[ZaloService] Zalo OA Refresh Token rotated successfully.")
                
                return new_token
            else:
                logger.error(f"[ZaloService] Refresh Token Failed: {data}")
                return None
        except Exception as e:
            logger.error(f"[ZaloService] Access Token retrieval error: {e}")
            return None

    async def push_support_notification(self, customer_name: str, message: str, session_id: str):
        """
        Đẩy thông báo chat khách hàng vào Zalo OA của Admin thưa sếp!
        Native Async (Elite R03 - Full I/O Safety).
        """
        admin_id = os.getenv("ZALO_ADMIN_ID")
        if not admin_id:
            logger.warning("[ZaloService] ZALO_ADMIN_ID not configured. Skipping push.")
            return

        token = await self._get_access_token()
        if not token:
            return

        text = (
            f"🔔 [HỖ TRỢ KHÁCH HÀNG]\n"
            f"👤 Khách: {customer_name}\n"
            f"💬 Nội dung: {message}\n"
            f"🔗 Session: {session_id}\n"
            f"Hệ thống: Vui lòng vào Admin Panel để xử lý ạ!"
        )

        payload = {
            "recipient": {"user_id": admin_id},
            "message": {"text": text}
        }
        headers = {
            "Content-Type": "application/json",
            "access_token": token
        }

        try:
            url = f"{self.api_base}/message"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                res_data = response.json()
                
            if res_data.get("error") != 0:
                logger.error(f"[ZaloService] Push Failed: {res_data}")
            else:
                logger.info(f"[ZaloService] Notified Admin {admin_id} for session {session_id}")
        except Exception as e:
            logger.error(f"[ZaloService] Push request error: {e}")

    async def push_order_notification(self, order_id: str, customer_name: str, total_amount: float, gift_info: Optional[Dict] = None):
        """
        Đẩy thông báo đơn hàng mới (kèm Gift Info) tới Zalo OA Admin thưa sếp!
        """
        admin_id = os.getenv("ZALO_ADMIN_ID")
        if not admin_id:
            return

        token = await self._get_access_token()
        if not token:
            return

        message_lines = [
            f"🎁 [ĐƠN HÀNG MỚI - QUÀ TẶNG]",
            f"👤 Người nhận: {customer_name}",
            f"💰 Tổng: {total_amount:,.0f} VNĐ",
        ]

        if gift_info:
            message_lines.append(f"━━━━━━━━━━━━━━━━━━")
            message_lines.append(f"👨‍💼 Người tặng: {gift_info.get('sender_name', 'N/A')}")
            message_lines.append(f"📞 SĐT Tặng: {gift_info.get('sender_phone', 'N/A')}")
            message_lines.append(f"💌 Lời nhắn: {gift_info.get('message', 'Không có')}")
            message_lines.append(f"🎁 Gói quà: {gift_info.get('packaging', 'Tiêu chuẩn')}")

        message_lines.append(f"🔗 ID Đơn: {order_id}")
        text = "\n".join(message_lines)

        payload = {
            "recipient": {"user_id": admin_id},
            "message": {"text": text}
        }
        headers = {"Content-Type": "application/json", "access_token": token}

        try:
            url = f"{self.api_base}/message"
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json=payload, headers=headers)
        except Exception as e:
            logger.error(f"[ZaloService] Order Push Failed: {e}")

zalo_service = ZaloService()
