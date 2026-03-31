from datetime import datetime, timezone
from litestar import Controller, post, get
from litestar.di import Provide
from litestar.params import Parameter
from litestar.middleware.rate_limit import RateLimitConfig
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

    @get()
    async def list_reviews(
        self,
        review_service: ReviewService,
        limit: int = Parameter(query="limit", default=20),
        offset: int = Parameter(query="offset", default=0),
        entity_type: str | None = Parameter(query="entity_type", required=False, default=None),
        entity_id: str | None = Parameter(query="entity_id", required=False, default=None)
    ) -> dict:
        # Public listing ONLY allows APPROVED status
        reviews, total = await review_service.get_reviews(
            limit=limit,
            offset=offset,
            entity_type=entity_type,
            entity_id=entity_id,
            status="APPROVED"
        )
        return {
            "items": [ReviewResponse.model_validate(r).model_dump() for r in reviews],
            "total": total
        }

    @post(middleware=[RateLimitConfig(rate_limit=("minute", 5)).middleware])
    async def create_review(self, data: CreateReviewRequest, review_service: ReviewService, db_session: AsyncSession) -> ReviewResponse:
        # [R82] BOT_HONEYPOT: Silent Rejection
        if data.website_url:
            # We return a fake success or just ignore to avoid tipping off the bot
            return ReviewResponse(
                id="bot-rejected",
                entity_type=data.entity_type,
                entity_id=data.entity_id,
                customer_name=data.customer_name,
                customer_phone=data.customer_phone,
                customer_location=data.customer_location,
                rating=data.rating,
                content=data.content,
                status="REJECTED",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ) 

        # Create review and return response mapping
        review = await review_service.create_review(data)
        await db_session.commit()
        return ReviewResponse.model_validate(review)
