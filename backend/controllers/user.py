from litestar import Controller, get, patch, Request
from typing import List, Dict, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.user_service import user_service
from backend.guards import PermissionGuard

logger = logging.getLogger("api-gateway")

class UserController(Controller):
    path = "/api/v1/users"
    guards = [PermissionGuard("system:all")]

    @get("/", guards=[PermissionGuard("system:all")])
    async def list_users(
        self, db_session: AsyncSession,
        limit: int = 10, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List users via UserService."""
        return await user_service.list_users(
            session=db_session,
            limit=limit,
            offset=offset,
            status=status,
            search=search
        )

    @get("/roles")
    async def list_roles(self, db_session: AsyncSession, limit: int = 100, offset: int = 0) -> List[Dict[str, object]]:
        """List all available roles via UserService."""
        return await user_service.list_roles(db_session, limit, offset)

    @get("/permissions")
    async def list_permissions(self, db_session: AsyncSession, limit: int = 200, offset: int = 0) -> List[Dict[str, object]]:
        """List all available system permissions via UserService."""
        return await user_service.list_permissions(db_session, limit, offset)

    @patch("/{user_id:str}/roles")
    async def update_user_roles(self, db_session: AsyncSession, user_id: str, data: List[str]) -> Dict[str, object]:
        """Update roles for a specific user via UserService."""
        return await user_service.update_user_roles(db_session, user_id, data)

    @patch("/{user_id:str}")
    async def update_user(self, db_session: AsyncSession, user_id: str, data: Dict[str, object]) -> Dict[str, object]:
        """Update a user's status or name via UserService."""
        return await user_service.update_user(db_session, user_id, data)

    @patch("/{user_id:str}/delete")
    async def delete_user(self, db_session: AsyncSession, user_id: str) -> Dict[str, object]:
        """Soft delete a user via UserService."""
        return await user_service.delete_user(db_session, user_id)

    @patch("/{role_id:str}/permissions")
    async def update_role_permissions(self, db_session: AsyncSession, role_id: str, data: List[str]) -> Dict[str, object]:
        """Update permissions for a specific role via UserService."""
        return await user_service.update_role_permissions(db_session, role_id, data)
