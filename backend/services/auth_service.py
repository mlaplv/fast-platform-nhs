import bcrypt
import os
import jwt
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, cast
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotAuthorizedException, ClientException

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
        """Register a new user with secure hashing and Scalar Insert (Zero-Hydration)."""
        # Check if email exists
        stmt = text("SELECT id FROM users WHERE email = :email LIMIT 1")
        res = await session.execute(stmt, {"email": data.email})
        if res.scalar():
            raise ClientException(status_code=400, detail="Email này đã được sử dụng")

        user_id = str(uuid.uuid4())
        hashed = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Rule R1.5: Zero-Hydration Insert
        await session.execute(
            text("""
                INSERT INTO users (id, username, email, name, password, status, tenant_id, created_at, updated_at)
                VALUES (:id, :username, :email, :name, :pwd, 'ACTIVE', 'default', NOW(), NOW())
            """),
            {
                "id": user_id,
                "username": data.email,
                "email": data.email,
                "name": data.name,
                "pwd": hashed
            }
        )

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
        """Authenticate user and generate access token via text-SQL (Zero-Hydration)."""
        # Load user info and RBAC via Scalar Projection
        sql = text("""
            SELECT
                u.id, u.email, u.password, u.name, u.tenant_id, u.status,
                r.code as role_code,
                p.code as perm_code
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE (u.email = :idnt OR u.username = :idnt) AND u.deleted_at IS NULL
        """)

        res = await session.execute(sql, {"idnt": data.identifier})
        rows = res.all()

        # DUMMY_HASH: timing attack mitigation
        dummy_hash = b"$2b$12$KIXH0V9S1P0n3r2G4.T.Z.Vqy8x9v.2h9D3bY/rE5FmQ6oA7L7f/e"

        if not rows:
            # Hash dummy to prevent timing leaks
            bcrypt.checkpw(data.password.encode('utf-8'), dummy_hash)
            raise NotAuthorizedException("Invalid email or password")

        # Basic User Info (first row)
        u_id = str(rows[0][0])
        u_email = rows[0][1]
        u_pwd = rows[0][2]
        u_name = rows[0][3]
        u_tenant = rows[0][4] or "default"
        u_status = rows[0][5]

        if u_status == "LOCKED":
            raise NotAuthorizedException("Tài khoản đã bị khóa")

        is_valid = bcrypt.checkpw(
            data.password.encode('utf-8'),
            u_pwd.encode('utf-8') if u_pwd else dummy_hash
        )

        if not is_valid:
            raise NotAuthorizedException("Invalid email or password")

        # Collect Roles and Permissions from rows
        roles = set()
        perms = set()
        for row in rows:
            if row[6]: roles.add(row[6]) # role_code
            if row[7]: perms.add(row[7]) # perm_code

        roles_list = list(roles)
        perms_list = list(perms)

        # CNS V70.4: Login signal
        await signal_center.dispatch(
            user_id=u_id,
            signal=SignalSchema(
                message=f"Đăng nhập thành công: {u_email}",
                severity=SignalSeverity.INFO,
                signal_type="SECURITY"
            ),
            db_session=session
        )

        # THIẾT QUÂN LUẬT: Giới hạn phiên 2 giờ
        expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
        access_token = self.create_access_token(
            data={
                "id": u_id,
                "sub": u_email,
                "roles": roles_list,
                "perms": perms_list,
                "tenant_id": u_tenant,
                "name": u_name
            },
            expires_delta=timedelta(minutes=expire_minutes)
        )

        return TokenResponse(
            access_token=access_token,
            role=roles_list[0] if roles_list else "CUSTOMER",
            name=u_name,
            email=u_email
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
