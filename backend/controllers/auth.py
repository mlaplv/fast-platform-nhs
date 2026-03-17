import bcrypt
import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from litestar import Controller, post, Request
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.auth import LoginRequest, TokenResponse, RegisterRequest
from backend.services.auth_service import auth_service

auth_limit_value = int(os.getenv("RATE_LIMIT_AUTH_MINUTE", "5"))
auth_rate_limit = RateLimitConfig(rate_limit=("minute", auth_limit_value), store="memory_store")


class AuthController(Controller):
    path = "/api/v1/auth"

    @post("/register", middleware=[auth_rate_limit.middleware])
    async def register(self, db_session: AsyncSession, data: RegisterRequest) -> Dict[str, str]:
        """Register a new user via AuthService."""
        return await auth_service.register(db_session, data)

    @post("/login", middleware=[auth_rate_limit.middleware])
    async def login(self, db_session: AsyncSession, data: LoginRequest) -> TokenResponse:
        """Login via AuthService."""
        return await auth_service.login(db_session, data)

    @staticmethod
    def get_current_user_role(request: Request) -> str:
        """R41: Performance optimization - use the state already resolved by AuthMiddleware."""
        user = getattr(request.state, "user", None)
        if not user:
            return "GUEST"

        roles = user.get("roles", [])
        return roles[0] if isinstance(roles, list) and roles else "GUEST"
