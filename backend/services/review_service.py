from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.filters import LimitOffset

from backend.database.models.system import SystemReview, ReviewEntityType
from backend.database.repositories import SystemReviewRepository
from backend.schemas.review import CreateReviewRequest, UpdateReviewStatusRequest

class ReviewService:
    def __init__(self, review_repo: SystemReviewRepository):
        self.review_repo = review_repo

    async def create_review(self, data: CreateReviewRequest) -> SystemReview:
        # 1. Anti-Spam: Duplicate Check (R67)
        if await self.is_duplicate(data):
            raise ValueError("Hệ thống phát hiện đánh giá trùng lặp. Vui lòng thử lại sau 24h.")

        # 2. Create review with PENDING status
        review = SystemReview(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_location=data.customer_location,
            rating=data.rating,
            content=data.content,
            status="PENDING"
        )
        return await self.review_repo.add(review)

    async def is_duplicate(self, data: CreateReviewRequest) -> bool:
        """Check if same user recently reviewed this entity (24h window)."""
        from datetime import datetime, timedelta
        from sqlalchemy import and_, select, func
        
        since = datetime.now() - timedelta(hours=24)
        
        # We check both name and phone if provided
        filters = [
            SystemReview.entity_id == data.entity_id,
            SystemReview.created_at >= since
        ]
        
        if data.customer_phone:
            filters.append(SystemReview.customer_phone == data.customer_phone)
        elif data.customer_name:
            filters.append(SystemReview.customer_name == data.customer_name)
            
        stmt = select(func.count()).select_from(SystemReview).where(and_(*filters))
        count = await self.review_repo.session.scalar(stmt)
        return count > 0

    async def get_reviews(self, limit: int = 20, offset: int = 0, entity_type: str | None = None, entity_id: str | None = None, status: str | None = None):
        filters = []
        if entity_type:
            filters.append(SystemReview.entity_type == entity_type)
        if entity_id:
            filters.append(SystemReview.entity_id == entity_id)
        if status:
            filters.append(SystemReview.status == status)
            
        kwargs = {}
        if filters:
            from sqlalchemy import and_
            kwargs["statement"] = self.review_repo.statement.where(and_(*filters))

        reviews, total = await self.review_repo.list_and_count(
            LimitOffset(limit=limit, offset=offset),
            **kwargs
        )
        return reviews, total

    async def update_status(self, review_id: str, data: UpdateReviewStatusRequest) -> SystemReview:
        try:
            review = await self.review_repo.get(review_id)
            review.status = data.status
            return await self.review_repo.update(review)
        except NotFoundError:
            raise ValueError(f"Review {review_id} not found")

    async def delete_review(self, review_id: str):
        try:
            await self.review_repo.delete(review_id)
        except NotFoundError:
            raise ValueError(f"Review {review_id} not found")

async def provide_review_service(review_repo: SystemReviewRepository) -> ReviewService:
    return ReviewService(review_repo)
