import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, Tuple, cast
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.sql import escape_like

logger = logging.getLogger("api-gateway")

class UserService:
    """
    ULTRA-LEAN USER SERVICE (ELITE V2.2)
    ------------------------------------
    Handles User, Role, and Permission management.
    Zero-Hydration (Rule 1.5): Raw SQL & Scalar Projection for <2GB RAM.
    """

    async def list_users(
        self,
        session: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, object]:
        """List users with total count and nested role/permission mapping via text-SQL (Zero-Hydration)."""
        conditions = ["u.deleted_at IS NULL"]
        params = {"limit": limit, "offset": offset}

        if status and status != "ALL":
            conditions.append("u.status = :status")
            params["status"] = status
        if search:
            conditions.append("(u.email ILIKE :search OR u.name ILIKE :search OR u.username ILIKE :search)")
            params["search"] = f"%{escape_like(search)}%"

        where_clause = " AND ".join(conditions)

        # 1. COUNT (Zero-Hydration)
        count_sql = text(f"SELECT COUNT(*) FROM users u WHERE {where_clause}")
        total = await session.scalar(count_sql, params) or 0

        # 2. Scalar Projection Fetch
        sql = text(f"""
            SELECT
                u.id, u.email, u.name, u.status, u.created_at,
                r.id as role_id, r.name as role_name, r.code as role_code,
                p.id as perm_id, p.code as perm_code, p.name as perm_name
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE {where_clause}
            ORDER BY u.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await session.execute(sql, params)

        users_map: Dict[str, Dict[str, object]] = {}
        for row in result:
            u_id = str(row[0])
            if u_id not in users_map:
                users_map[u_id] = {
                    "id": u_id,
                    "email": row[1],
                    "name": row[2] or "Unknown",
                    "status": row[3] or "ACTIVE",
                    "createdAt": row[4].isoformat() if row[4] else "",
                    "roles": {}
                }

            if row[5]: # role_id
                r_id = str(row[5])
                roles_dict = cast(Dict[str, Dict[str, object]], users_map[u_id]["roles"])
                if r_id not in roles_dict:
                    roles_dict[r_id] = {
                        "id": r_id, "name": row[6], "code": row[7],
                        "permissions": {}
                    }

                if row[8]: # perm_id
                    p_id = str(row[8])
                    perms_dict = cast(Dict[str, Dict[str, object]], roles_dict[r_id]["permissions"])
                    perms_dict[p_id] = {
                        "id": p_id, "code": row[9], "name": row[10]
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
        """List roles with mapped permission indices for UI via text-SQL."""
        # Get all perms for numeric ID mapping
        perm_sql = text("SELECT code FROM permissions WHERE deleted_at IS NULL ORDER BY code ASC")
        perm_res = await session.execute(perm_sql)
        all_perm_codes = [r[0] for r in perm_res]
        perm_to_idx = {code: i+1 for i, code in enumerate(all_perm_codes)}

        sql = text("""
            SELECT r.id, r.name, r.code, r.description, r.tenant_id,
                   p.id as perm_id, p.code as perm_code, p.name as perm_name, p.description as perm_desc
            FROM roles r
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE r.deleted_at IS NULL
            ORDER BY r.created_at ASC
            LIMIT :limit OFFSET :offset
        """)

        res = await session.execute(sql, {"limit": limit, "offset": offset})

        roles_map: Dict[str, Dict[str, object]] = {}
        for r in res:
            rid = str(r[0])
            if rid not in roles_map:
                roles_map[rid] = {
                    "id": rid, "name": r[1], "code": r[2],
                    "description": r[3],
                    "tenant_id": r[4] or "smartshop",
                    "permissions": []
                }

            if r[5]: # perm_id
                roles_map[rid]["permissions"].append({
                    "id": perm_to_idx.get(r[6], 0),
                    "code": r[6],
                    "name": r[7],
                    "description": r[8]
                })

        return list(roles_map.values())

    async def list_permissions(
        self,
        session: AsyncSession,
        limit: int = 200,
        offset: int = 0
    ) -> List[Dict[str, object]]:
        """List all system permissions via text-SQL."""
        sql = text("SELECT code, name, description FROM permissions WHERE deleted_at IS NULL ORDER BY code ASC")
        res = await session.execute(sql)
        all_perms = res.all()

        perm_to_idx = {r[0]: i+1 for i, r in enumerate(all_perms)}

        # Paginate in memory since we already fetched all for index mapping (usually small set)
        paginated = all_perms[offset : offset + limit]

        return [
            {
                "id": perm_to_idx.get(p[0], 0),
                "code": p[0],
                "name": p[1],
                "description": p[2]
            }
            for p in paginated
        ]

    async def update_user_roles(self, session: AsyncSession, user_id: str, role_codes: List[str]) -> Dict[str, object]:
        """Update roles for a user via direct SQL (Zero-Hydration)."""
        # 1. Clear existing roles
        await session.execute(
            text("DELETE FROM user_roles WHERE user_id = :uid"),
            {"uid": user_id}
        )

        # 2. Add new roles
        if role_codes:
            role_ids_sql = text("SELECT id FROM roles WHERE code = ANY(:codes)")
            res = await session.execute(role_ids_sql, {"codes": role_codes})
            role_ids = [str(r[0]) for r in res]

            if role_ids:
                insert_sql = text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid)")
                for rid in role_ids:
                    await session.execute(insert_sql, {"uid": user_id, "rid": rid})

        await session.commit()

        # 3. Fetch full state via list_users logic (Zero-Hydration)
        params = {"uid": user_id}
        sql = text("""
            SELECT
                u.id, u.email, u.name, u.status, u.created_at,
                r.id as role_id, r.name as role_name, r.code as role_code,
                p.id as perm_id, p.code as perm_code, p.name as perm_name
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE u.id = :uid
        """)

        result = await session.execute(sql, params)
        rows = result.all()
        if not rows:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"User {user_id} not found")

        # Reuse mapping logic (simplified for single user)
        u = {
            "id": str(rows[0][0]),
            "email": rows[0][1],
            "name": rows[0][2] or "Unknown",
            "status": rows[0][3] or "ACTIVE",
            "createdAt": rows[0][4].isoformat() if rows[0][4] else "",
            "roles": {}
        }

        for row in rows:
            if row[5]: # role_id
                rid = str(row[5])
                roles_dict = cast(Dict[str, Dict[str, object]], u["roles"])
                if rid not in roles_dict:
                    roles_dict[rid] = {
                        "id": rid, "name": row[6], "code": row[7],
                        "permissions": {}
                    }
                if row[8]: # perm_id
                    pid = str(row[8])
                    perms_dict = cast(Dict[str, Dict[str, object]], roles_dict[rid]["permissions"])
                    perms_dict[pid] = {"id": pid, "code": row[9], "name": row[10]}

        final_roles = []
        for r in u["roles"].values():
            r["permissions"] = list(r["permissions"].values())
            final_roles.append(r)
        u["roles"] = final_roles

        return u

    async def update_user(self, session: AsyncSession, user_id: str, data: Dict[str, object]) -> Dict[str, object]:
        """Update basic user info via direct SQL and return mapped result (Zero-Hydration)."""
        set_clauses = []
        params = {"id": user_id}

        if "name" in data:
            set_clauses.append("name = :name")
            params["name"] = data["name"]
        if "status" in data:
            set_clauses.append("status = :status")
            params["status"] = data["status"]

        if not set_clauses:
            # Just fetch current
            sql = text("SELECT id, email, name, status FROM users WHERE id = :id")
            res = await session.execute(sql, {"id": user_id})
            r = res.first()
            if not r:
                from litestar.exceptions import NotFoundException
                raise NotFoundException(f"User {user_id} not found")
            return {"id": str(r[0]), "email": r[1], "name": r[2], "status": r[3]}

        set_clauses.append("updated_at = NOW()")
        sql = text(f"UPDATE users SET {', '.join(set_clauses)} WHERE id = :id RETURNING id, email, name, status")
        result = await session.execute(sql, params)
        r = result.first()

        if not r:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"User {user_id} not found")

        await session.commit()
        return {
            "id": str(r[0]), "email": r[1], "name": r[2],
            "status": r[3] or "ACTIVE",
        }

    async def delete_user(self, session: AsyncSession, user_id: str) -> Dict[str, object]:
        """Soft delete (lock) a user via direct SQL (Zero-Hydration)."""
        sql = text("""
            UPDATE users
            SET deleted_at = NOW(), status = 'LOCKED', updated_at = NOW()
            WHERE id = :id
            RETURNING id, email, name, status
        """)
        result = await session.execute(sql, {"id": user_id})
        r = result.first()

        if not r:
             from litestar.exceptions import NotFoundException
             raise NotFoundException(f"User {user_id} not found")

        await session.commit()
        return {
            "id": str(r[0]), "email": r[1], "name": r[2],
            "status": r[3] or "LOCKED",
            "deleted": True
        }

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[Dict[str, object]]:
        """Fetch a single user by email via Scalar Projection (Zero-Hydration)."""
        sql = text("SELECT id, email, username, name, status, tenant_id FROM users WHERE email = :email AND deleted_at IS NULL")
        res = await session.execute(sql, {"email": email})
        r = res.first()
        if not r:
            return None
        return {
            "id": str(r[0]),
            "email": r[1],
            "username": r[2],
            "name": r[3],
            "status": r[4],
            "tenant_id": r[5]
        }

    async def get_user_with_profile(self, session: AsyncSession, email: str) -> Optional[Dict[str, object]]:
        """Fetch user with voice profile via Scalar Projection (Zero-Hydration)."""
        sql = text("""
            SELECT u.id, u.email, u.name, u.status,
                   vp.id as profile_id, vp.provider, vp.voice_id, vp.settings
            FROM users u
            LEFT JOIN voice_profiles vp ON u.id = vp.user_id
            WHERE u.email = :email AND u.deleted_at IS NULL
        """)
        res = await session.execute(sql, {"email": email})
        r = res.first()
        if not r:
            return None

        return {
            "id": str(r[0]),
            "email": r[1],
            "name": r[2],
            "status": r[3],
            "voice_profile": {
                "id": str(r[4]) if r[4] else None,
                "provider": r[5],
                "voice_id": r[6],
                "settings": r[7] or {}
            } if r[4] else None
        }

    async def update_role_permissions(self, session: AsyncSession, role_id: str, permission_ids: List[str]) -> Dict[str, object]:
        """Update permissions for a role via direct SQL (Zero-Hydration)."""
        # Resolve role identity
        role_res = await session.execute(
            text("SELECT id, name, code, description, tenant_id FROM roles WHERE id = :id OR code = :id"),
            {"id": role_id}
        )
        r_row = role_res.first()
        if not r_row:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Role {role_id} not found")

        rid = str(r_row[0])

        # 1. Clear existing
        await session.execute(text("DELETE FROM role_permissions WHERE role_id = :rid"), {"rid": rid})

        # 2. Resolve permissions
        if permission_ids:
            # Handle numeric IDs if provided
            if all(d.isdigit() for d in permission_ids):
                all_perms_stmt = text("SELECT id, code FROM permissions ORDER BY code ASC")
                all_perms_res = await session.execute(all_perms_stmt)
                all_perms = all_perms_res.all()
                numeric_mapping = {str(i+1): p[1] for i, p in enumerate(all_perms)}
                resolved_ids = [numeric_mapping.get(d, d) for d in permission_ids]
            else:
                resolved_ids = permission_ids

            perm_res = await session.execute(
                text("SELECT id FROM permissions WHERE id = ANY(:ids) OR code = ANY(:ids)"),
                {"ids": resolved_ids}
            )
            p_ids = [str(p[0]) for p in perm_res]

            if p_ids:
                insert_sql = text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:rid, :pid)")
                for pid in p_ids:
                    await session.execute(insert_sql, {"rid": rid, "pid": pid})

        await session.commit()

        # 3. Return updated state via scalar projection
        perm_sql = text("SELECT code FROM permissions WHERE deleted_at IS NULL ORDER BY code ASC")
        perm_res = await session.execute(perm_sql)
        perm_to_idx = {row[0]: i+1 for i, row in enumerate(perm_res)}

        sql = text("""
            SELECT p.id, p.code, p.name, p.description
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = :rid
            ORDER BY p.code ASC
        """)
        res = await session.execute(sql, {"rid": rid})

        return {
            "ok": True,
            "id": rid, "name": r_row[1], "code": r_row[2], "description": r_row[3],
            "tenant_id": r_row[4] or "smartshop",
            "permissions": [
                {
                    "id": perm_to_idx.get(p[1], 0),
                    "code": p[1], "name": p[2], "description": p[3]
                }
                for p in res
            ]
        }

# Global Instance
user_service = UserService()
