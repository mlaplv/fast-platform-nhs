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
from backend.schemas.user import UserResponse, UserUpdatePayload, UpdatePasswordPayload
from backend.schemas.order import OrderListResponse, OrderResponse
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

    @post("/avatar")
    async def upload_avatar(
        self, 
        request: Request, 
        db_session: AsyncSession,
    ) -> SuccessResponse:
        """
        Elite V3.0: Securely upload and set profile avatar.
        """
        user_state = request.scope.get("state", {}).get("user")
        if not user_state:
            from litestar.exceptions import NotAuthorizedException
            raise NotAuthorizedException("User not authenticated")
            
        user_id = user_state.get("id")
        
        # Elite V3.1: Manual form parsing to bypass Litestar validation issues with UploadFile
        form = await request.form()
        file = form.get("file")
        
        if not file or not hasattr(file, "read"):
             from litestar.exceptions import ValidationException
             raise ValidationException("Vui lòng cung cấp tệp tin hình ảnh (field: 'file')")
             
        content = await file.read()
        filename = file.filename
        content_type = file.content_type
        
        repo = MediaRegistryRepository(session=db_session)
        asset = await media_service.upload_asset(
            repo=repo,
            file_content=content,
            filename=filename,
            content_type=content_type,
            owner_id=user_id
        )
        
        if not asset:
            from litestar.exceptions import InternalServerException
            raise InternalServerException("Failed to process avatar upload")
            
        # Update user avatar_url
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.avatar_url = asset.file_path
            
        await db_session.commit()
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
