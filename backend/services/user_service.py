import logging
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional, Tuple
from collections import defaultdict
import uuid

from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database.models import User, Role, Permission, Order
from backend.utils.sql import escape_like
from backend.schemas.user import UserResponse, UserListResponse, RoleResponse, PermissionResponse
from backend.schemas.common import SuccessResponse

logger = logging.getLogger("api-gateway")

class UserService:
    @staticmethod
    async def list_users(
        db_session: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> UserListResponse:
        """Moves logic from UserController.list_users. Uses Scalar Projection and N+1 optimized role fetching."""
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
        total = await db_session.scalar(count_stmt) or 0

        # 2. Scalar Projection Fetch
        stmt = (
            select(
                User.id, User.email, User.name, User.status, User.created_at
            )
            .where(where_clause)
            .limit(limit).offset(offset).order_by(User.created_at.desc())
        )

        result = await db_session.execute(stmt)
        user_rows = result.all()

        if not user_rows:
            return UserListResponse(data=[], total=total)

        # 3. N+1 KILL: Fetch roles for all listed users in one batch
        user_ids = [str(r.id) for r in user_rows]

        role_stmt = (
            select(User.id.label("user_id"), Role)
            .join(User.roles)
            .options(selectinload(Role.permissions))
            .where(User.id.in_(user_ids))
        )
        role_res = await db_session.execute(role_stmt)

        user_roles_map = defaultdict(list)
        for row in role_res:
            user_roles_map[str(row.user_id)].append(row.Role)

        # 4. Construct response data
        data = []
        for row in user_rows:
            user_dict = dict(row._mapping)
            user_dict["roles"] = user_roles_map.get(str(row.id), [])
            data.append(UserResponse.model_validate(user_dict))

        return UserListResponse(data=data, total=total)

    @staticmethod
    async def list_roles(db_session: AsyncSession, limit: int = 100, offset: int = 0) -> List[RoleResponse]:
        """Moves logic from UserController.list_roles."""
        perm_stmt = select(Permission).order_by(Permission.code.asc())
        perm_res = await db_session.execute(perm_stmt)
        all_perms = perm_res.scalars().all()
        perm_to_idx = {p.code: i+1 for i, p in enumerate(all_perms)}

        stmt = select(Role).limit(limit).offset(offset).options(
            selectinload(Role.permissions)
        ).order_by(Role.created_at.asc())

        result = await db_session.execute(stmt)
        roles = result.scalars().all()

        for r in roles:
            for p in getattr(r, "permissions", []):
                setattr(p, "ui_id", perm_to_idx.get(p.code, 0))

        return [RoleResponse.model_validate(r) for r in roles]

    @staticmethod
    async def list_permissions(db_session: AsyncSession, limit: int = 200, offset: int = 0) -> List[PermissionResponse]:
        """Moves logic from UserController.list_permissions."""
        stmt = select(Permission).order_by(Permission.code.asc()).limit(limit).offset(offset)
        result = await db_session.execute(stmt)
        perms = result.scalars().all()

        return [PermissionResponse.model_validate(p) for p in perms]

    @staticmethod
    async def update_roles(db_session: AsyncSession, user_id: str, role_codes: List[str]) -> SuccessResponse:
        """Moves logic from UserController.update_user_roles."""
        role_stmt = select(Role).where(Role.code.in_(role_codes))
        role_res = await db_session.execute(role_stmt)
        roles = role_res.scalars().all()

        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
             raise NotFoundException(f"User {user_id} not found")

        user.roles = list(roles)
        return SuccessResponse(ok=True, id=user_id, message="User roles updated")

    @staticmethod
    async def update_user(db_session: AsyncSession, user_id: str, data: Dict[str, object]) -> User:
        """Moves logic from UserController.update_user."""
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(f"User {user_id} not found")

        if "name" in data:
            user.name = str(data["name"])
        if "status" in data:
            user.status = str(data["status"])
        if "gender" in data:
            user.gender = str(data["gender"])
        if "dob" in data:
            user.dob = datetime.fromisoformat(data["dob"].replace("Z", "+00:00")) if isinstance(data["dob"], str) else data["dob"]
        if "avatar_url" in data:
            user.avatar_url = str(data["avatar_url"])
        if "extra_metadata" in data:
            user.extra_metadata = data["extra_metadata"] if isinstance(data["extra_metadata"], dict) else {}

        return user

    @staticmethod
    async def delete_user(db_session: AsyncSession, user_id: str) -> SuccessResponse:
        """Moves logic from UserController.delete_user."""
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(f"User {user_id} not found")

        user.deleted_at = datetime.now(timezone.utc)
        user.status = "LOCKED"

        return SuccessResponse(ok=True, id=user_id, message="User locked/deleted")

    @staticmethod
    async def update_role_permissions(db_session: AsyncSession, role_id: str, permission_codes: List[str]) -> SuccessResponse:
        """Moves logic from UserController.update_role_permissions."""
        stmt = select(Role).where(
            or_(Role.id == role_id, Role.code == role_id)
        ).options(selectinload(Role.permissions))

        result = await db_session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise NotFoundException(f"Role {role_id} not found")

        mapped_data = list(permission_codes)
        if all(d.isdigit() for d in permission_codes):
            all_perms_stmt = select(Permission).order_by(Permission.code.asc())
            all_perms_res = await db_session.execute(all_perms_stmt)
            all_perms = all_perms_res.scalars().all()
            numeric_mapping = {str(i+1): p.code for i, p in enumerate(all_perms)}
            mapped_data = [numeric_mapping.get(d, d) for d in permission_codes]

        perm_stmt = select(Permission).where(
            or_(Permission.code.in_(mapped_data), Permission.id.in_(mapped_data))
        )
        perm_result = await db_session.execute(perm_stmt)
        permissions = perm_result.scalars().all()

        role.permissions = list(permissions)
        return SuccessResponse(ok=True, id=str(role.id), message=f"Permissions for role {role.code} updated")

    @staticmethod
    async def get_or_resolve_customer(
        db: AsyncSession,
        phone: str,
        name: Optional[str] = None,
        current_address: Optional[str] = None,
        tenant_id: str = "default"
    ) -> Tuple[User, bool, Optional[str], bool]:
        """
        Elite V2.2: Identify customer by phone and detect address changes.
        Returns: (User, is_new, previous_address, address_changed)
        """
        # 1. Identity Lookup
        stmt = select(User).where(
            and_(
                User.phone == phone,
                User.tenant_id == tenant_id,
                User.deleted_at == None
            )
        )
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            # 2. Returning Customer - Check Address History
            last_order_stmt = (
                select(Order.customer_address)
                .where(Order.user_id == user.id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            last_addr = await db.scalar(last_order_stmt)
            
            address_changed = False
            if last_addr and current_address:
                # Professional Normalization for comparison
                address_changed = last_addr.strip().lower() != current_address.strip().lower()
            
            return user, False, last_addr, address_changed

        # 3. New Customer - Auto-Creation (Identity-First Protocol)
        new_id = str(uuid.uuid4())
        # Use phone as username/email fallback to satisfy NOT NULL constraints
        username = phone
        email = f"{phone}@micsmo.com"
        
        new_user = User(
            id=new_id,
            username=username,
            email=email,
            name=name or "Quý khách",
            phone=phone,
            status="ACTIVE",
            tenant_id=tenant_id
        )

        # Assign CUSTOMER role if it exists in seed
        role_stmt = select(Role).where(Role.code == "CUSTOMER")
        role_res = await db.execute(role_stmt)
        customer_role = role_res.scalar_one_or_none()
        if customer_role:
            new_user.roles.append(customer_role)

        # Elite V2.2: Savepoint guard against concurrent INSERT race condition.
        # If two requests arrive simultaneously for the same new phone, only one
        # INSERT wins; the other catches IntegrityError and re-fetches.
        try:
            async with db.begin_nested():
                db.add(new_user)
                await db.flush()
        except IntegrityError:
            logger.warning("[UserService] Concurrent user creation race detected for phone=%s. Re-fetching.", phone)
            re_stmt = select(User).where(
                or_(
                    and_(User.phone == phone, User.tenant_id == tenant_id, User.deleted_at == None),
                    and_(User.email == email, User.deleted_at == None)
                )
            )
            existing = (await db.execute(re_stmt)).scalar_one_or_none()
            if existing:
                return existing, False, None, False
            raise  # Unknown IntegrityError — re-raise for visibility
        
        return new_user, True, None, False

user_service = UserService()
