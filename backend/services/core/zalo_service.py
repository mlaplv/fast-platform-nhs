import logging
import asyncio
import requests
from typing import Optional, Dict

logger = logging.getLogger("api-gateway")

class ZaloService:
    """
    Elite V2.2: Zalo Order Intelligence (Lite Free Edition) thưa sếp!
    Sử dụng kỹ thuật phân tích URL Profile để phát hiện Zalo không tốn phí.
    """

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

            # Nếu tồn tại, Zalo thường trả về trang profile có title "Zalo - [Tên]"
            # Hoặc redirect đến một URL chứa UID/Hash.
            # Nếu không tồn tại, nó sẽ về trang chủ hoặc báo lỗi.
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

zalo_service = ZaloService()
