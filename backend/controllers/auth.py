from __future__ import annotations
import os
import logging
from typing import Dict, List, Optional
from litestar import Controller, post, Request
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.auth import LoginRequest, TokenResponse, RegisterRequest, SocialLoginResponse, OTPRequestResponse, OTPVerifyResponse
from backend.schemas.common import SuccessResponse
from backend.services.auth_service import auth_service

logger = logging.getLogger("api-gateway")

auth_limit_value = int(os.getenv("RATE_LIMIT_AUTH_MINUTE", "5"))
auth_rate_limit = RateLimitConfig(rate_limit=("minute", auth_limit_value), store="memory_store")

class AuthController(Controller):
    path = "/api/v1/auth"

    @post("/register", middleware=[auth_rate_limit.middleware])
    async def register(self, db_session: "AsyncSession", data: RegisterRequest) -> SuccessResponse:
        """PUBLIC: Handle user registration via AuthService."""
        res = await auth_service.register(db_session, data)
        await db_session.commit()
        return res

    @post("/login", middleware=[auth_rate_limit.middleware])
    async def login(self, db_session: "AsyncSession", data: LoginRequest) -> TokenResponse:
        """PUBLIC: Handle user login via AuthService."""
        # NOTE: Login does not need commit unless it modifies data (signals are flushed/committed by middleware usually)
        # However, to be safe and consistent with Service-Centric rules for mutations:
        res = await auth_service.login(db_session, data)
        await db_session.commit()
        return res

    # ═══════════════════════════════════════════════════════
    # EXTENDED AUTH (Social & OTP) - Consolidated
    # ═══════════════════════════════════════════════════════

    @post("/social/{provider:str}", middleware=[auth_rate_limit.middleware])
    async def social_login(self, provider: str, data: Dict[str, object]) -> SocialLoginResponse:
        """Stub cho social login (Google, Facebook, Zalo)"""
        return await auth_service.social_login(provider, data)

    @post("/otp/request", middleware=[auth_rate_limit.middleware])
    async def request_otp(self, data: Dict[str, object]) -> OTPRequestResponse:
        """Stub cho OTP login via Phone"""
        return await auth_service.request_otp(data)

    @post("/otp/verify", middleware=[auth_rate_limit.middleware])
    async def verify_otp(self, data: Dict[str, object]) -> OTPVerifyResponse:
        """Stub cho xác thực OTP"""
        return await auth_service.verify_otp(data)

    @staticmethod
    def get_current_user_role(request: Request) -> str:
        """R41: Performance optimization - use the state already resolved by AuthMiddleware."""
        user = getattr(request.state, "user", None)
        if not user:
            return "GUEST"

        roles = user.get("roles", [])
        return roles[0] if isinstance(roles, list) and roles else "GUEST"
