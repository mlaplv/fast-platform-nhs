from __future__ import annotations
from litestar import Controller, get, patch, post, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Optional
import logging

from backend.database.models import User
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.user import UserResponse, UserListResponse, RoleResponse, PermissionResponse, UserUpdatePayload, UserCreatePayload, LoyaltyResponse, PointAdjustmentRequest
from backend.schemas.common import SuccessResponse
from backend.services.user_service import user_service
from backend.core.martial_law import martial_law_manager
from litestar.exceptions import ClientException, PermissionDeniedException

logger = logging.getLogger("api-gateway")

class UserController(Controller):
    path = "/api/v1/users"
    guards = [PermissionGuard(PermissionEnum.USER_MANAGE)]

    @get("/", guards=[PermissionGuard(PermissionEnum.USER_MANAGE)])
    async def list_users(
        self, db_session: "AsyncSession",
        limit: int = 10, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> UserListResponse:
        """List users (R76: Scalar Projection). R60: password hash NEVER sent."""
        return await user_service.list_users(db_session, limit, offset, status, search)

    @get("/roles")
    async def list_roles(self, db_session: "AsyncSession", limit: int = 100, offset: int = 0) -> List[RoleResponse]:
        """List all available roles. R22: paginated. R41: selectinload."""
        return await user_service.list_roles(db_session, limit, offset)

    @get("/permissions")
    async def list_permissions(self, db_session: "AsyncSession", limit: int = 200, offset: int = 0) -> List[PermissionResponse]:
        """List all available system permissions."""
        return await user_service.list_permissions(db_session, limit, offset)

    @patch("/{user_id:str}/roles")
    async def update_user_roles(self, request: Request, db_session: "AsyncSession", user_id: str, data: List[str]) -> SuccessResponse:
        """Update roles for a specific user (Surgical Update)."""
        user_state = getattr(request.state, "user", {})
        actor_id = user_state.get("sub", "SYSTEM")
        is_super = "SUPER_ADMIN" in user_state.get("roles", [])

        # [THIẾT QUÂN LUẬT] Chặn và chuyển sang Draft
        intercepted = await martial_law_manager.intercept_critical_action(
            db_session, actor_id, "UPDATE_ROLES", "users", user_id, {"roles": data}, is_super
        )
        
        if intercepted:
            await db_session.commit()
            return SuccessResponse(message="Yêu cầu thay đổi quyền đã được gửi vào hàng chờ Phê duyệt (Draft).")

        res = await user_service.update_roles(db_session, user_id, data)
        await db_session.commit()
        return res

    @patch("/{user_id:str}")
    async def update_user(self, db_session: "AsyncSession", user_id: str, data: UserUpdatePayload) -> UserResponse:
        """Update a user's status or name (Elite V2.2: Fixed Serialization)."""
        try:
            user = await user_service.update_user(db_session, user_id, data.model_dump(exclude_unset=True))
            # R60: Validate BEFORE commit to ensure all relationship data is captured while session is active
            response = UserResponse.model_validate(user)
            await db_session.commit()
            return response
        except IntegrityError:
            await db_session.rollback()
            raise ClientException(status_code=400, detail="Data integrity violation. Email or username might already exist.")

    @post("/", guards=[PermissionGuard(PermissionEnum.USER_MANAGE)])
    async def create_user(self, db_session: "AsyncSession", data: UserCreatePayload) -> UserResponse:
        """Create a new user identity (Elite V2.2: Fixed Serialization)."""
        try:
            user = await user_service.create_user(db_session, data.model_dump(exclude_unset=True))
            await db_session.commit()
            return UserResponse.model_validate(user)
        except IntegrityError:
            await db_session.rollback()
            raise ClientException(status_code=400, detail="Identity creation failed due to unique constraint violation.")

    @patch("/{user_id:str}/delete")
    async def delete_user(self, request: Request, db_session: "AsyncSession", user_id: str) -> SuccessResponse:
        """Soft delete a user."""
        user_state = getattr(request.state, "user", {})
        actor_id = user_state.get("sub", "SYSTEM")
        is_super = "SUPER_ADMIN" in user_state.get("roles", [])

        # [THIẾT QUÂN LUẬT] Chặn và chuyển sang Draft
        intercepted = await martial_law_manager.intercept_critical_action(
            db_session, actor_id, "DELETE", "users", user_id, {}, is_super
        )
        
        if intercepted:
            await db_session.commit()
            return SuccessResponse(message="Yêu cầu xóa tài khoản đã được gửi vào hàng chờ Phê duyệt (Draft).")

        res = await user_service.delete_user(db_session, user_id)
        await db_session.commit()
        return res

    @patch("/{role_id:str}/permissions")
    async def update_role_permissions(self, db_session: "AsyncSession", role_id: str, data: List[str]) -> SuccessResponse:
        """Update permissions for a specific role (R36)."""
        res = await user_service.update_role_permissions(db_session, role_id, data)
        await db_session.commit()
        return res

    @get("/{user_id:str}/loyalty", guards=[PermissionGuard(PermissionEnum.USER_MANAGE)])
    async def get_user_loyalty(self, db_session: "AsyncSession", user_id: str) -> LoyaltyResponse:
        """Fetch user loyalty summary for admin."""
        return await user_service.get_user_loyalty(db_session, user_id)

    @post("/{user_id:str}/loyalty/adjust", guards=[PermissionGuard(PermissionEnum.USER_MANAGE)])
    async def adjust_user_points(self, db_session: "AsyncSession", user_id: str, data: PointAdjustmentRequest) -> SuccessResponse:
        """Manually adjust user points (Admin)."""
        res = await user_service.adjust_points(db_session, user_id, data)
        await db_session.commit()
        return res

    @post("/{user_id:str}/logout-all")
    async def force_logout_user(self, request: Request, db_session: "AsyncSession", user_id: str) -> SuccessResponse:
        """Force logout all devices for a user by rotating security stamp."""
        user_state = getattr(request.state, "user", {})
        actor_id = user_state.get("sub", "SYSTEM")
        is_super = "SUPER_ADMIN" in user_state.get("roles", [])

        # [THIẾT QUÂN LUẬT] Chặn và chuyển sang Draft nếu không phải Super Admin
        intercepted = await martial_law_manager.intercept_critical_action(
            db_session, actor_id, "FORCE_LOGOUT", "users", user_id, {}, is_super
        )
        
        if intercepted:
            await db_session.commit()
            return SuccessResponse(message="Yêu cầu cưỡng bức đăng xuất đã được gửi vào hàng chờ Phê duyệt.")

        # Rotate Stamp
        import uuid
        import sqlalchemy as sa
        stmt = sa.update(User).where(User.id == user_id).values(security_stamp=str(uuid.uuid4()))
        await db_session.execute(stmt)
        await db_session.commit()
        
        return SuccessResponse(message=f"Đã thu hồi toàn bộ phiên làm việc của user {user_id}")
