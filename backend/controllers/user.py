from __future__ import annotations
from litestar import Controller, get, patch, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
import logging

from backend.database.models import User
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.user import UserResponse, UserListResponse, RoleResponse, PermissionResponse, UserUpdatePayload
from backend.schemas.common import SuccessResponse
from backend.services.user_service import user_service

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
    async def update_user_roles(self, db_session: "AsyncSession", user_id: str, data: List[str]) -> SuccessResponse:
        """Update roles for a specific user (Surgical Update)."""
        res = await user_service.update_roles(db_session, user_id, data)
        await db_session.commit()
        return res

    @patch("/{user_id:str}")
    async def update_user(self, db_session: "AsyncSession", user_id: str, data: UserUpdatePayload) -> SuccessResponse:
        """Update a user's status or name (Elite V2.2: Typed)."""
        res = await user_service.update_user(db_session, user_id, data.model_dump(exclude_unset=True))
        await db_session.commit()
        return res

    @patch("/{user_id:str}/delete")
    async def delete_user(self, db_session: "AsyncSession", user_id: str) -> SuccessResponse:
        """Soft delete a user."""
        res = await user_service.delete_user(db_session, user_id)
        await db_session.commit()
        return res

    @patch("/{role_id:str}/permissions")
    async def update_role_permissions(self, db_session: "AsyncSession", role_id: str, data: List[str]) -> SuccessResponse:
        """Update permissions for a specific role (R36)."""
        res = await user_service.update_role_permissions(db_session, role_id, data)
        await db_session.commit()
        return res
