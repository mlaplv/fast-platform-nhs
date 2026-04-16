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

from backend.database.models import User, Role, SystemOTP
from backend.schemas.auth import (
    LoginRequest, TokenResponse, RegisterRequest,
    SocialLoginResponse, OTPRequestResponse, OTPVerifyResponse
)
from backend.schemas.common import SuccessResponse
from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.signal_center import signal_center

logger = logging.getLogger("api-gateway")

SECRET_KEY = os.environ.get("ENCRYPTION_SALT", "Micsmo_Elite_Standard_Salt_2026") # R00: Consistent SSOT Key
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

        # THIẾT QUÂN LUẬT: Phân tách thời lượng phiên bản (Duy trì cảnh giới)
        if data.remember_me:
            expire_minutes = 7 * 24 * 60  # 7 Days (10080 mins)
            logger.info(f"[AuthService] Long-term surveillance established for {user.email} (7 days).")
        else:
            expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

        token_data = {
            "id": str(user.id),
            "sub": user.email,
            "roles": roles,
            "perms": permissions,
            "tenant_id": getattr(user, 'tenant_id', 'default'),
            "stamp": getattr(user, "security_stamp", "MISSING"),
            "name": user.name,
            "hpw": user.password is not None,
            "rem": data.remember_me  # Mark for potential downstream logic
        }

        access_token = AuthService.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=expire_minutes)
        )

        return TokenResponse(
            id=str(user.id),
            access_token=access_token,
            role=roles[0] if roles else "CUSTOMER",
            name=user.name,
            email=user.email,
            has_password=user.password is not None
        )

    @staticmethod
    async def handle_social_user(db_session: AsyncSession, profile: Dict[str, str]) -> str:
        """Thực thi luồng Login DB chuẩn hóa cho Social Oauth2 (Tạo hoặc Tìm User và trả về JWT)"""
        email = profile.get("email", "").strip().lower()
        name = profile.get("name", "Social User")
        avatar = profile.get("avatar", "")
        # Nếu provider không cấp email (như Zalo), ta sinh email ảo
        if not email:
            email = f"user_{uuid.uuid4().hex[:8]}@social.smartshop.test"
            
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == email)
        )
        res = await db_session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user:
            user_id = str(uuid.uuid4())
            user_kwargs = {
                "id": user_id,
                "username": email,
                "email": email,
                "name": name,
                "status": "ACTIVE",
                "tenant_id": "default"
            }
            if hasattr(User, "avatar_url"):
                user_kwargs["avatar_url"] = avatar
            elif hasattr(User, "avatar"):
                user_kwargs["avatar"] = avatar
                
            user = User(**user_kwargs)
            db_session.add(user)
            await db_session.flush()
            roles = ["CUSTOMER"]
            permissions = []
            logger.info(f"[AuthService] Mới tạo tài khoản Oauth2 cho {email}")
        else:
            roles = [r.code for r in getattr(user, "roles", [])]
            permissions = []
            for r in getattr(user, "roles", []):
                permissions.extend([p.code for p in getattr(r, "permissions", [])])
                
        if not roles:
            roles = ["CUSTOMER"]
            
        token_data = {
            "id": str(user.id),
            "sub": user.email,
            "roles": roles,
            "perms": list(set(permissions)),
            "tenant_id": getattr(user, 'tenant_id', 'default'),
            "stamp": getattr(user, "security_stamp", "MISSING"),
            "name": user.name,
            "hpw": user.password is not None
        }

        # Lưu ý: Token Social Login giới hạn duy trì 120 phút mặc định (giống OTP)
        return AuthService.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=120)
        )

    @staticmethod
    async def request_otp(db_session: AsyncSession, data: Dict[str, object]) -> OTPRequestResponse:
        """PUBLIC: Request OTP login via Phone or Email (Elite V2.2)."""
        import secrets
        from datetime import datetime, timedelta, timezone

        identifier = str(data.get("email") or data.get("phone"))
        if not identifier:
            raise ClientException(status_code=400, detail="Identifier (email/phone) is required")

        # 1. Generate 6-digit code (Elite V2.2: Cryptographically secure via secrets)
        code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        otp_token = str(uuid.uuid4())
        
        # 2. Store in DB
        new_otp = SystemOTP(
            id=str(uuid.uuid4()),
            identifier=identifier,
            code=code,
            token=otp_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            tenant_id="default"
        )
        db_session.add(new_otp)
        
        # 3. Real Delivery: Enqueue background job (Elite V2.2)
        request_id = str(uuid.uuid4())
        try:
            from backend.infra.arq_config import get_redis_settings
            from arq import create_pool
            
            redis_pool = await create_pool(get_redis_settings())
            await redis_pool.enqueue_job("send_otp_email", identifier, code, request_id, _queue_name="default")
            logger.info(f"📧 [AuthService] OTP task enqueued for {identifier} (ID: {request_id})")
        except Exception as e:
            logger.error(f"❌ [AuthService] Failed to enqueue OTP task: {e}")
            # Fallback for dev: still log the code so Sếp can test if Redis is down
            logger.warning(f"⚠️ Simulation Fallback: OTP for {identifier} is {code}")

        return OTPRequestResponse(
            status="success",
            message=f"Mã OTP đã được gửi đến {identifier}.",
            otp_token=otp_token,
            request_id=request_id  # Added for Live Tracking
        )

    @staticmethod
    async def verify_otp(db_session: AsyncSession, data: Dict[str, object]) -> OTPVerifyResponse:
        """PUBLIC: Verify OTP code and generate real token. Auto-register if user doesn't exist."""
        from datetime import datetime, timezone
        
        # Elite V2.2: Hardened normalization
        identifier = str(data.get("email") or data.get("phone") or "").strip().lower()
        code = str(data.get("code") or "").strip()
        otp_token = str(data.get("otp_token") or "").strip()

        if not identifier or not code or not otp_token:
            logger.warning(f"⚠️ [AuthService] Missing verification metadata: id={identifier}, code={'***' if code else 'MISSING'}, token={'PRESENT' if otp_token else 'MISSING'}")
            raise NotAuthorizedException("Thiếu thông tin xác thực")

        # 1. Validate OTP with detailed logging
        stmt = select(SystemOTP).where(
            SystemOTP.identifier == identifier,
            SystemOTP.token == otp_token,
            SystemOTP.used_at.is_(None)
        )
        res = await db_session.execute(stmt)
        otp_record = res.scalar_one_or_none()

        if not otp_record:
            logger.error(f"❌ [AuthService] Verification Failed: No active OTP record found for identifier {identifier} and token {otp_token[:8]}...")
            raise NotAuthorizedException("Mã OTP không hợp lệ hoặc đã được sử dụng")

        if otp_record.code != code:
            logger.error(f"❌ [AuthService] Verification Failed: Code mismatch for {identifier}. Expected {otp_record.code}, received {code}")
            raise NotAuthorizedException("Mã OTP không chính xác")

        if not otp_record.is_valid:
            logger.error(f"❌ [AuthService] Verification Failed: OTP expired for {identifier}. Expired at: {otp_record.expires_at}")
            raise NotAuthorizedException("Mã OTP đã hết hạn")

        # 2. Mark OTP as used
        otp_record.used_at = datetime.now(timezone.utc)

        # 3. Find or Create User (Quick Register)
        stmt_user = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where((User.email == identifier) | (User.phone == identifier))
        )
        res_user = await db_session.execute(stmt_user)
        user = res_user.scalar_one_or_none()
        
        roles = []

        if not user:
            # Create a basic user
            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                username=identifier,
                email=identifier if "@" in identifier else f"{identifier}@smartshop.test",
                phone=identifier if "@" not in identifier else None,
                name=str(data.get("name") or identifier.split("@")[0]),
                status="ACTIVE",
                tenant_id = "default"
            )
            db_session.add(user)
            await db_session.flush()
            roles = ["CUSTOMER"]
            permissions = []
            logger.info(f"[AuthService] New user auto-registered via OTP: {identifier}")
        else:
            # 4. Generate real access token data from existing user
            roles = [r.code for r in getattr(user, "roles", [])]
            permissions = []
            for r in getattr(user, "roles", []):
                permissions.extend([p.code for p in getattr(r, "permissions", [])])
        
        if not roles:
            roles = ["CUSTOMER"]
            
        token_data = {
            "id": str(user.id),
            "sub": user.email,
            "roles": roles,
            "perms": list(set(permissions if 'permissions' in locals() else [])),
            "tenant_id": getattr(user, 'tenant_id', 'default'),
            "stamp": getattr(user, "security_stamp", "MISSING"),
            "name": user.name,
            "hpw": user.password is not None
        }

        access_token = AuthService.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=120)
        )

        return OTPVerifyResponse(
            status="success",
            id=str(user.id),
            access_token=access_token,
            role=roles[0],
            has_password=user.password is not None
        )

    @staticmethod
    def create_access_token(data: Dict[str, object], expires_delta: timedelta) -> str:
        """Generate JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

auth_service = AuthService()
