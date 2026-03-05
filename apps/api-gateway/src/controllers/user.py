from litestar import Controller, get, patch, Request
from litestar.di import Provide
from typing import List, Dict, Union, Optional
from datetime import datetime, timezone
import logging

from src.database.repositories import UserRepository, RoleRepository, provide_user_repo, provide_role_repo
from src.database.models import User, Role, Permission
from src.guards import PermissionGuard
from src.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class UserController(Controller):
    path = "/api/v1/users"
    guards = [PermissionGuard("system:all")]
    dependencies = {
        "user_repo": Provide(provide_user_repo),
        "role_repo": Provide(provide_role_repo),
    }

    @get("/")
    async def list_users(
        self, user_repo: UserRepository,
        limit: int = 10, offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List users with server-side pagination. R60: password hash NEVER sent."""
        from sqlalchemy import select, func, and_, or_
        from sqlalchemy.orm import selectinload
        
        conditions = []
        if status and status != "ALL":
            conditions.append(User.status == status)
        if search:
            safe = escape_like(search)
            conditions.append(or_(
                User.email.ilike(f"%{safe}%"),
                User.name.ilike(f"%{safe}%"),
                User.username.ilike(f"%{safe}%"),
            ))

        where_clause = and_(*conditions) if conditions else True

        count_stmt = select(func.count(User.id)).where(where_clause)
        total = await user_repo.session.scalar(count_stmt) or 0

        stmt = select(User).where(where_clause).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).limit(limit).offset(offset)
        result = await user_repo.session.execute(stmt)
        users = result.scalars().all()
        
        data = [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name or u.username or "",
                "status": getattr(u, 'status', 'ACTIVE') or "ACTIVE",
                "createdAt": u.created_at.isoformat() if hasattr(u, 'created_at') and u.created_at else "",
                "roles": [
                    {
                        "id": str(r.id), "name": r.name, "code": r.code,
                        "permissions": [
                            {"id": str(p.id), "code": p.code, "name": p.name} 
                            for p in getattr(r, "permissions", [])
                        ]
                    }
                    for r in getattr(u, "roles", [])
                ],
            }
            for u in users
        ]
        return {"data": data, "total": total}

    @get("/roles")
    async def list_roles(self, role_repo: RoleRepository, limit: int = 100, offset: int = 0) -> List[Dict[str, object]]:
        """List all available roles. R22: paginated. R41: selectinload."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Get all perms for numeric ID mapping (UI compatibility)
        perm_stmt = select(Permission).order_by(Permission.code.asc())
        perm_res = await role_repo.session.execute(perm_stmt)
        all_perms = perm_res.scalars().all()
        perm_to_idx = {p.code: i+1 for i, p in enumerate(all_perms)}

        stmt = select(Role).limit(limit).offset(offset).options(
            selectinload(Role.permissions)
        ).order_by(Role.created_at.asc())
        
        result = await role_repo.session.execute(stmt)
        roles = result.scalars().all()
        
        return [
            {
                "id": str(r.id), "name": r.name, "code": r.code,
                "description": r.description,
                "tenant_id": getattr(r, "tenant_id", "smartshop"),
                "permissions": [
                    {
                        "id": perm_to_idx.get(p.code, 0), 
                        "code": p.code, 
                        "name": p.name,
                        "description": p.description
                    } 
                    for p in sorted(getattr(r, "permissions", []), key=lambda x: x.code)
                ],
            }
            for r in roles
        ]

    @get("/permissions")
    async def list_permissions(self, role_repo: RoleRepository, limit: int = 200, offset: int = 0) -> List[Dict[str, object]]:
        """List all available system permissions."""
        from sqlalchemy import select
        stmt = select(Permission).order_by(Permission.code.asc()).limit(limit).offset(offset)
        result = await role_repo.session.execute(stmt)
        perms = result.scalars().all()
        
        # Get global list to ensure IDs match indices reliably across pagination (if limited)
        global_stmt = select(Permission).order_by(Permission.code.asc())
        global_res = await role_repo.session.execute(global_stmt)
        global_perms = global_res.scalars().all()
        perm_to_idx = {p.code: i+1 for i, p in enumerate(global_perms)}

        return [
            {
                "id": perm_to_idx.get(p.code, 0), 
                "code": p.code, 
                "name": p.name,
                "description": p.description
            }
            for p in perms
        ]

    @patch("/{user_id:str}/roles")
    async def update_user_roles(self, user_repo: UserRepository, role_repo: RoleRepository, user_id: str, data: List[str]) -> Dict[str, object]:
        """Update roles for a specific user."""
        # Find roles by code
        roles = await role_repo.list(code={"in": data})
        
        # Load user with roles (Rule R41)
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await user_repo.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
             from litestar.exceptions import NotFoundException
             raise NotFoundException(f"User {user_id} not found")
        
        # Update roles relationship
        user.roles = list(roles)
        await user_repo.session.commit()
        
        return {
            "id": str(user.id), "email": user.email, "name": user.name, 
            "status": getattr(user, "status", "ACTIVE"),
            "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else "",
            "roles": [
                {
                    "id": str(r.id), "name": r.name, "code": r.code,
                    "permissions": [
                        {"id": str(p.id), "code": p.code, "name": p.name} 
                        for p in getattr(r, "permissions", [])
                    ]
                }
                for r in getattr(user, "roles", [])
            ],
        }

    @patch("/{user_id:str}")
    async def update_user(self, user_repo: UserRepository, user_id: str, data: Dict[str, object]) -> Dict[str, object]:
        """Update a user's status or name."""
        user = await user_repo.get(user_id)
        
        if "name" in data:
            user.name = data["name"]
        if "status" in data:
            user.status = data["status"]
            
        await user_repo.session.commit()
        return {
            "id": str(user.id), "email": user.email, "name": user.name, 
            "status": getattr(user, "status", "ACTIVE"),
        }

    @patch("/{user_id:str}/delete")
    async def delete_user(self, user_repo: UserRepository, user_id: str) -> Dict[str, object]:
        """Soft delete a user by locking their status and logging deletion time."""
        user = await user_repo.get(user_id)
        
        user.deleted_at = datetime.now(timezone.utc)
        user.status = "LOCKED"
        
        await user_repo.session.commit()
        return {
            "id": str(user.id), "email": user.email, "name": user.name, 
            "status": getattr(user, "status", "LOCKED"),
            "deleted": True
        }

    @patch("/{role_id:str}/permissions")
    async def update_role_permissions(self, role_repo: RoleRepository, role_id: str, data: List[str]) -> Dict[str, object]:
        """Update permissions for a specific role (Rule R36)."""
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload
        
        # 1. Load role with permissions (Robust lookup by ID or Code)
        stmt = select(Role).where(
            or_(Role.id == role_id, Role.code == role_id)
        ).options(selectinload(Role.permissions))
        
        result = await role_repo.session.execute(stmt)
        role = result.scalar_one_or_none()
        
        if not role:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Role {role_id} not found")
        
        # 2. Find permissions by code or ID (Robust mapping)
        logger.debug(f"[Permissions Update] Role: {role.code}, Requested: {data}")
        
        # UI-Mapping Support: If the frontend sends numeric strings like "1", "2", "3"
        # We try to map them to the corresponding permission in the alphabetical list
        mapped_data = list(data)
        if all(d.isdigit() for d in data):
            all_perms_stmt = select(Permission).order_by(Permission.code.asc())
            all_perms_res = await role_repo.session.execute(all_perms_stmt)
            all_perms = all_perms_res.scalars().all()
            
            numeric_mapping = {str(i+1): p.code for i, p in enumerate(all_perms)}
            mapped_data = [numeric_mapping.get(d, d) for d in data]
            logger.debug(f"[Permissions Update] Numeric detected. Mapped {data} -> {mapped_data}")

        perm_stmt = select(Permission).where(
            or_(Permission.code.in_(mapped_data), Permission.id.in_(mapped_data))
        )
        perm_result = await role_repo.session.execute(perm_stmt)
        permissions = perm_result.scalars().all()
        logger.debug(f"[Permissions Update] Found {len(permissions)} permissions in DB")
        
        # 3. Update relationship
        role.permissions = list(permissions)
        
        # 4. Extract data for response BEFORE commit to avoid lazy-loading crashes
        res_id = str(role.id)
        res_name = role.name
        res_code = role.code
        res_desc = role.description
        res_tenant = getattr(role, "tenant_id", "smartshop")
        
        # Sort permissions by code to match list_permissions (Elite Sync)
        # We also need a mapping for numeric IDs in the response
        all_perms_stmt = select(Permission).order_by(Permission.code.asc())
        all_perms_res = await role_repo.session.execute(all_perms_stmt)
        all_perms = all_perms_res.scalars().all()
        perm_to_idx = {p.code: i+1 for i, p in enumerate(all_perms)}

        sorted_permissions = sorted(permissions, key=lambda x: x.code)
        res_perms = [
            {
                "id": perm_to_idx.get(p.code, 0), 
                "code": p.code, 
                "name": p.name,
                "description": p.description
            }
            for p in sorted_permissions
        ]
        
        await role_repo.session.commit()
        logger.debug(f"[Permissions Update] Status: SUCCESS, Role: {res_code}")
        
        return {
            "ok": True,
            "id": res_id,
            "name": res_name,
            "code": res_code,
            "description": res_desc,
            "tenant_id": res_tenant,
            "permissions": res_perms
        }
