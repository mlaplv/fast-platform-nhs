from datetime import datetime, timezone
from litestar import Controller, post, get, Request
from litestar.di import Provide
from litestar.params import Parameter
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.review import CreateReviewRequest, ReviewResponse, PublicReviewResponse, ReviewStatsResponse
from backend.services.review_service import ReviewService, provide_review_service
from backend.database.repositories import provide_system_review_repo, MediaRegistryRepository, provide_media_repo
from backend.services.media.media_service import media_service
from backend.services.media.schemas import MediaDetailResponse, MediaAssetResponse
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.exceptions import HTTPException

class PublicReviewController(Controller):
    path = "/api/v1/client/reviews"
    tags = ["Client Review"]
    dependencies = {
        "review_repo": Provide(provide_system_review_repo),
        "review_service": Provide(provide_review_service),
        "media_repo": Provide(provide_media_repo),
    }

    @get()
    async def list_reviews(
        self,
        review_service: ReviewService,
        limit: int = Parameter(query="limit", default=20),
        offset: int = Parameter(query="offset", default=0),
        entity_type: str | None = Parameter(query="entity_type", required=False, default=None),
        entity_id: str | None = Parameter(query="entity_id", required=False, default=None),
        rating: int | None = Parameter(query="rating", required=False, default=None),
        has_media: bool | None = Parameter(query="has_media", required=False, default=None)
    ) -> dict:
        # Public listing ONLY allows APPROVED status
        reviews, total = await review_service.get_reviews(
            limit=limit,
            offset=offset,
            entity_type=entity_type,
            entity_id=entity_id,
            status="APPROVED",
            rating=rating,
            has_media=has_media
        )
        return {
            "items": [PublicReviewResponse.model_validate(r).model_dump() for r in reviews],
            "total": total
        }

    @get("/stats")
    async def get_stats(
        self,
        review_service: ReviewService,
        entity_type: str = Parameter(query="entity_type"),
        entity_id: str = Parameter(query="entity_id")
    ) -> ReviewStatsResponse:
        stats = await review_service.get_review_stats(entity_type, entity_id)
        return ReviewStatsResponse(**stats)

    @post(middleware=[RateLimitConfig(rate_limit=("minute", 5)).middleware])
    async def create_review(self, request: Request, data: CreateReviewRequest, review_service: ReviewService, db_session: AsyncSession) -> PublicReviewResponse:
        # [Elite V2.2] Authenticated User Linkage
        user = getattr(request.state, "user", None)
        if user:
            data.customer_name = user.get("name") or data.customer_name
            # If we want to strictly use user info:
            # data.customer_name = user.get("name")
            # data.customer_email = user.get("email")
        
        # [R82] BOT_HONEYPOT: Silent Rejection
        if data.website_url:
            # We return a fake success or just ignore to avoid tipping off the bot
            return PublicReviewResponse(
                id="bot-rejected",
                customer_name=data.customer_name,
                customer_location=data.customer_location,
                rating=data.rating,
                content=data.content,
                created_at=datetime.now(timezone.utc)
            ) 

        # Create review and return response mapping
        review = await review_service.create_review(data)
        await db_session.commit()
        return PublicReviewResponse.model_validate(review)

    @post("/upload", middleware=[RateLimitConfig(rate_limit=("minute", 10)).middleware], status_code=201)
    async def upload_review_media(
        self, 
        request: Request, 
        media_repo: MediaRegistryRepository, 
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART)
    ) -> MediaDetailResponse:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Vui lòng đăng nhập để tải ảnh")
        
        # Elite Military-Grade Size Restrictions
        content_obj = await data.read()
        is_video = data.content_type.startswith("video/")
        size_limit = 20 * 1024 * 1024 if is_video else 5 * 1024 * 1024
        
        if len(content_obj) > size_limit:
            msg = "Video không được vượt quá 20MB" if is_video else "Ảnh không được vượt quá 5MB"
            raise HTTPException(status_code=413, detail=msg)

        asset = await media_service.upload_asset(
            repo=media_repo, 
            file_content=content_obj, 
            filename=data.filename, 
            content_type=data.content_type, 
            owner_id=user.get("sub", user.get("id"))
        )
        if not asset: 
            raise HTTPException(status_code=500, detail="Quy trình xử lý file thất bại")
        return MediaDetailResponse(status="success", data=MediaAssetResponse.model_validate(asset))

    @post("/{review_id:str}/like", middleware=[RateLimitConfig(rate_limit=("minute", 20)).middleware])
    async def like_review(self, review_id: str, review_service: ReviewService, db_session: AsyncSession) -> dict:
        new_count = await review_service.increment_like(review_id)
        await db_session.commit()
        return {"status": "success", "new_count": new_count}

    @post("/{review_id:str}/report", middleware=[RateLimitConfig(rate_limit=("minute", 5)).middleware])
    async def report_review(self, review_id: str, data: dict[str, str], review_service: ReviewService, db_session: AsyncSession) -> dict:
        reason = data.get("reason", "Vi phạm tiêu chuẩn cộng đồng")
        await review_service.report_review(review_id, reason)
        await db_session.commit()
        return {"status": "success"}

