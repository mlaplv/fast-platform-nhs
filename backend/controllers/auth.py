import bcrypt
import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from litestar import Controller, post, Request
from litestar.exceptions import NotAuthorizedException, ClientException
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.stores.memory import MemoryStore
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload
from sqlalchemy import select
from backend.database.models import Notification, User, Role
from backend.schemas.auth import LoginRequest, TokenResponse, RegisterRequest

SECRET_KEY = os.environ["ENCRYPTION_SALT"]  # MUST be set — crash on start if missing (CTO Audit V2 C2)
ALGORITHM = "HS256"

auth_limit_value = int(os.getenv("RATE_LIMIT_AUTH_MINUTE", "5"))
auth_rate_limit = RateLimitConfig(rate_limit=("minute", auth_limit_value), store="memory_store")


class AuthController(Controller):
    path = "/api/v1/auth"

    @post("/register", middleware=[auth_rate_limit.middleware])
    async def register(self, db_session: AsyncSession, data: RegisterRequest) -> Dict[str, str]:
        import uuid
        import bcrypt
        
        # Check if email exists
        stmt = select(User).where(User.email == data.email)
        res = await db_session.execute(stmt)
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
        db_session.add(new_user)
        # Flush to get the user inserted before adding notification
        await db_session.flush()

        new_notif = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="SYSTEM",
            message=f"Chào mừng {data.name} gia nhập hệ thống"
        )
        db_session.add(new_notif)

        return {"id": user_id, "message": "Tạo tài khoản thành công"}

    @post("/login", middleware=[auth_rate_limit.middleware])
    async def login(self, db_session: AsyncSession, data: LoginRequest) -> TokenResponse:
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
        # Assuming relationship "roles" exists in User model
        roles = [r.code for r in getattr(user, "roles", [])]
        permissions = []
        if hasattr(user, "roles"):
            for r in user.roles:
                if hasattr(r, "permissions"):
                    permissions.extend([p.code for p in r.permissions])
        permissions = list(set(permissions))

        # Login notification (Audit Log)
        import uuid
        new_notif = Notification(
            id=str(uuid.uuid4()),
            user_id=user.id,
            type="SECURITY",
            message=f"Identity Verified: Session established for {user.email}"
        )
        db_session.add(new_notif)
        # NOTE: Do NOT call db_session.commit() — Litestar auto-commits at end of request

        # THIẾT QUÂN LUẬT: Giới hạn phiên 2 giờ
        expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
        access_token = self._create_access_token(
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

    def _create_access_token(self, data: Dict[str, object], expires_delta: timedelta) -> str:
        to_encode = data.copy()
        try:
             expire = datetime.now(timezone.utc) + expires_delta
        except Exception:
             expire = datetime.now(timezone.utc) + timedelta(hours=2)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def get_current_user_role(request: Request) -> str:
        """R41: Performance optimization - use the state already resolved by AuthMiddleware."""
        user = getattr(request.state, "user", None)
        if not user:
            return "GUEST"
            
        roles = user.get("roles", [])
        return roles[0] if isinstance(roles, list) and roles else "GUEST"
