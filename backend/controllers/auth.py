from __future__ import annotations
import os
import logging
from typing import Dict, List, Optional
from litestar import Controller, post, get, Request
from litestar.response import Redirect
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.auth import (
    LoginRequest, TokenResponse, RegisterRequest, SocialLoginResponse, 
    OTPRequestResponse, OTPVerifyResponse, SocialLoginRequest, OTPRequest, OTPVerifyRequest
)
from backend.schemas.common import SuccessResponse
from backend.services.auth_service import auth_service
from backend.services.oauth_service import oauth2_service

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

    @get("/oauth/login/{provider:str}")
    async def oauth_login(self, provider: str) -> Redirect:
        """PUBLIC: Chuyển hướng người dùng sang trang Đăng nhập của Service"""
        login_url = oauth2_service.get_login_url(provider)
        return Redirect(path=login_url)

    @get("/oauth/callback/{provider:str}")
    async def oauth_callback(self, db_session: "AsyncSession", provider: str, code: str) -> Redirect:
        """PUBLIC: Hứng Authorization Code từ Service, sinh JWT trả về Client"""
        # 1. Giao tiếp lấy profile
        user_profile = await oauth2_service.exchange_code_for_user(provider, code)
        
        # 2. Xử lý User trong CSDL (AuthService)
        access_token = await auth_service.handle_social_user(db_session, user_profile)
        await db_session.commit()
        
        # 3. Chuyển hướng vòng vây về Client Route ẩn
        frontend_callback = f"{oauth2_service.frontend_url}/auth/callback?token={access_token}"
        return Redirect(path=frontend_callback)

    @post("/otp/request", middleware=[auth_rate_limit.middleware])
    async def request_otp(self, db_session: "AsyncSession", data: OTPRequest) -> OTPRequestResponse:
        """PUBLIC: Request OTP login via Phone or Email."""
        res = await auth_service.request_otp(db_session, data.model_dump())
        await db_session.commit()
        return res

    @post("/otp/verify", middleware=[auth_rate_limit.middleware])
    async def verify_otp(self, db_session: "AsyncSession", data: OTPVerifyRequest) -> OTPVerifyResponse:
        """PUBLIC: Verify OTP code and generate access token."""
        res = await auth_service.verify_otp(db_session, data.model_dump())
        await db_session.commit()
        return res

    @staticmethod
    def get_current_user_role(request: Request) -> str:
        """R41: Performance optimization - use the state already resolved by AuthMiddleware."""
        user = getattr(request.state, "user", None)
        if not user:
            return "GUEST"

        roles = user.get("roles", [])
        return roles[0] if isinstance(roles, list) and roles else "GUEST"
