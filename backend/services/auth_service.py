import os
import jwt
import uuid
import bcrypt
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotAuthorizedException, ClientException

from backend.database.models import User, Role
from backend.schemas.auth import (
    LoginRequest, TokenResponse, RegisterRequest,
    SocialLoginResponse, OTPRequestResponse, OTPVerifyResponse
)
from backend.schemas.common import SuccessResponse
from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.signal_center import signal_center

logger = logging.getLogger("api-gateway")

SECRET_KEY = os.environ.get("ENCRYPTION_SALT", "unsafe-default-salt")
ALGORITHM = "HS256"

class AuthService:
    @staticmethod
    async def register(db_session: AsyncSession, data: RegisterRequest) -> SuccessResponse:
        """Handle user registration with CNS V70 signal dispatch."""
        # Check if email exists
        stmt = select(User.id).where(User.email == data.email)
        res = await db_session.execute(stmt)
        if res.scalar_one_or_none():
            raise ClientException(status_code=400, detail="Email này đã được sử dụng")

        user_id = str(uuid.uuid4())
        hashed = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(
            id=user_id,
            username=data.email,  # default username to email
            email=data.email,
            name=data.name,
            password=hashed,
            status="ACTIVE",
            tenant_id="default"
        )
        db_session.add(new_user)
        # Flush to get the user inserted before adding notification/signal
        await db_session.flush()

        # CNS V70: Unified signal dispatch
        await signal_center.dispatch(
            user_id=user_id,
            signal=SignalSchema(
                message=f"Chào mừng {data.name} gia nhập hệ thống",
                severity=SignalSeverity.INFO,
                signal_type="SYSTEM"
            ),
            db_session=db_session
        )

        return SuccessResponse(ok=True, id=user_id, message="Tạo tài khoản thành công")

    @staticmethod
    async def login(db_session: AsyncSession, data: LoginRequest) -> TokenResponse:
        """Handle user login and token generation."""
        # Load user with roles and permissions eagerly (R36)
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where((User.email == data.identifier) | (User.username == data.identifier))
        )
        res = await db_session.execute(stmt)
        user = res.scalar_one_or_none()

        # DUMMY_HASH: timing attack mitigation
        dummy_hash = b"$2b$12$KIXH0V9S1P0n3r2G4.T.Z.Vqy8x9v.2h9D3bY/rE5FmQ6oA7L7f/e"

        is_user_valid = user and user.password is not None
        hash_to_check = user.password.encode('utf-8') if is_user_valid else dummy_hash

        is_valid = bcrypt.checkpw(
            data.password.encode('utf-8'),
            hash_to_check
        )

        if not is_user_valid or not is_valid:
            raise NotAuthorizedException("Invalid email or password")

        # Roles and Permissions
        roles = [r.code for r in getattr(user, "roles", [])]
        permissions = []
        for r in getattr(user, "roles", []):
            permissions.extend([p.code for p in getattr(r, "permissions", [])])
        permissions = list(set(permissions))

        # CNS V70.4: Login signal
        await signal_center.dispatch(
            user_id=str(user.id),
            signal=SignalSchema(
                message=f"Đăng nhập thành công: {user.email}",
                severity=SignalSeverity.INFO,
                signal_type="SECURITY"
            ),
            db_session=db_session
        )

        # THIẾT QUÂN LUẬT: Giới hạn phiên 2 giờ
        expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

        token_data = {
            "id": str(user.id),
            "sub": user.email,
            "roles": roles,
            "perms": permissions,
            "tenant_id": getattr(user, 'tenant_id', 'default'),
            "name": user.name
        }

        access_token = AuthService.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=expire_minutes)
        )

        return TokenResponse(
            access_token=access_token,
            role=roles[0] if roles else "CUSTOMER",
            name=user.name,
            email=user.email
        )

    @staticmethod
    async def social_login(provider: str, data: Dict[str, object]) -> SocialLoginResponse:
        """Stub cho social login (Google, Facebook, Zalo)"""
        return SocialLoginResponse(
            status="success",
            message=f"Social login via {provider} initiated.",
            instructions="Vui lòng cấu hình OAuth2 Credentials trong .env để kích hoạt logic thật."
        )

    @staticmethod
    async def request_otp(data: Dict[str, object]) -> OTPRequestResponse:
        """Stub cho OTP login via Phone"""
        phone = str(data.get("phone", "Unknown"))
        return OTPRequestResponse(
            status="success",
            message=f"Mã OTP đã được gửi đến {phone} (Simulation).",
            otp_token="stub_otp_session_xyz123"
        )

    @staticmethod
    async def verify_otp(data: Dict[str, object]) -> OTPVerifyResponse:
        """Stub cho xác thực OTP"""
        return OTPVerifyResponse(
            status="success",
            access_token="stub_access_token_via_otp",
            role="CUSTOMER"
        )

    @staticmethod
    def create_access_token(data: Dict[str, object], expires_delta: timedelta) -> str:
        """Generate JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

auth_service = AuthService()
