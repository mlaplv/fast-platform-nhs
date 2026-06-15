import logging
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional, Tuple
from collections import defaultdict
import uuid
from backend.utils.uid import new_id

from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from litestar.exceptions import NotFoundException, ClientException, NotAuthorizedException
import bcrypt

from backend.database.models import User, Role, Permission, Order, Base
from backend.database.models.commerce import UserLoyalty, PointTransaction
from backend.schemas.user import UserResponse, UserListResponse, RoleResponse, PermissionResponse, LoyaltyResponse, PointAdjustmentRequest
from backend.schemas.common import SuccessResponse
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

class UserService:
    @staticmethod
    async def sync_rbac(db_session: AsyncSession) -> None:
        """
        [Elite V2.2] Auto-Sync Mechanism.
        Đảm bảo PermissionEnum luôn khớp 100% với Database khi hệ thống khởi động.
        """
        logger.info("🔐 [RBAC Sync] Synchronizing permissions and system roles...")
        
        # 1. Sync Permissions
        all_codes = PermissionEnum.all_codes()
        existing_perms_res = await db_session.execute(select(Permission))
        existing_perms = {p.code: p for p in existing_perms_res.scalars().all()}
        
        for code in all_codes:
            if code not in existing_perms:
                parts = code.split(":")
                name = " ".join([p.capitalize() for p in parts])
                p = Permission(id=f"perm_{code.replace(':', '_')}", name=name, code=code)
                db_session.add(p)
                existing_perms[code] = p
        
        await db_session.flush()

        # 2. Sync Core Roles (SUPER_ADMIN, CUSTOMER, etc.)
        # Rule: SUPER_ADMIN must always have ALL permissions
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.code == "SUPER_ADMIN")
        sa_role = (await db_session.execute(stmt)).scalar_one_or_none()
        
        if not sa_role:
            sa_role = Role(id="role_superadmin", name="Super Admin", code="SUPER_ADMIN", tenant_id="osmo")
            db_session.add(sa_role)
        
        sa_role.permissions = list(existing_perms.values())
        
        # Ensure CUSTOMER role exists
        cust_stmt = select(Role).where(Role.code == "CUSTOMER")
        if not (await db_session.execute(cust_stmt)).scalar_one_or_none():
            db_session.add(Role(id="role_customer", name="Customer", code="CUSTOMER", tenant_id="osmo"))
            
        await db_session.commit()
        logger.info("✅ [RBAC Sync] Permissions and System Roles are now Elite V2.2 compliant.")

    @staticmethod
    def _is_elite_admin(username: str, email: str) -> bool:
        """Centralized Elite Admin Detection Logic."""
        return username in ["admin", "mlap"] or email in ["admin@osmo", "boss@osmo"]

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
                User.id, User.email, User.username, User.name, User.status, User.created_at
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
    async def create_user(db_session: AsyncSession, data: Dict[str, object]) -> User:
        """Elite V2.2: Create a new user identity with hashed password."""
        email = str(data["email"])
        name = str(data["name"])
        password = str(data.get("password", "SmartShop@123"))
        username = str(data.get("username", email.split("@")[0]))
        
        # Check for existing
        stmt = select(User).where(or_(User.email == email, User.username == username))
        existing = await db_session.scalar(stmt)
        if existing:
            raise ClientException(status_code=400, detail="Identity or Email already exists in this sector.")

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = User(
            id=new_id(),
            email=email,
            username=username,
            name=name,
            password=hashed,
            status="ACTIVE"
        )
        
        # Handle Roles
        role_codes = data.get("role_codes", [])
        
        # Auto-Admin Detection for Elite accounts
        if UserService._is_elite_admin(username, email) and "SUPER_ADMIN" not in role_codes:
            role_codes.append("SUPER_ADMIN")
        
        # Default to CUSTOMER if still empty
        if not role_codes:
            role_codes = ["CUSTOMER"]

        if role_codes:
            role_stmt = select(Role).options(selectinload(Role.permissions)).where(Role.code.in_(role_codes))
            role_res = await db_session.execute(role_stmt)
            new_user.roles = list(role_res.scalars().all())

        db_session.add(new_user)
        await db_session.flush() # Ensure ID is generated and constraints checked
        return new_user

    @staticmethod
    async def update_user(db_session: AsyncSession, user_id: str, data: Dict[str, object]) -> User:
        """Moves logic from UserController.update_user. Elite V2.2: Returns hydrated model."""
        stmt = select(User).where(User.id == user_id).options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(f"User {user_id} not found")

        if "username" in data:
            val = str(data["username"]).strip()
            if val:
                user.username = val
        if "email" in data:
            val = str(data["email"]).strip()
            if val:
                user.email = val
        if "name" in data: user.name = str(data["name"])
        if "status" in data: user.status = str(data["status"])
        if "gender" in data: user.gender = str(data["gender"])
        if "dob" in data:
            val = data["dob"]
            if isinstance(val, str) and val:
                # Elite V3.0: Ensure timezone awareness for sa.DateTime(timezone=True)
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                user.dob = dt
            elif isinstance(val, datetime):
                user.dob = val if val.tzinfo else val.replace(tzinfo=timezone.utc)
            else:
                user.dob = None

        if "avatar_url" in data: user.avatar_url = str(data["avatar_url"])
        if "phone" in data: user.phone = str(data["phone"])
        if "extra_metadata" in data:
            incoming = data["extra_metadata"] if isinstance(data["extra_metadata"], dict) else {}
            # Elite V3.1: Deep merge — không overwrite — bảo vệ các key khác (tier, points, skinProfile...)
            # SQLAlchemy không detect mutation trên JSON column → bắt buộc dùng flag_modified()
            merged = {**(user.extra_metadata or {}), **incoming}
            user.extra_metadata = merged
            flag_modified(user, "extra_metadata")  # ← Kìu SQLAlchemy flush JSON vào DB

        if "roles" in data and isinstance(data["roles"], list):
            role_codes = list(data["roles"])
            # Auto-Admin Reinforcement
            if UserService._is_elite_admin(user.username, user.email) and "SUPER_ADMIN" not in role_codes:
                role_codes.append("SUPER_ADMIN")
                
            role_stmt = select(Role).options(selectinload(Role.permissions)).where(Role.code.in_(role_codes))
            role_res = await db_session.execute(role_stmt)
            user.roles = list(role_res.scalars().all())

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
    async def update_password(db_session: AsyncSession, user_id: str, old_password: Optional[str], new_password: str) -> SuccessResponse:
        """
        Elite V3.0: Securely update or set user password.
        Supports Social/OTP users setting their first password.
        """
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(f"User {user_id} not found")

        # 1. Verification logic
        if user.password is not None:
            # Case: Standard user, must verify existing password
            if not old_password:
                raise ClientException(status_code=400, detail="Vui lòng cung cấp mật khẩu hiện tại.")
            
            is_valid = bcrypt.checkpw(
                old_password.encode('utf-8'),
                user.password.encode('utf-8')
            )
            if not is_valid:
                raise NotAuthorizedException("Mật khẩu hiện tại không chính xác.")
        else:
            # Case: Social/OTP user setting password for the first time
            logger.info(f"[UserService] Social user {user.email} setting first password.")

        # 2. Hashing and storage
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password = hashed
        
        # 3. Security Stamp rotation if applicable
        if hasattr(user, "security_stamp"):
            user.security_stamp = new_id()
            # Invalidate Redis cache for stamp
            try:
                from backend.services.ai_engine.core.key_rotator import key_rotator
                if key_rotator._use_redis and key_rotator.client:
                    stamp_key = f"security:stamp:{user_id}"
                    await key_rotator.client.delete(stamp_key)
            except Exception:
                pass

        return SuccessResponse(ok=True, id=user_id, message="Mật khẩu đã được cập nhật thành công.")

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
        user = res.scalars().first()

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
        new_id_val = new_id()
        # Use phone as username/email fallback to satisfy NOT NULL constraints
        username = phone
        email = f"{phone}@osmo"
        
        new_user = User(
            id=new_id_val,
            username=username,
            email=email,
            name=name or "Quý khách",
            phone=phone,
            status="ACTIVE",
            tenant_id=tenant_id
        )

        # Assign CUSTOMER role if it exists in seed
        role_stmt = select(Role).options(selectinload(Role.permissions)).where(Role.code == "CUSTOMER")
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


    @staticmethod
    async def get_user_loyalty(db_session: AsyncSession, user_id: str) -> LoyaltyResponse:
        """Fetch user loyalty summary for admin."""
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
        loyalty = await db_session.scalar(stmt)
        
        if not loyalty:
            # Create if missing
            loyalty = UserLoyalty(user_id=user_id, available_points=0, total_spent=0.0)
            db_session.add(loyalty)
            await db_session.flush()

        history_stmt = (
            select(PointTransaction)
            .where(PointTransaction.user_id == user_id)
            .order_by(PointTransaction.created_at.desc())
            .limit(50)
        )
        history = (await db_session.execute(history_stmt)).scalars().all()
        
        res = LoyaltyResponse.model_validate(loyalty)
        res.history = history
        return res

    @staticmethod
    async def adjust_points(db_session: AsyncSession, user_id: str, data: PointAdjustmentRequest) -> SuccessResponse:
        """Manually adjust user points (Admin Logic)."""
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
        loyalty = await db_session.scalar(stmt)
        
        if not loyalty:
            loyalty = UserLoyalty(user_id=user_id, available_points=0, total_spent=0.0)
            db_session.add(loyalty)

        loyalty.available_points += data.amount
        
        # Create ledger entry
        transaction = PointTransaction(
            user_id=user_id,
            amount=data.amount,
            transaction_type=data.transaction_type,
            status="COMPLETED",
            notes=data.notes
        )
        db_session.add(transaction)
        
        return SuccessResponse(ok=True, message=f"Adjusted {data.amount} points. New balance: {loyalty.available_points}")

user_service = UserService()
