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
            attributes=data.attributes,
            attachments=data.attachments,
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

    async def get_reviews(self, limit: int = 20, offset: int = 0, entity_type: str | None = None, entity_id: str | None = None, status: str | None = None, **kwargs):
        filters = []
        if entity_type:
            filters.append(SystemReview.entity_type == entity_type)
        if entity_id:
            filters.append(SystemReview.entity_id == entity_id)
        if status:
            filters.append(SystemReview.status == status)
        
        if kwargs.get("has_media"):
            filters.append(SystemReview.attachments != None)
        if kwargs.get("rating"):
            filters.append(SystemReview.rating == int(kwargs.get("rating")))
            
        repo_kwargs = {}
        if filters:
            from sqlalchemy import and_
            repo_kwargs["statement"] = self.review_repo.statement.where(and_(*filters))

        reviews, total = await self.review_repo.list_and_count(
            LimitOffset(limit=limit, offset=offset),
            **repo_kwargs
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

    async def get_review_stats(self, entity_type: str, entity_id: str) -> dict:
        """Thống kê chi tiết đánh giá cho UI Product Detail (Elite V2.2)."""
        from sqlalchemy import select, func, and_
        
        # 1. Cơ bản: Total & Average
        stmt = select(
            func.count(SystemReview.id).label("total"),
            func.avg(SystemReview.rating).label("avg")
        ).where(and_(
            SystemReview.entity_type == entity_type,
            SystemReview.entity_id == entity_id,
            SystemReview.status == "APPROVED"
        ))
        result = await self.review_repo.session.execute(stmt)
        row = result.fetchone()
        total_count = row.total if row else 0
        avg_rating = float(row.avg) if row and row.avg else 0.0

        # 2. Rating Breakdown
        stmt_breakdown = select(
            SystemReview.rating,
            func.count(SystemReview.id)
        ).where(and_(
            SystemReview.entity_type == entity_type,
            SystemReview.entity_id == entity_id,
            SystemReview.status == "APPROVED"
        )).group_by(SystemReview.rating)
        
        breakdown_res = await self.review_repo.session.execute(stmt_breakdown)
        rating_breakdown = {i: 0 for i in range(1, 6)}
        for r, c in breakdown_res:
            rating_breakdown[r] = c

        # 3. Has Media & Has Content
        stmt_media = select(func.count(SystemReview.id)).where(and_(
            SystemReview.entity_type == entity_type,
            SystemReview.entity_id == entity_id,
            SystemReview.status == "APPROVED",
            SystemReview.attachments != None
        ))
        media_count = await self.review_repo.session.scalar(stmt_media) or 0

        stmt_content = select(func.count(SystemReview.id)).where(and_(
            SystemReview.entity_type == entity_type,
            SystemReview.entity_id == entity_id,
            SystemReview.status == "APPROVED",
            SystemReview.content != ""
        ))
        content_count = await self.review_repo.session.scalar(stmt_content) or 0

        return {
            "total_count": total_count,
            "average_rating": round(avg_rating, 1),
            "rating_breakdown": rating_breakdown,
            "has_content_count": content_count,
            "has_media_count": media_count
        }

async def provide_review_service(review_repo: SystemReviewRepository) -> ReviewService:
    return ReviewService(review_repo)
