from litestar import Controller, get, patch, delete, post
from litestar.exceptions import ValidationException
from litestar.di import Provide
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.review import UpdateReviewStatusRequest, UpdateReviewRequest, ReviewResponse, AiSeedReviewRequest
from backend.services.review_service import ReviewService, provide_review_service
from backend.database.repositories import provide_system_review_repo
from backend.constants.permissions import PermissionEnum
from backend.guards import PermissionGuard
import logging

logger = logging.getLogger("api-gateway")

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
        entity_id: str | None = Parameter(query="entity_id", required=False, default=None),
        status: str | None = Parameter(query="status", required=False, default=None)
    ) -> dict:
        reviews, total = await review_service.get_reviews(
            limit=limit,
            offset=offset,
            entity_type=entity_type,
            entity_id=entity_id,
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

    @patch("/{review_id:str}")
    async def update_review_full(
        self,
        review_id: str,
        data: UpdateReviewRequest,
        review_service: ReviewService,
        db_session: AsyncSession
    ) -> ReviewResponse:
        """Elite V2.2: Universal Review Update (Content + Metadata)."""
        review = await review_service.update_content(review_id, data)
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

    @post("/ai-seed")
    async def ai_seed_one_review(
        self,
        data: AiSeedReviewRequest,
        review_service: ReviewService,
        db_session: AsyncSession
    ) -> ReviewResponse:
        """
        Xohi Review Lab: Tạo 1 đánh giá chất lượng cao bằng AI.
        Phong cách random (tiktok/shopee/lazada/authentic), bypass anti-spam.
        Extensible: entity_type hỗ trợ PRODUCT, NEWS, CATEGORY.
        """
        try:
            review = await review_service.ai_seed_one(
                entity_type=data.entity_type,
                entity_id=data.entity_id
            )
        except ValueError as exc:
            logger.warning(
                "[ReviewLab] Invalid seed request: entity_type=%s entity_id=%s — %s",
                data.entity_type, data.entity_id, exc
            )
            raise ValidationException(detail=str(exc)) from exc
        await db_session.commit()
        logger.info(
            "[ReviewLab] AI-seeded review %s for %s %s (style=%s)",
            review.id, data.entity_type, data.entity_id,
            (review.attributes or {}).get("style", "?")
        )
        return ReviewResponse.model_validate(review)
