import os
from litestar import Controller, post
from litestar.middleware.rate_limit import RateLimitConfig
from typing import Dict
from litestar.stores.memory import MemoryStore

# Create a dedicated rate-limit configuration for Authentication
auth_limit_value = int(os.getenv("RATE_LIMIT_AUTH_MINUTE", "5"))
auth_rate_limit = RateLimitConfig(rate_limit=("minute", auth_limit_value), store=MemoryStore())

class AuthExtendedController(Controller):
    path = "/api/v1/auth/extended"
    
    @post("/social/{provider:str}", middleware=[auth_rate_limit.middleware])
    async def social_login(self, provider: str, data: Dict[str, object]) -> Dict[str, object]:
        """Stub cho social login (Google, Facebook, Zalo)"""
        return {
            "status": "success",
            "message": f"Social login via {provider} initiated.",
            "instructions": "Vui lòng cấu hình OAuth2 Credentials trong .env để kích hoạt logic thật."
        }
        
    @post("/otp/request", middleware=[auth_rate_limit.middleware])
    async def request_otp(self, data: Dict[str, object]) -> Dict[str, object]:
        """Stub cho OTP login via Phone"""
        phone = data.get("phone")
        return {
            "status": "success",
            "message": f"Mã OTP đã được gửi đến {phone} (Simulation).",
            "otp_token": "stub_otp_session_xyz123"
        }

    @post("/otp/verify", middleware=[auth_rate_limit.middleware])
    async def verify_otp(self, data: Dict[str, object]) -> Dict[str, object]:
        """Stub cho xác thực OTP"""
        return {
            "status": "success",
            "access_token": "stub_access_token_via_otp",
            "role": "CUSTOMER"
        }
