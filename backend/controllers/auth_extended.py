import os
from litestar import Controller, post
from litestar.middleware.rate_limit import RateLimitConfig
from typing import Dict
from litestar.stores.memory import MemoryStore

# Create a dedicated rate-limit configuration for Authentication
auth_limit_value = int(os.getenv("RATE_LIMIT_AUTH_MINUTE", "5"))
auth_rate_limit = RateLimitConfig(rate_limit=("minute", auth_limit_value), store="memory_store")

from litestar import Controller, post
from litestar.middleware.rate_limit import RateLimitConfig
from typing import Dict
import os
from backend.services.auth_service import auth_service

# Create a dedicated rate-limit configuration for Authentication
auth_limit_value = int(os.getenv("RATE_LIMIT_AUTH_MINUTE", "5"))
auth_rate_limit = RateLimitConfig(rate_limit=("minute", auth_limit_value), store="memory_store")

class AuthExtendedController(Controller):
    path = "/api/v1/auth/extended"

    @post("/social/{provider:str}", middleware=[auth_rate_limit.middleware])
    async def social_login(self, provider: str, data: Dict[str, object]) -> Dict[str, object]:
        """Social login via AuthService."""
        return await auth_service.social_login(provider, data)

    @post("/otp/request", middleware=[auth_rate_limit.middleware])
    async def request_otp(self, data: Dict[str, object]) -> Dict[str, object]:
        """Request OTP via AuthService."""
        phone = str(data.get("phone", "unknown"))
        return await auth_service.request_otp(phone)

    @post("/otp/verify", middleware=[auth_rate_limit.middleware])
    async def verify_otp(self, data: Dict[str, object]) -> Dict[str, object]:
        """Verify OTP via AuthService."""
        return await auth_service.verify_otp(data)
