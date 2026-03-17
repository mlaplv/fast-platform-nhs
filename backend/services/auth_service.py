import bcrypt
import os
import jwt
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, cast
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotAuthorizedException, ClientException

from backend.database.models import User, Role
from backend.schemas.auth import LoginRequest, TokenResponse, RegisterRequest
from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.signal_center import signal_center

logger = logging.getLogger("api-gateway")

SECRET_KEY = os.environ.get("ENCRYPTION_SALT")
if not SECRET_KEY:
    raise RuntimeError("ENCRYPTION_SALT environment variable is not set")
ALGORITHM = "HS256"

class AuthService:
    """
    ULTRA-LEAN AUTH SERVICE (ELITE V2.2)
    ------------------------------------
    Centralizes Registration, Login, and JWT Token management.
    """

    async def register(self, session: AsyncSession, data: RegisterRequest) -> Dict[str, str]:
        """Register a new user with secure hashing and signal dispatch."""
        # Check if email exists
        stmt = select(User.id).where(User.email == data.email)
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            raise ClientException(status_code=400, detail="Email này đã được sử dụng")

        user_id = str(uuid.uuid4())
        hashed = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(
            id=user_id,
            username=data.email, # default username to email
            email=data.email,
            name=data.name,
            password=hashed,
            status="ACTIVE",
            tenant_id="default"
        )
        session.add(new_user)
        # Flush to get the user inserted before adding notification
        await session.flush()

        # CNS V70: Unified signal dispatch
        await signal_center.dispatch(
            user_id=user_id,
            signal=SignalSchema(
                message=f"Chào mừng {data.name} gia nhập hệ thống",
                severity=SignalSeverity.INFO,
                signal_type="SYSTEM"
            ),
            db_session=session
        )

        return {"id": user_id, "message": "Tạo tài khoản thành công"}

    async def login(self, session: AsyncSession, data: LoginRequest) -> TokenResponse:
        """Authenticate user and generate access token."""
        # Load user with roles and permissions eagerly (R36)
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where((User.email == data.identifier) | (User.username == data.identifier))
        )
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        # DUMMY_HASH: timing attack mitigation
        dummy_hash = b"$2b$12$KIXH0V9S1P0n3r2G4.T.Z.Vqy8x9v.2h9D3bY/rE5FmQ6oA7L7f/e"

        is_user_valid = user is not None and user.password is not None

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
        if hasattr(user, "roles"):
            for r in user.roles:
                if hasattr(r, "permissions"):
                    permissions.extend([p.code for p in r.permissions])
        permissions = list(set(permissions))

        # CNS V70.4: Login signal
        await signal_center.dispatch(
            user_id=str(user.id),
            signal=SignalSchema(
                message=f"Đăng nhập thành công: {user.email}",
                severity=SignalSeverity.INFO,
                signal_type="SECURITY"
            ),
            db_session=session
        )

        # THIẾT QUÂN LUẬT: Giới hạn phiên 2 giờ
        expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
        access_token = self.create_access_token(
            data={
                "id": str(user.id),
                "sub": user.email,
                "roles": roles,
                "perms": permissions,
                "tenant_id": getattr(user, 'tenant_id', 'default'),
                "name": user.name
            },
            expires_delta=timedelta(minutes=expire_minutes)
        )

        return TokenResponse(
            access_token=access_token,
            role=roles[0] if roles else "CUSTOMER",
            name=user.name,
            email=user.email
        )

    def create_access_token(self, data: Dict[str, object], expires_delta: timedelta) -> str:
        """Generate a secure JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    async def social_login(self, provider: str, data: Dict[str, object]) -> Dict[str, object]:
        """Social login logic (Future-ready stub)."""
        return {
            "status": "success",
            "message": f"Social login via {provider} initiated.",
            "instructions": "Vui lòng cấu hình OAuth2 Credentials trong .env để kích hoạt logic thật."
        }

    async def request_otp(self, phone: str) -> Dict[str, object]:
        """Request OTP logic (Future-ready stub)."""
        return {
            "status": "success",
            "message": f"Mã OTP đã được gửi đến {phone} (Simulation).",
            "otp_token": "stub_otp_session_xyz123"
        }

    async def verify_otp(self, data: Dict[str, object]) -> Dict[str, object]:
        """Verify OTP logic (Future-ready stub)."""
        return {
            "status": "success",
            "access_token": "stub_access_token_via_otp",
            "role": "CUSTOMER"
        }

# Singleton
auth_service = AuthService()
