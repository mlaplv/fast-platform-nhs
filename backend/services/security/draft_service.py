from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.system import Draft
from backend.database.models import User, Role
from backend.schemas.common import SuccessResponse
from litestar.exceptions import NotFoundException
import logging

logger = logging.getLogger("api-gateway")

class DraftService:
    async def list_drafts(self, db_session: AsyncSession) -> list[Draft]:
        stmt = select(Draft).where(Draft.status == "PENDING").order_by(Draft.created_at.desc())
        res = await db_session.execute(stmt)
        return list(res.scalars().all())

    async def approve_draft(self, db_session: AsyncSession, draft_id: str, reviewer_id: str) -> SuccessResponse:
        stmt = select(Draft).where(Draft.id == draft_id)
        res = await db_session.execute(stmt)
        draft = res.scalar_one_or_none()
        if not draft:
            raise NotFoundException("Draft not found")

        # Apply the changes
        try:
            if draft.action == "DELETE":
                # Handle soft delete if model supports it
                # For now, simplistic mapping
                if draft.target_model == "users":
                    from backend.services.user_service import user_service
                    await user_service.delete_user(db_session, draft.target_id)
            
            elif draft.action == "UPDATE_ROLES":
                if draft.target_model == "users":
                    from backend.services.user_service import user_service
                    await user_service.update_roles(db_session, draft.target_id, draft.payload.get("roles", []))
            
            elif draft.action == "FORCE_LOGOUT":
                if draft.target_model == "users":
                    import uuid
                    stmt = update(User).where(User.id == draft.target_id).values(security_stamp=str(uuid.uuid4()))
                    await db_session.execute(stmt)

            draft.status = "APPROVED"
            draft.reviewer_id = reviewer_id
            await db_session.commit()
            return SuccessResponse(message="Yêu cầu đã được thực thi thành công.")
        except Exception as e:
            await db_session.rollback()
            logger.error(f"Failed to apply draft {draft_id}: {e}")
            raise

    async def reject_draft(self, db_session: AsyncSession, draft_id: str, reviewer_id: str) -> SuccessResponse:
        stmt = select(Draft).where(Draft.id == draft_id)
        res = await db_session.execute(stmt)
        draft = res.scalar_one_or_none()
        if not draft:
            raise NotFoundException("Draft not found")
        
        draft.status = "REJECTED"
        draft.reviewer_id = reviewer_id
        await db_session.commit()
        return SuccessResponse(message="Yêu cầu đã bị từ chối.")

draft_service = DraftService()
