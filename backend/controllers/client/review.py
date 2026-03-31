from litestar import Controller, post
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.review import CreateReviewRequest, ReviewResponse
from backend.services.review_service import ReviewService, provide_review_service
from backend.database.repositories import provide_system_review_repo

class PublicReviewController(Controller):
    path = "/api/v1/client/reviews"
    tags = ["Client Review"]
    dependencies = {
        "review_repo": Provide(provide_system_review_repo),
        "review_service": Provide(provide_review_service),
    }

    @post()
    async def create_review(self, data: CreateReviewRequest, review_service: ReviewService, db_session: AsyncSession) -> ReviewResponse:
        # Create review and return response mapping
        review = await review_service.create_review(data)
        await db_session.commit()
        return ReviewResponse.model_validate(review)
