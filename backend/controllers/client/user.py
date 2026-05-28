from litestar import Controller, get, patch, post, Request
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Annotated
import logging

from backend.database.models import User, Role
from backend.database.repositories import MediaRegistryRepository
from backend.schemas.user import UserResponse, UserUpdatePayload, UpdatePasswordPayload, LoyaltyResponse, PointTransactionResponse
from backend.schemas.order import OrderListResponse, OrderResponse, CancelOrderRequest
from backend.database.models.commerce import Order, UserLoyalty, PointTransaction
from backend.schemas.common import SuccessResponse
from backend.services.user_service import user_service
from backend.services.media.media_service import media_service

logger = logging.getLogger("api-gateway")

class ClientUserController(Controller):
    path = "/api/v1/client/user"

    @get("/profile")
    async def get_profile(self, request: Request, db_session: AsyncSession) -> UserResponse:
        """
        Elite V3.0: Fetch current user profile.
        """
        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            from litestar.exceptions import NotAuthorizedException
            raise NotAuthorizedException("User not authenticated")
            
        user_id = user_state.get("id")
        
        # Elite V3.1 Fix: Bắt buộc load roles và permissions để Pydantic validate UserResponse (tránh MissingGreenlet 500)
        stmt = select(User).where(User.id == user_id).options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            from litestar.exceptions import NotFoundException
            raise NotFoundException("User profile not found")
            
        return UserResponse.model_validate(user)

    @patch("/profile")
    async def update_profile(self, request: Request, db_session: AsyncSession, data: UserUpdatePayload) -> SuccessResponse:
        """
        Elite V3.0: Update current user profile (Name, Gender, DOB).
        """
        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            from litestar.exceptions import NotAuthorizedException
            raise NotAuthorizedException("User not authenticated")

        user_id = user_state.get("id")

        try:
            # We use a restricted update for clients (can't change roles/status)
            update_data = data.model_dump(exclude_unset=True)
            # Security: Remove keys that customers shouldn't touch
            update_data.pop("roles", None)
            update_data.pop("status", None)

            # Elite V3.0: Delegate all field mapping to Service
            await user_service.update_user(db_session, user_id, update_data)
            await db_session.commit()
            
            return SuccessResponse(ok=True, id=user_id)
        except IntegrityError as e:
            await db_session.rollback()
            from litestar.exceptions import ClientException
            error_msg = str(e.orig)
            if "users_username_key" in error_msg:
                raise ClientException(status_code=409, detail="Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.")
            if "users_email_key" in error_msg:
                raise ClientException(status_code=409, detail="Địa chỉ Email đã được sử dụng bởi một tài khoản khác.")
            raise ClientException(status_code=409, detail="Thông tin cập nhật bị trùng lặp dữ liệu.")
        except Exception as e:
            await db_session.rollback()
            logger.exception("Error updating profile for user %s: %s", user_id, str(e))
            raise e

    @get("/orders")
    async def get_my_orders(
        self,
        request: Request,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> OrderListResponse:
        """
        Elite V3.0: Fetch order history for the current authenticated user.
        """
        from backend.database.models.commerce import Order
        from sqlalchemy import and_, select, func
        from backend.database import current_tenant_id

        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            from litestar.exceptions import NotAuthorizedException
            raise NotAuthorizedException("User not authenticated")

        user_id = user_state.get("id")

        # SECURITY: Cap pagination to prevent DoS
        limit = max(1, min(limit, 100))
        offset = max(0, min(offset, 10_000))

        conditions = [
            Order.user_id == user_id,
            Order.deleted_at == None,
            Order.tenant_id == (current_tenant_id.get() or "default")
        ]

        if status and status != "all":
            conditions.append(Order.status == status.upper())

        # Count total
        count_stmt = select(func.count(Order.id)).where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0

        # Fetch data
        stmt = select(Order).where(and_(*conditions)).limit(limit).offset(offset).order_by(Order.created_at.desc())
        result = await db_session.execute(stmt)
        orders = result.scalars().all()

        data = [OrderResponse.model_validate(order) for order in orders]
        return OrderListResponse(data=data, total=total)

    @post("/orders/{order_id:str}/cancel")
    async def cancel_my_order(
        self,
        request: Request,
        db_session: AsyncSession,
        order_id: str,
        data: CancelOrderRequest
    ) -> SuccessResponse:
        """
        Elite V2.2: Public Secure Cancellation Endpoint.
        Allows users to cancel their own PENDING orders.
        """
        from backend.services.commerce.order import order_service
        from backend.database.models.commerce import Order
        from litestar.exceptions import NotAuthorizedException, ValidationException

        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            raise NotAuthorizedException("User not authenticated")
        user_id = user_state.get("id")

        # 1. Ownership & Existential Verification
        stmt = select(Order).where(Order.id == order_id)
        res = await db_session.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
             from litestar.exceptions import NotFoundException
             raise NotFoundException(f"Đơn hàng {order_id} không tồn tại")
        
        if str(order.user_id) != str(user_id):
             raise NotAuthorizedException("Bạn không có quyền hủy đơn hàng này.")

        # 2. Strict State Machine (Shopee policy): Only PENDING orders can be self-cancelled.
        # PACKED = kho da dong goi, khong the tu huy — phai lien he shop.
        if order.status.upper() not in ["PENDING"]:
             raise ValidationException("Đơn hàng này đã vào giai đoạn vận chuyển và không thể tự hủy.")

        # 3. Delegate to Service for history and event bus
        res = await order_service.cancel_order(
            db_session=db_session,
            order_id=order_id,
            reason=data.reason,
            actor_email=user_state.get("username", "Customer")
        )
        await db_session.commit()
        return res

    @post("/avatar")
    async def upload_avatar(
        self,
        request: Request,
        db_session: AsyncSession,
    ) -> SuccessResponse:
        """
        Elite V3.0: Securely upload and set profile avatar.
        SECURITY: MIME whitelist, 5MB cap, isolated 'avatars/' storage.
        """
        from litestar.exceptions import NotAuthorizedException, ValidationException, NotFoundException, InternalServerException
        from backend.database.models.media import MediaRegistry  # noqa: F401 - used below

        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            raise NotAuthorizedException("User not authenticated")

        user_id = user_state.get("id")

        form = await request.form()
        file = form.get("file")

        if not file or not hasattr(file, "read"):
            raise ValidationException("Vui long cung cap tep tin hinh anh (field: 'file')")

        # SECURITY: MIME whitelist - block executable/malicious types
        ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        content_type = getattr(file, "content_type", "") or ""
        if content_type.lower() not in ALLOWED_MIME:
            raise ValidationException(f"Dinh dang khong duoc phep: {content_type}. Chi chap nhan: JPEG, PNG, WebP, GIF.")

        content = await file.read()
        filename = file.filename

        # SECURITY: 5MB hard cap to prevent memory exhaustion
        MAX_AVATAR_BYTES = 5 * 1024 * 1024  # 5MB
        if len(content) > MAX_AVATAR_BYTES:
            raise ValidationException("Kich thuoc anh khong duoc vuot qua 5MB.")

        # 1. Fetch current user to get old avatar_url
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")

        old_avatar_path = user.avatar_url

        # 2. Upload new avatar with 'avatars/' prefix for isolation
        repo = MediaRegistryRepository(session=db_session)
        asset = await media_service.upload_asset(
            repo=repo,
            file_content=content,
            filename=filename,
            content_type=content_type,
            owner_id=user_id,
            is_avatar=True
        )

        if not asset:
            raise InternalServerException("Failed to process avatar upload")

        # 3. Update user avatar_url
        user.avatar_url = asset.file_path
        await db_session.commit()

        # 4. Hard-delete old avatar if it exists
        if old_avatar_path:
            from backend.services.storage.manager import storage
            try:
                await storage.delete(old_avatar_path)
                stmt_asset = select(MediaRegistry).where(MediaRegistry.file_path == old_avatar_path)
                old_asset = (await db_session.execute(stmt_asset)).scalar_one_or_none()
                if old_asset:
                    await db_session.delete(old_asset)
                    await db_session.commit()
            except Exception as e:
                logger.error(f"Failed to hard-delete old avatar {old_avatar_path}: {e}")

        return SuccessResponse(ok=True, id=user_id, data={"avatar_url": asset.file_path})

    @patch("/password")
    async def update_password(self, request: Request, db_session: AsyncSession, data: UpdatePasswordPayload) -> SuccessResponse:
        """
        Elite V3.0: Securely update current user password.
        """
        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            from litestar.exceptions import NotAuthorizedException
            raise NotAuthorizedException("User not authenticated")

        user_id = user_state.get("id")
        
        res = await user_service.update_password(
            db_session=db_session,
            user_id=user_id,
            old_password=data.old_password,
            new_password=data.new_password
        )
        await db_session.commit()
        return res

    @get("/loyalty")
    async def get_loyalty(self, request: Request, db_session: AsyncSession) -> LoyaltyResponse:
        """
        Elite V2.2: Fetch loyalty points and history.
        """
        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            from litestar.exceptions import NotAuthorizedException
            raise NotAuthorizedException("User not authenticated")
            
        user_id = user_state.get("id")
        
        # Fetch loyalty profile
        l_stmt = select(UserLoyalty).where(UserLoyalty.user_id == user_id)
        l_res = await db_session.execute(l_stmt)
        loyalty = l_res.scalar_one_or_none()
        
        if not loyalty:
            # Sếp Rule: Auto-create if not exists upon first view
            loyalty = UserLoyalty(user_id=user_id, available_points=0, total_spent=0.0)
            db_session.add(loyalty)
            await db_session.flush()
            
        # Fetch history (limited to last 50)
        h_stmt = select(PointTransaction).where(PointTransaction.user_id == user_id).order_by(PointTransaction.created_at.desc()).limit(50)
        h_res = await db_session.execute(h_stmt)
        history = h_res.scalars().all()
        
        resp = LoyaltyResponse.model_validate(loyalty)
        resp.history = [PointTransactionResponse.model_validate(h) for h in history]
        
        return resp

