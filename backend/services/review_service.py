import random
from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.filters import LimitOffset
from backend.utils.uid import new_id

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

    async def _sync_product_rating(self, entity_type: str, entity_id: str) -> None:
        """Write-through: Recompute avg rating từ APPROVED reviews và ghi vào product_metadata.
        Đảm bảo product listing API luôn trả đúng reviews_trust_score mà không cần N+1 join.
        """
        if entity_type != "PRODUCT":
            return
        try:
            from sqlalchemy import select, func, and_, update
            from sqlalchemy.orm.attributes import flag_modified
            from backend.database.models import ProductBase

            # 1. Tính avg + count của APPROVED reviews
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
            total_count: int = row.total if row else 0
            avg_rating: float = round(float(row.avg), 1) if (row and row.avg) else 0.0

            # 2. Load product
            p_stmt = select(ProductBase).where(ProductBase.id == entity_id)
            product = (await self.review_repo.session.execute(p_stmt)).scalar_one_or_none()
            if not product:
                return

            # 3. Ghi vào product_metadata — chỉ set khi có ít nhất 1 review
            if not product.product_metadata:
                product.product_metadata = {}
            if total_count > 0:
                product.product_metadata["reviews_trust_score"] = avg_rating
                product.product_metadata["review_count"] = total_count
            else:
                # Xoá field nếu không còn review nào approved
                product.product_metadata.pop("reviews_trust_score", None)
                product.product_metadata.pop("review_count", None)

            flag_modified(product, "product_metadata")
            await self.review_repo.session.flush()
        except Exception as exc:
            import logging
            logging.getLogger("api-gateway").warning(
                f"[ReviewService._sync_product_rating] Non-blocking failure for {entity_id}: {exc}"
            )

    async def update_status(self, review_id: str, data: UpdateReviewStatusRequest) -> SystemReview:
        try:
            review = await self.review_repo.get(review_id)
            old_status = review.status
            review.status = data.status

            # 1. Ghi dữ liệu review cập nhật status xuống DB
            updated = await self.review_repo.update(review)

            # 2. Write-Through: cập nhật product_metadata trong cùng transaction
            await self._sync_product_rating(review.entity_type, review.entity_id)

            # 3. BẮT BUỘC CHỦ ĐỘNG COMMIT để tránh Race Condition với Worker ngầm (arq)
            await self.review_repo.session.commit()

            # 4. Chỉ khi dữ liệu đã commit 100% vật lý mới enqueue background job sinh Knowledge Graph
            if data.status == "APPROVED" and old_status != "APPROVED":
                try:
                    from backend.infra.arq_config import get_redis_settings
                    from arq import create_pool
                    
                    redis_pool = await create_pool(get_redis_settings())
                    try:
                        await redis_pool.enqueue_job("generate_review_kg_job", str(review.id), _queue_name="high")
                        logging.getLogger("api-gateway").info(f"🧬 [ReviewService] Enqueued background KG generation for review {review.id}")
                    finally:
                        # [P0-FIX] Đóng pool ngay sau khi enqueue để giải phóng kết nối Redis
                        # Tránh HTTP request của DB session bị treo khi pool chưa đóng
                        await redis_pool.aclose()
                except Exception as e:
                    # Non-blocking failure for KG generation enqueue
                    import logging
                    logging.getLogger("api-gateway").error(f"❌ [ReviewService] Failed to enqueue KG generation job: {e}")

            return updated
        except NotFoundError:
            raise ValueError(f"Review {review_id} not found")

    async def update_content(self, review_id: str, data: UpdateReviewRequest) -> SystemReview:
        try:
            review = await self.review_repo.get(review_id)
            
            # Elite V2.2: Universal Field Update
            if data.content is not None:
                review.content = data.content
            if data.rating is not None:
                review.rating = data.rating
            if data.customer_name is not None:
                review.customer_name = data.customer_name
            if data.customer_phone is not None:
                review.customer_phone = data.customer_phone
            if data.customer_location is not None:
                review.customer_location = data.customer_location
            if data.entity_type is not None:
                review.entity_type = data.entity_type
            if data.entity_id is not None:
                review.entity_id = data.entity_id
            
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

            updated = await self.review_repo.update(review)

            # Write-Through: nếu rating thay đổi, recompute product avg_rating
            await self._sync_product_rating(review.entity_type, review.entity_id)

            return updated
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

            # Write-Through: sau khi xoá, recompute product avg_rating
            await self._sync_product_rating(review.entity_type, review.entity_id)
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
            noti = Notification(
                id=new_id(),
                type="REPORT",
                message=f"Báo cáo đánh giá {review_id} (Entity: {review.entity_type} {review.entity_id}): {reason}",
                user_id=None # System wide admin notification
            )
            self.review_repo.session.add(noti)
        except NotFoundError:
            raise ValueError(f"Review {review_id} not found")

    async def ai_seed_one(self, entity_type: str, entity_id: str) -> SystemReview:
        """
        Xohi Review Lab: Tạo 1 đánh giá chất lượng cao bằng AI.
        - Phong cách: ngẫu nhiên (tiktok / shopee / lazada / authentic)
        - Bypass anti-spam: không check duplicate
        - Extensible: thêm NEWS/CATEGORY chỉ cần thêm branch load entity
        """
        import uuid
        import logging
        from pydantic_ai import Agent
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        logger = logging.getLogger("api-gateway")

        # --- 1. Load entity context (Extensible architecture) ---
        entity_name = ""
        entity_desc = ""
        entity_attrs: dict[str, object] = {}

        if entity_type == "PRODUCT":
            from sqlalchemy import select
            from backend.database.models import ProductBase
            stmt = select(
                ProductBase.name,
                ProductBase.short_description,
                ProductBase.product_metadata
            ).where(ProductBase.id == entity_id)
            row = (await self.review_repo.session.execute(stmt)).fetchone()
            if not row:
                raise ValueError(f"Product {entity_id} not found")
            entity_name = row.name or ""
            entity_desc = row.short_description or ""
            entity_attrs = (row.product_metadata or {}).get("attributes", {})
        elif entity_type == "NEWS":
            from sqlalchemy import select
            from backend.database.models.content import Article
            stmt = select(
                Article.title,
                Article.excerpt
            ).where(Article.id == entity_id)
            row = (await self.review_repo.session.execute(stmt)).fetchone()
            if not row:
                raise ValueError(f"News article {entity_id} not found")
            entity_name = row.title or ""
            entity_desc = row.excerpt or ""
        elif entity_type == "CATEGORY":
            from sqlalchemy import select, text
            row = (await self.review_repo.session.execute(
                text("SELECT name, description FROM categories WHERE id = :id"),
                {"id": entity_id}
            )).fetchone()
            if not row:
                raise ValueError(f"Category {entity_id} not found")
            entity_name = row.name or ""
            entity_desc = row.description or ""
        else:
            raise ValueError(f"Unsupported entity_type: {entity_type}")

        # --- 2. Random style — backend chọn, UI không cần control ---
        style = random.choice(["tiktok", "shopee", "lazada", "authentic"])

        # --- 3. Random Vietnamese profile ---
        vn_names = [
            "Nguyễn Thị Lan", "Trần Thị Mai", "Lê Thị Hương", "Phạm Thị Ngọc",
            "Hoàng Thị Linh", "Võ Thị Thu", "Bùi Thị Hà", "Trương Thị Dung",
            "Nguyễn Văn An", "Trần Văn Bình", "Lê Văn Cường", "Phạm Văn Duy",
            "Hoàng Văn Em", "Võ Văn Phúc", "Nguyễn Thị Thu Hương", "Đặng Thị Kim Oanh",
            "Phan Thị Thanh Thảo", "Đỗ Thị Bích Ngọc", "Lưu Thị Minh Tuyết", "Cao Thị Lan Anh",
            "Vũ Thị Hồng Hạnh", "Tạ Thị Kim Dung", "Nguyễn Thị Thanh Loan", "Trịnh Thị Lé",
        ]
        vn_locations = [
            "TP.HCM", "Hà Nội", "Đà Nẵng", "Cần Thơ", "Hải Phòng",
            "Nha Trang", "Huế", "Vũng Tàu", "Biên Hòa", "Bình Dương",
            "Long An", "Tiền Giang", "Bến Tre", "Quảng Ngãi", "Quảng Nam",
            "Thành phố Thủ Đức", "Quận 7", "Quận Bình Thạnh", "Hóc Môn", "Tân Bình",
        ]
        customer_name = random.choice(vn_names)
        customer_location = random.choice(vn_locations)

        # --- 4. Rating distribution realistic (5★ xác suất cao) ---
        rating_pool = [5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 3]
        rating = random.choice(rating_pool)

        # --- 5. Style-specific prompt instructions & System prompts ---
        if entity_type == "NEWS":
            style_instructions = {
                "tiktok": (
                    "Phong cách TikTok (độc giả trẻ): cực kỳ ngắn gọn (dưới 20 từ, tối đa 100 ký tự), "
                    "đưa 1-2 emoji tự nhiên, giọng trẻ trung/Gen Z. VD: '✨ thông tin hữu ích ghê, đúng cái mình đang tìm kiếm luôn'"
                ),
                "shopee": (
                    "Phong cách bình luận chia sẻ: trung bình 20-30 từ, chia sẻ ngắn gọn về trải nghiệm thực tế "
                    "hoặc thói quen liên quan đến bài viết. VD: 'Mình từng thử đổi thói quen như bài viết và thấy đỡ hẳn.'"
                ),
                "lazada": (
                    "Phong cách khách quan: khoảng 25-35 từ, nhận xét về tính thực tế hoặc giá trị kiến thức "
                    "mà bài viết mang lại. VD: 'Bài viết phân tích rất chi tiết và khoa học, giúp mình hiểu rõ nguyên nhân.'"
                ),
                "authentic": (
                    "Phong cách tự nhiên: bình luận cực kỳ ngắn gọn như comment dạo trên mạng xã hội, "
                    "giọng văn chân thực, không trang trọng. VD: 'bài viết hay quá, lưu lại để áp dụng mới được'"
                ),
            }
            context_lines = [f"Tiêu đề bài viết: {entity_name}"]
            if entity_desc:
                context_lines.append(f"Tóm tắt bài viết: {entity_desc[:200]}")
            context_lines.append(f"Số sao đánh giá bài viết: {rating}/5")
            content_foundation = "\n".join(context_lines)

            system_prompt = f"""Bạn là một độc giả Việt Nam vừa đọc xong bài viết tin tức.
Nhiệm vụ: Viết ĐÚNG 1 CÂU BÌNH LUẬN/ĐÁNH GIÁ chân thực, không hoa mỹ về bài viết này.
{style_instructions[style]}
CHỈ THỊ QUAN TRỌNG:
1. BÁM SÁT TIÊU ĐỀ BÀI VIẾT trong câu một cách tự nhiên (không bắt buộc bê nguyên xi cả tiêu đề dài dòng, chỉ cần đề cập ý chính hoặc tên chủ đề bài viết).
2. Các câu bắt buộc phải là một câu hoàn chỉnh về mặt ngữ nghĩa (Có đầy đủ chủ ngữ + vị ngữ).
3. Tuyệt đối không được ngắt dòng khi chưa viết hết câu.
4. Hãy chủ động viết ngắn gọn ngay từ đầu (TỐI ĐA 30 từ, dưới 140 ký tự).
5. Chỉ trả về ĐÚNG 1 CÂU bình luận duy nhất, không thêm bất kỳ văn bản giải thích nào khác."""

        elif entity_type == "CATEGORY":
            style_instructions = {
                "tiktok": (
                    "Phong cách TikTok Shop: cực kỳ ngắn gọn (dưới 20 từ, tối đa 100 ký tự), đưa 1-2 emoji tự nhiên, "
                    "giọng Gen Z/trẻ trung. VD: '✨ danh mục này nhiều món xinh xỉu, săn sale mỏi tay luôn'"
                ),
                "shopee": (
                    "Phong cách Shopee: trung bình 25-35 từ, chia sẻ cảm nhận về sự phong phú của danh mục sản phẩm này."
                ),
                "lazada": (
                    "Phong cách Lazada: chuyên nghiệp hơn, khoảng 30-40 từ, đánh giá độ đa dạng, mức giá sản phẩm."
                ),
                "authentic": (
                    "Phong cách tự nhiên: bình luận ngắn gọn, chân thực như khách mua hàng bình thường."
                ),
            }
            context_lines = [f"Tên danh mục sản phẩm: {entity_name}"]
            if entity_desc:
                context_lines.append(f"Mô tả danh mục: {entity_desc[:200]}")
            context_lines.append(f"Số sao đánh giá: {rating}/5")
            content_foundation = "\n".join(context_lines)

            system_prompt = f"""Bạn là một khách hàng Việt Nam vừa trải nghiệm mua sắm các sản phẩm thuộc danh mục sản phẩm này.
Nhiệm vụ: Viết ĐÚNG 1 CÂU ĐÁNH GIÁ chân thực, không hoa mỹ.
{style_instructions[style]}
CHỈ THỊ QUAN TRỌNG:
1. BÁM SÁT TÊN DANH MỤC trong câu một cách tự nhiên.
2. Các câu bắt buộc phải là một câu hoàn chỉnh về mặt ngữ nghĩa (Có đầy đủ chủ ngữ + vị ngữ).
3. Tuyệt đối không được ngắt dòng khi chưa viết hết câu.
4. Hãy chủ động viết ngắn gọn ngay từ đầu (TỐI ĐA 30 từ, dưới 140 ký tự).
5. Chỉ trả về ĐÚNG 1 CÂU duy nhất, không thêm bất kỳ văn bản giải thích nào khác."""

        else: # PRODUCT
            style_instructions = {
                "tiktok": (
                    "Phong cách TikTok Shop: rất ngắn (tối đa 20 từ), đưa 1-2 emoji tự nhiên, "
                    "giọng Gen Z/trẻ trung, không quá trang trọng. VD: '✨ món này xịt lắm, da mình mịn hờ'"
                ),
                "shopee": (
                    "Phong cách Shopee: trung bình 25-35 từ, chân thực như user thật, "
                    "có đề cập 1 chi tiết cụ thể (mùi hương, cảm giác, vỏ hộp, tốc độ giao hàng)."
                ),
                "lazada": (
                    "Phong cách Lazada: chuyên nghiệp hơn, khoảng 30-40 từ, "
                    "có nhận xét kỹ thuật (chất liệu, công nghệ, hiệu quả rõ ràng)."
                ),
                "authentic": (
                    "Phong cách tự nhiên: viết như nhắn tin thực tế, "
                    "không theo form cở nào, có thể có typo nhỏ, ngắn gọn và chân thực nhất."
                ),
            }
            context_lines = [f"Tên sản phẩm: {entity_name}"]
            if entity_desc:
                context_lines.append(f"Mô tả: {entity_desc[:200]}")
            if entity_attrs:
                attrs_text = ", ".join(f"{k}: {v}" for k, v in list(entity_attrs.items())[:5])
                context_lines.append(f"Thuộc tính: {attrs_text}")
            context_lines.append(f"Số sao đánh giá: {rating}/5")
            content_foundation = "\n".join(context_lines)

            system_prompt = f"""Bạn là một khách hàng Việt Nam vừa mua và dùng xong sản phẩm.
Nhiệm vụ: Viết ĐÚNG 1 CÂU ĐÁNH GIÁ chân thực, không phản cảm, không hoa mỹ.
{style_instructions[style]}
CHỈ THỊ QUAN TRỌNG:
1. BÁM SÁT TÊN SẢN PHẨM trong câu.
2. Các câu bắt buộc phải là một câu hoàn chỉnh về mặt ngữ nghĩa (Có đầy đủ chủ ngữ + vị ngữ).
3. Tuyệt đối không được ngắt dòng khi chưa viết hết câu.
4. Hãy chủ động viết ngắn gọn ngay từ đầu (TỐI ĐA 30 từ, dưới 140 ký tự).
5. Đa dạng hóa: không lặp cấu trúc "Sản phẩm tốt, thấm nhanh...".
6. Chỉ trả về ĐÚNG 1 CÂU duy nhất, không thêm bất kỳ văn bản giải thích nào khác."""

        prompt = f"Dữ liệu: {content_foundation}"

        # --- 7. Call LLM qua trinity_bridge ---
        agent = Agent(output_type=str, retries=2)
        try:
            response = await trinity_bridge.run(
                agent,
                prompt,
                system_prompt=system_prompt,
                role="lite",
                timeout=30.0,
                safety_none=True,
                model_settings={"max_tokens": 300, "thinking": False},
            )
            content_raw = str(getattr(response, "data", response)).strip()
            # Sanitize: bỏ quote dư và xử lý newline
            content_raw = content_raw.strip('"\' \n').split('\n')[0][:500]
        except Exception as exc:
            logger.error(f"[ReviewService.ai_seed_one] LLM failed: {exc}")
            raise ValueError(f"AI không thể tạo nội dung: {exc}")

        # --- 8. Insert SystemReview APPROVED — bypass duplicate check ---
        review = SystemReview(
            id=new_id(),
            entity_type=entity_type,  # type: ignore[arg-type]
            entity_id=entity_id,
            customer_name=customer_name,
            customer_phone=None,
            customer_location=customer_location,
            rating=rating,
            content=content_raw,
            status="APPROVED",
            attributes={"style": style, "ai_seeded": True},
        )
        result = await self.review_repo.add(review)

        # Write-Through: AI seed tạo review APPROVED → cập nhật product_metadata
        await self._sync_product_rating(entity_type, entity_id)

        return result


async def provide_review_service(review_repo: SystemReviewRepository) -> ReviewService:
    return ReviewService(review_repo)
