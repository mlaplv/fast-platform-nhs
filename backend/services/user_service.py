import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, Tuple, cast
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import User, Role, Permission
from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class UserService:
    """
    ULTRA-LEAN USER SERVICE (ELITE V2.2)
    ------------------------------------
    Handles User, Role, and Permission management.
    """

    async def list_users(
        self,
        session: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List users with total count and nested role/permission mapping."""
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

        # 1. COUNT (Zero-Hydration)
        count_stmt = select(func.count(User.id)).where(where_clause)
        total = await session.scalar(count_stmt) or 0

        # 2. Scalar Projection Fetch with manual nesting
        stmt = (
            select(
                User.id, User.email, User.name, User.status, User.created_at,
                Role.id.label("role_id"), Role.name.label("role_name"), Role.code.label("role_code"),
                Permission.id.label("perm_id"), Permission.code.label("perm_code"), Permission.name.label("perm_name")
            )
            .outerjoin(User.roles)
            .outerjoin(Role.permissions)
            .where(where_clause)
            .limit(limit).offset(offset)
        )

        result = await session.execute(stmt)

        users_map: Dict[str, Dict[str, object]] = {}
        for row in result:
            u_id = str(row.id)
            if u_id not in users_map:
                users_map[u_id] = {
                    "id": u_id,
                    "email": row.email,
                    "name": row.name or "Unknown",
                    "status": row.status or "ACTIVE",
                    "createdAt": row.created_at.isoformat() if row.created_at else "",
                    "roles": {}
                }

            if row.role_id:
                r_id = str(row.role_id)
                roles_dict = cast(Dict[str, Dict[str, object]], users_map[u_id]["roles"])
                if r_id not in roles_dict:
                    roles_dict[r_id] = {
                        "id": r_id, "name": row.role_name, "code": row.role_code,
                        "permissions": {}
                    }

                if row.perm_id:
                    p_id = str(row.perm_id)
                    perms_dict = cast(Dict[str, Dict[str, object]], roles_dict[r_id]["permissions"])
                    perms_dict[p_id] = {
                        "id": p_id, "code": row.perm_code, "name": row.perm_name
                    }

        data = []
        for u in users_map.values():
            u_roles = []
            roles_dict = cast(Dict[str, Dict[str, object]], u["roles"])
            for r in roles_dict.values():
                perms_dict = cast(Dict[str, Dict[str, object]], r["permissions"])
                r["permissions"] = list(perms_dict.values())
                u_roles.append(r)
            u["roles"] = u_roles
            data.append(u)

        return {"data": data, "total": total}

    async def list_roles(
        self,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, object]]:
        """List roles with mapped permission indices for UI."""
        # Get all perms for numeric ID mapping
        perm_stmt = select(Permission).order_by(Permission.code.asc())
        perm_res = await session.execute(perm_stmt)
        all_perms = perm_res.scalars().all()
        perm_to_idx = {p.code: i+1 for i, p in enumerate(all_perms)}

        stmt = select(Role).limit(limit).offset(offset).options(
            selectinload(Role.permissions)
        ).order_by(Role.created_at.asc())

        result = await session.execute(stmt)
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

    async def list_permissions(
        self,
        session: AsyncSession,
        limit: int = 200,
        offset: int = 0
    ) -> List[Dict[str, object]]:
        """List all system permissions."""
        stmt = select(Permission).order_by(Permission.code.asc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        perms = result.scalars().all()

        global_stmt = select(Permission).order_by(Permission.code.asc())
        global_res = await session.execute(global_stmt)
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

    async def update_user_roles(self, session: AsyncSession, user_id: str, role_codes: List[str]) -> Dict[str, object]:
        """Update roles for a user by role codes and return mapped result."""
        role_stmt = select(Role).where(Role.code.in_(role_codes)).options(selectinload(Role.permissions))
        role_res = await session.execute(role_stmt)
        roles = role_res.scalars().all()

        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles).selectinload(Role.permissions))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"User {user_id} not found")

        user.roles = list(roles)
        await session.commit()

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

    async def update_user(self, session: AsyncSession, user_id: str, data: Dict[str, object]) -> Dict[str, object]:
        """Update basic user info and return mapped result."""
        user = await session.get(User, user_id)
        if not user:
             from litestar.exceptions import NotFoundException
             raise NotFoundException(f"User {user_id} not found")

        if "name" in data: user.name = cast(str, data["name"])
        if "status" in data: user.status = cast(str, data["status"])

        await session.commit()
        return {
            "id": str(user.id), "email": user.email, "name": user.name,
            "status": getattr(user, "status", "ACTIVE"),
        }

    async def delete_user(self, session: AsyncSession, user_id: str) -> Dict[str, object]:
        """Soft delete (lock) a user and return mapped result."""
        user = await session.get(User, user_id)
        if not user:
             from litestar.exceptions import NotFoundException
             raise NotFoundException(f"User {user_id} not found")

        user.deleted_at = datetime.now(timezone.utc)
        user.status = "LOCKED"

        await session.commit()
        return {
            "id": str(user.id), "email": user.email, "name": user.name,
            "status": getattr(user, "status", "LOCKED"),
            "deleted": True
        }

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """Fetch a single user by email."""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_with_profile(self, session: AsyncSession, email: str) -> Optional[User]:
        """Fetch user with voice profile (N+1 Optimized)"""
        stmt = select(User).where(User.email == email).options(selectinload(User.voice_profile))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_role_permissions(self, session: AsyncSession, role_id: str, permission_ids: List[str]) -> Dict[str, object]:
        """Update permissions for a role and return mapped result."""
        stmt = select(Role).where(
            or_(Role.id == role_id, Role.code == role_id)
        ).options(selectinload(Role.permissions))

        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Role {role_id} not found")

        mapped_data = list(permission_ids)
        if all(d.isdigit() for d in permission_ids):
            all_perms_stmt = select(Permission).order_by(Permission.code.asc())
            all_perms_res = await session.execute(all_perms_stmt)
            all_perms = all_perms_res.scalars().all()

            numeric_mapping = {str(i+1): p.code for i, p in enumerate(all_perms)}
            mapped_data = [numeric_mapping.get(d, d) for d in permission_ids]

        perm_stmt = select(Permission).where(
            or_(Permission.code.in_(mapped_data), Permission.id.in_(mapped_data))
        )
        perm_result = await session.execute(perm_stmt)
        permissions = perm_result.scalars().all()

        role.permissions = list(permissions)
        await session.commit()

        # Scalar projection for UI mapping
        all_perms_stmt = select(Permission).order_by(Permission.code.asc())
        all_perms_res = await session.execute(all_perms_stmt)
        global_perms = all_perms_res.scalars().all()
        perm_to_idx = {p.code: i+1 for i, p in enumerate(global_perms)}

        return {
            "ok": True,
            "id": str(role.id),
            "name": role.name,
            "code": role.code,
            "description": role.description,
            "tenant_id": getattr(role, "tenant_id", "smartshop"),
            "permissions": [
                {
                    "id": perm_to_idx.get(p.code, 0),
                    "code": p.code,
                    "name": p.name,
                    "description": p.description
                }
                for p in sorted(getattr(role, "permissions", []), key=lambda x: x.code)
            ]
        }

# Global Instance
user_service = UserService()
