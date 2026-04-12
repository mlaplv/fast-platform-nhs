from litestar import Controller, get, patch, delete
from litestar.di import Provide
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.review import UpdateReviewStatusRequest, UpdateReviewRequest, ReviewResponse
from backend.services.review_service import ReviewService, provide_review_service
from backend.database.repositories import provide_system_review_repo
from backend.constants.permissions import PermissionEnum
from backend.guards import PermissionGuard

class AdminReviewController(Controller):
    path = "/api/v1/reviews"
    tags = ["Admin Review"]
    guards = [PermissionGuard(PermissionEnum.PRODUCT_WRITE)] # R02 Strict Permission
    dependencies = {
        "review_repo": Provide(provide_system_review_repo),
        "review_service": Provide(provide_review_service),
    }

    @get()
    async def list_reviews(
        self,
        review_service: ReviewService,
        limit: int = Parameter(query="limit", default=20),
        offset: int = Parameter(query="offset", default=0),
        entity_type: str | None = Parameter(query="entity_type", required=False, default=None),
        status: str | None = Parameter(query="status", required=False, default=None)
    ) -> dict:
        reviews, total = await review_service.get_reviews(
            limit=limit,
            offset=offset,
            entity_type=entity_type,
            status=status
        )
        return {
            "items": [ReviewResponse.model_validate(r).model_dump() for r in reviews],
            "total": total
        }

    @patch("/{review_id:str}/status")
    async def update_status(
        self,
        review_id: str,
        data: UpdateReviewStatusRequest,
        review_service: ReviewService,
        db_session: AsyncSession
    ) -> ReviewResponse:
        review = await review_service.update_status(review_id, data)
        await db_session.commit()
        return ReviewResponse.model_validate(review)

    @patch("/{review_id:str}/content")
    async def update_content(
        self,
        review_id: str,
        data: UpdateReviewRequest,
        review_service: ReviewService,
        db_session: AsyncSession
    ) -> ReviewResponse:
        review = await review_service.update_content(review_id, data)
        await db_session.commit()
        return ReviewResponse.model_validate(review)

    @delete("/{review_id:str}")
    async def delete_review(
        self,
        review_id: str,
        review_service: ReviewService,
        db_session: AsyncSession
    ) -> None:
        await review_service.delete_review(review_id)
        await db_session.commit()
