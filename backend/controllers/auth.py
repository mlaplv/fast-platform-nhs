from __future__ import annotations
import logging
from litestar import Controller, post, get, Request, Response
from litestar.response import Redirect
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession
import os

from backend.constants.tenants import ADMIN_DOMAIN, APP_DOMAIN
from backend.schemas.auth import (
    LoginRequest, TokenResponse, RegisterRequest,
    OTPRequestResponse, OTPVerifyResponse, OTPRequest, OTPVerifyRequest
)
from backend.schemas.common import SuccessResponse
from backend.services.auth_service import auth_service
from backend.services.oauth_service import oauth2_service

logger = logging.getLogger("api-gateway")

auth_limit_value = int(os.getenv("RATE_LIMIT_AUTH_MINUTE", "5"))
auth_rate_limit = RateLimitConfig(rate_limit=("minute", auth_limit_value), store="memory_store")

# R00: Territory-Isolated Cookie Domains (CRITICAL SECURITY)
# Admin: exact domain (no dot prefix) → CHỆ gửi đến admin.osmo.vn
# Storefront: wildcard domain (dot prefix) → gửi đến osmo.vn và subdomains
_ADMIN_COOKIE_DOMAIN: str = ADMIN_DOMAIN                                     # "admin.osmo.vn"
_STOREFRONT_COOKIE_DOMAIN: str | None = f".{APP_DOMAIN}" if "." in APP_DOMAIN else None  # ".osmo.vn"
_MAX_AGE_SHORT: int = 7200            # 2 hours (default)
_MAX_AGE_LONG: int  = 7 * 24 * 3600  # 7 days (remember_me)


class AuthController(Controller):
    path = "/api/v1/auth"

    @staticmethod
    def _is_admin_host(request: Request) -> bool:
        """Elite V2.2: Deterministic admin territory detection using SSOT constant."""
        host = (request.headers.get("host", "") or "").split(":")[0].lower()
        return host == ADMIN_DOMAIN

    @staticmethod
    def _set_secure_cookie(response: Response, token: str, is_admin: bool, remember_me: bool = False) -> None:
        """Elite V2.2: Military-Grade Cookie Provisioning — Territory-Isolated Domains."""
        key = "admin_token" if is_admin else "access_token"
        max_age = _MAX_AGE_LONG if remember_me else _MAX_AGE_SHORT

        # CRITICAL: Admin cookie dùng EXACT domain (không dấu chấm) để
        # KHÔNG bao giờ bị gửi sang storefront domain.
        # Storefront cookie dùng wildcard domain (.osmo.vn).
        domain = _ADMIN_COOKIE_DOMAIN if is_admin else _STOREFRONT_COOKIE_DOMAIN

        response.set_cookie(
            key=key,
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=max_age,
            domain=domain,
            path="/"
        )

    @post("/register", middleware=[auth_rate_limit.middleware])
    async def register(self, db_session: AsyncSession, data: RegisterRequest) -> SuccessResponse:
        """PUBLIC: Handle user registration via AuthService."""
        res = await auth_service.register(db_session, data)
        await db_session.commit()
        return res

    @post("/login", middleware=[auth_rate_limit.middleware])
    async def login(self, request: Request, db_session: AsyncSession, data: LoginRequest) -> Response[TokenResponse]:
        """PUBLIC: Handle user login via AuthService with Military-Grade Cookies."""
        res = await auth_service.login(db_session, data)
        await db_session.commit()

        is_admin = self._is_admin_host(request)
        resp: Response[TokenResponse] = Response(content=res)
        self._set_secure_cookie(resp, res.access_token, is_admin, data.remember_me)
        return resp

    # ═══════════════════════════════════════════════════════
    # EXTENDED AUTH (Social & OTP) - Consolidated
    # ═══════════════════════════════════════════════════════

    @get("/oauth/login/{provider:str}")
    async def oauth_login(self, request: Request, provider: str) -> Redirect:
        """PUBLIC: Chuyển hướng người dùng sang trang Đăng nhập của Provider."""
        login_url, code_verifier = oauth2_service.get_login_url(provider)
        resp = Redirect(path=login_url)
        if code_verifier:
            resp.set_cookie(
                key="zalo_code_verifier",
                value=code_verifier,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=300,
                path="/"
            )
        return resp

    @get("/oauth/callback/{provider:str}")
    async def oauth_callback(self, request: Request, db_session: AsyncSession, provider: str, code: str) -> Redirect:
        """PUBLIC: Hứng Authorization Code từ Provider, sinh JWT và set HttpOnly Cookie."""
        code_verifier = request.cookies.get("zalo_code_verifier")
        user_profile = await oauth2_service.exchange_code_for_user(provider, code, code_verifier)
        access_token = await auth_service.handle_social_user(db_session, user_profile)
        await db_session.commit()

        # Social Login luôn remember_me=True (UX chuẩn)
        is_admin = self._is_admin_host(request)
        frontend_callback = f"{oauth2_service.frontend_url}/auth/callback?token={access_token}"
        resp = Redirect(path=frontend_callback)
        if code_verifier:
            resp.delete_cookie(key="zalo_code_verifier", path="/")
            
        self._set_secure_cookie(resp, access_token, is_admin, remember_me=True)
        return resp

    @post("/otp/request", middleware=[auth_rate_limit.middleware])
    async def request_otp(self, db_session: AsyncSession, data: OTPRequest) -> OTPRequestResponse:
        """PUBLIC: Request OTP login via Phone or Email."""
        res = await auth_service.request_otp(db_session, data.model_dump())
        await db_session.commit()
        return res

    @post("/otp/verify", middleware=[auth_rate_limit.middleware])
    async def verify_otp(self, request: Request, db_session: AsyncSession, data: OTPVerifyRequest) -> Response[OTPVerifyResponse]:
        """PUBLIC: Verify OTP code and generate access token with Military-Grade Cookies."""
        res = await auth_service.verify_otp(db_session, data.model_dump())
        await db_session.commit()

        # OTP Login luôn remember_me=True (user đã xác thực số điện thoại)
        is_admin = self._is_admin_host(request)
        resp: Response[OTPVerifyResponse] = Response(content=res)
        self._set_secure_cookie(resp, res.access_token, is_admin, remember_me=True)
        return resp

    @staticmethod
    def get_current_user_role(request: Request) -> str:
        """R41: Performance optimization — use state already resolved by AuthMiddleware."""
        user = getattr(request.state, "user", None)
        if not user:
            return "GUEST"
        roles: list[str] = user.get("roles", [])
        return roles[0] if roles else "GUEST"
