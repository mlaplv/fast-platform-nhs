import logging
import asyncio
import requests
import os
from typing import Optional, Dict

logger = logging.getLogger("api-gateway")

class ZaloService:
    """
    Elite V2.2: Zalo Intelligence (Business OA Edition) thưa sếp!
    Hỗ trợ đồng bộ tin nhắn khách hàng trực tiếp về Zalo OA của Admin.
    """

    def __init__(self):
        self.api_base = "https://openapi.zalo.me/v2.0/oa"
        self.token_url = "https://oauth.zaloapp.com/v4/oa/access_token"

    @staticmethod
    def _check_sync(phone: str) -> bool:
        """Worker function chạy trong thread riêng để không block Event Loop."""
        try:
            # Format phone chuẩn Việt Nam (Bỏ dấu cách, dấu +)
            clean_phone = "".join(filter(str.isdigit, phone))
            if clean_phone.startswith("84"):
                clean_phone = "0" + clean_phone[2:]

            url = f"https://zalo.me/{clean_phone}"
            # Giả lập Mobile Browser để Zalo không chặn bot thưa sếp!
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
            }

            response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            content = response.text.lower()

            # Dấu hiệu nhận diện tài khoản tồn tại thưa sếp!
            if "nhắn tin cho" in content or "zalo -" in content or "zalo.me/" in response.url:
                if response.url.strip("/") != "https://zalo.me":
                    return True

            return False
        except Exception as e:
            logger.error(f"[ZaloService] Check failed for {phone}: {e}")
            return False

    async def check_existence(self, phone: str) -> bool:
        """Async wrapper cho hàm check đồng bộ thưa sếp!"""
        if not phone:
            return False
        return await asyncio.to_thread(self._check_sync, phone)

    def generate_deep_link(self, phone: str, message: str) -> str:
        """Tạo link mở Zalo và điền sẵn tin nhắn thưa sếp!"""
        import urllib.parse
        clean_phone = "".join(filter(str.isdigit, phone))
        encoded_msg = urllib.parse.quote(message)
        return f"https://zalo.me/{clean_phone}?text={encoded_msg}"

    async def _get_access_token(self) -> Optional[str]:
        """
        Lấy Access Token từ Redis hoặc Refresh từ Zalo API thưa sếp!
        Sử dụng cơ chế Singleton Cache để tối ưu Performance.
        """
        from backend.services.xohi_memory import xohi_memory
        
        # 1. Thử lấy từ Redis trước
        token = await xohi_memory.client.get("system:zalo_oa_access_token")
        if token:
            return token

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
            
            # Sử dụng to_thread để tránh block Loop khi gọi requests.post
            response = await asyncio.to_thread(
                requests.post, self.token_url, data=payload, headers=headers, timeout=10
            )
            data = response.json()

            if "access_token" in data:
                new_token = data["access_token"]
                new_refresh = data.get("refresh_token")
                expires_in = int(data.get("expires_in", 3600)) - 60 # Trừ 1 phút cho an toàn

                # Lưu Access Token vào Redis
                await xohi_memory.client.set("system:zalo_oa_access_token", new_token, ex=expires_in)
                
                # CẬP NHẬT REFRESH TOKEN MỚI (Zalo 2.0 xoay vòng refresh token)
                if new_refresh:
                    # Lưu vào Redis để dùng cho lần sau, sếp cần update lại .env định kỳ nếu VPS restart
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
        Địa chỉ đích: ZALO_ADMIN_ID trong .env
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
            response = await asyncio.to_thread(
                requests.post, url, json=payload, headers=headers, timeout=10
            )
            res_data = response.json()
            if res_data.get("error") != 0:
                logger.error(f"[ZaloService] Push Failed: {res_data}")
            else:
                logger.info(f"[ZaloService] Notified Admin {admin_id} for session {session_id}")
        except Exception as e:
            logger.error(f"[ZaloService] Push request error: {e}")

zalo_service = ZaloService()
