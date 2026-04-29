from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.filters import LimitOffset

from backend.database.models.system import SystemReview, ReviewEntityType
from backend.database.repositories import SystemReviewRepository
from backend.schemas.review import CreateReviewRequest, UpdateReviewStatusRequest, UpdateReviewRequest

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
            # Elite V2.2: Defensive JSONB Check using CASE to prevent scalar evaluation
            from sqlalchemy import func, case
            filters.append(case(
                (func.jsonb_typeof(SystemReview.attachments) == 'array', func.jsonb_array_length(SystemReview.attachments)),
                else_=0
            ) > 0)
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

    async def update_content(self, review_id: str, data: UpdateReviewRequest) -> SystemReview:
        try:
            review = await self.review_repo.get(review_id)
            review.content = data.content
            
            # Smart Diff: Xóa vật lý những attachment bị loại bỏ khỏi danh sách khi edit
            if data.attachments is not None:
                old_urls = set(media.get("url", "") for media in (review.attachments or []))
                new_urls = set(media.get("url", "") for media in data.attachments)
                
                removed_urls = old_urls - new_urls
                if removed_urls:
                    from backend.services.media.media_service import media_service
                    from backend.database.repositories import MediaRegistryRepository
                    from backend.database.models import MediaRegistry
                    from sqlalchemy import select
                    
                    media_repo = MediaRegistryRepository(session=self.review_repo.session)
                    for url in removed_urls:
                        if not url: continue
                        path = url.split("?")[0]
                        if "://" in path:
                            parts = path.split("://")[1].split("/", 1)
                            path = "/" + parts[1] if len(parts) > 1 else "/"
                        if not path.startswith("/"): path = "/" + path
                        
                        stmt = select(MediaRegistry).where(
                            (MediaRegistry.file_path == path) | 
                            (MediaRegistry.file_path == path.lstrip("/"))
                        )
                        asset = (await self.review_repo.session.execute(stmt)).scalar_one_or_none()
                        if asset:
                            await media_service.delete_asset(media_repo, str(asset.id), permanent=True)
                        else:
                            try:
                                from backend.services.storage.manager import storage
                                await storage.delete(path)
                            except Exception:
                                pass
                
                review.attachments = data.attachments

            return await self.review_repo.update(review)
        except NotFoundError:
            raise ValueError(f"Review {review_id} not found")

    async def delete_review(self, review_id: str):
        try:
            review = await self.review_repo.get(review_id)
            
            # Physical Hard Delete Media before deleting the review
            if review.attachments:
                from backend.services.media.media_service import media_service
                from backend.database.repositories import MediaRegistryRepository
                from backend.database.models import MediaRegistry
                from sqlalchemy import select
                
                media_repo = MediaRegistryRepository(session=self.review_repo.session)
                
                for media in review.attachments:
                    url = media.get("url", "")
                    if url:
                        path = url.split("?")[0]
                        if "://" in path:
                            parts = path.split("://")[1].split("/", 1)
                            path = "/" + parts[1] if len(parts) > 1 else "/"
                        if not path.startswith("/"): path = "/" + path
                        
                        stmt = select(MediaRegistry).where(
                            (MediaRegistry.file_path == path) | 
                            (MediaRegistry.file_path == path.lstrip("/"))
                        )
                        asset = (await self.review_repo.session.execute(stmt)).scalar_one_or_none()
                        if asset:
                            await media_service.delete_asset(media_repo, str(asset.id), permanent=True)
                        else:
                            try:
                                from backend.services.storage.manager import storage
                                await storage.delete(path)
                            except Exception:
                                pass

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

        # 3. Has Media (Elite V2.2: Defensive JSONB check using CASE to avoid scalar errors)
        from sqlalchemy import case
        stmt_media = select(func.count(SystemReview.id)).where(and_(
            SystemReview.entity_type == entity_type,
            SystemReview.entity_id == entity_id,
            SystemReview.status == "APPROVED",
            case(
                (func.jsonb_typeof(SystemReview.attachments) == 'array', func.jsonb_array_length(SystemReview.attachments)),
                else_=0
            ) > 0
        ))
        media_count = await self.review_repo.session.scalar(stmt_media) or 0

        stmt_content = select(func.count(SystemReview.id)).where(and_(
            SystemReview.entity_type == entity_type,
            SystemReview.entity_id == entity_id,
            SystemReview.status == "APPROVED",
            SystemReview.content != ""
        ))
        content_count = await self.review_repo.session.scalar(stmt_content) or 0

        # 4. Product Sales (Elite V2.2: Marketing Boost Integration)
        order_count = 0
        if entity_type == "PRODUCT":
            from backend.database.models import ProductBase
            from sqlalchemy import select
            stmt_sales = select(ProductBase.order_count, ProductBase.product_metadata).where(ProductBase.id == entity_id)
            p_row = (await self.review_repo.session.execute(stmt_sales)).fetchone()
            if p_row:
                raw_count = p_row.order_count or 0
                metadata = p_row.product_metadata or {}
                
                # Use standard display logic for consistency
                import os
                from datetime import datetime
                try:
                    g_by_count = int(os.getenv("G_BY_COUNT", "0"))
                except:
                    g_by_count = 0
                
                # 🎯 Elite FOMO Logic: Hourly Growth + Unique Product Offset (Consistent with ProductService)
                now = datetime.now()
                hour_factor = now.hour * 2
                min_factor = now.minute // 15
                
                # Unique deterministic offset per product (Same seed as ProductService)
                unique_offset = (abs(hash(str(entity_id))) % 150) * 50
                fomo_boost = hour_factor + min_factor + unique_offset
                
                # Base from metadata + real orders + marketing boost + fomo
                from backend.services.commerce.product import RE_ORDER_COUNT
                base_text = str(metadata.get("reviews_count_text", "0"))
                match = RE_ORDER_COUNT.search(base_text)
                base_num = 0
                if match:
                    clean_num = match.group(1).replace(",", "").replace(".", "")
                    base_num = int(clean_num) if clean_num.isdigit() else 0
                
                order_count = base_num + raw_count + g_by_count + fomo_boost

        return {
            "total_count": total_count,
            "average_rating": round(avg_rating, 1),
            "rating_breakdown": rating_breakdown,
            "has_content_count": content_count,
            "has_media_count": media_count,
            "order_count": order_count
        }

    async def increment_like(self, review_id: str) -> int:
        from sqlalchemy import update, func, select
        stmt = update(SystemReview).where(SystemReview.id == review_id).values(
            likes_count=func.coalesce(SystemReview.likes_count, 0) + 1
        ).returning(SystemReview.likes_count)
        
        res = await self.review_repo.session.execute(stmt)
        new_count = res.scalar()
        return new_count or 0

    async def report_review(self, review_id: str, reason: str) -> None:
        try:
            review = await self.review_repo.get(review_id)
            from backend.database.models.system import Notification
            import uuid
            noti = Notification(
                id=str(uuid.uuid4()),
                type="REPORT",
                message=f"Báo cáo đánh giá {review_id} (Entity: {review.entity_type} {review.entity_id}): {reason}",
                user_id=None # System wide admin notification
            )
            self.review_repo.session.add(noti)
        except NotFoundError:
            raise ValueError(f"Review {review_id} not found")

async def provide_review_service(review_repo: SystemReviewRepository) -> ReviewService:
    return ReviewService(review_repo)
