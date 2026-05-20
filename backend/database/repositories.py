from sqlalchemy.ext.asyncio import AsyncSession
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from backend.database.models import (
    User, VoiceProfile, Role, Permission, Category, Article, Order,
    ProductBase, ProductVariant, ProductEmbedding,
    ArticleEmbedding, Draft, AgentTelemetryLog, ChatMessage, Notification,
    ContentCampaign, MediaRegistry, MediaUsage, Appointment, ContentScout,
    SupportKnowledge
)
from typing import TypedDict, List, Optional
class UserDict(TypedDict):
    id: str
    roles: List[str]

class UserRepository(SQLAlchemyAsyncRepository[User]):
    model_type = User

class VoiceProfileRepository(SQLAlchemyAsyncRepository[VoiceProfile]):
    model_type = VoiceProfile

class RoleRepository(SQLAlchemyAsyncRepository[Role]):
    model_type = Role

class PermissionRepository(SQLAlchemyAsyncRepository[Permission]):
    model_type = Permission

class CategoryRepository(SQLAlchemyAsyncRepository[Category]):
    model_type = Category

class ArticleRepository(SQLAlchemyAsyncRepository[Article]):
    model_type = Article

class OrderRepository(SQLAlchemyAsyncRepository[Order]):
    model_type = Order

class ProductBaseRepository(SQLAlchemyAsyncRepository[ProductBase]):
    model_type = ProductBase

class ProductVariantRepository(SQLAlchemyAsyncRepository[ProductVariant]):
    model_type = ProductVariant

class ProductEmbeddingRepository(SQLAlchemyAsyncRepository[ProductEmbedding]):
    model_type = ProductEmbedding


class ArticleEmbeddingRepository(SQLAlchemyAsyncRepository[ArticleEmbedding]):
    model_type = ArticleEmbedding

class DraftRepository(SQLAlchemyAsyncRepository[Draft]):
    model_type = Draft

class AgentTelemetryLogRepository(SQLAlchemyAsyncRepository[AgentTelemetryLog]):
    model_type = AgentTelemetryLog

class ChatMessageRepository(SQLAlchemyAsyncRepository[ChatMessage]):
    model_type = ChatMessage

class NotificationRepository(SQLAlchemyAsyncRepository[Notification]):
    model_type = Notification

class ContentCampaignRepository(SQLAlchemyAsyncRepository[ContentCampaign]):
    model_type = ContentCampaign

class MediaRegistryRepository(SQLAlchemyAsyncRepository[MediaRegistry]):
    model_type = MediaRegistry

class MediaUsageRepository(SQLAlchemyAsyncRepository[MediaUsage]):
    model_type = MediaUsage

class AppointmentRepository(SQLAlchemyAsyncRepository[Appointment]):
    model_type = Appointment

    async def list_with_count(self, limit: int = 100, offset: int = 0) -> tuple[list[Appointment], int]:
        """[R102] Core implementation for listing appointments with total count."""
        from sqlalchemy import select, func
        stmt = select(self.model_type).order_by(self.model_type.start_time).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        count_stmt = select(func.count()).select_from(self.model_type)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0
        return items, total

from backend.database.models.system import SystemReview

class ContentScoutRepository(SQLAlchemyAsyncRepository[ContentScout]):
    model_type = ContentScout

class SystemReviewRepository(SQLAlchemyAsyncRepository[SystemReview]):
    model_type = SystemReview

class SupportKnowledgeRepository(SQLAlchemyAsyncRepository[SupportKnowledge]):
    model_type = SupportKnowledge

# ==========================================
# REPOSITORY PROVIDERS (V55.0 DI PATTERN)
# ==========================================

async def provide_user_repo(db_session: AsyncSession) -> UserRepository:
    return UserRepository(session=db_session)

async def provide_role_repo(db_session: AsyncSession) -> RoleRepository:
    return RoleRepository(session=db_session)

async def provide_category_repo(db_session: AsyncSession) -> CategoryRepository:
    return CategoryRepository(session=db_session)

async def provide_product_repo(db_session: AsyncSession) -> ProductBaseRepository:
    return ProductBaseRepository(session=db_session)

async def provide_order_repo(db_session: AsyncSession) -> OrderRepository:
    return OrderRepository(session=db_session)

from litestar import Request
from sqlalchemy import select

async def provide_article_repo(db_session: AsyncSession, request: Request) -> ArticleRepository:
    user: Optional[UserDict] = getattr(request.state, "user", None)
    
    # [Elite V3 ABAC] Global Row-Level Security
    # Nếu không phải SUPER_ADMIN, chỉ thấy bài của mình
    if user and "SUPER_ADMIN" not in user.get("roles", []):
        stmt = select(Article).where(Article.author_id == user.get("id"))
        return ArticleRepository(session=db_session, statement=stmt)
        
    return ArticleRepository(session=db_session)

async def provide_voice_repo(db_session: AsyncSession) -> VoiceProfileRepository:
    return VoiceProfileRepository(session=db_session)

async def provide_chat_repo(db_session: AsyncSession) -> ChatMessageRepository:
    return ChatMessageRepository(session=db_session)

async def provide_telemetry_repo(db_session: AsyncSession) -> AgentTelemetryLogRepository:
    return AgentTelemetryLogRepository(session=db_session)

async def provide_campaign_repo(db_session: AsyncSession, request: Request) -> ContentCampaignRepository:
    user: Optional[UserDict] = getattr(request.state, "user", None)
    
    if user and "SUPER_ADMIN" not in user.get("roles", []):
        stmt = select(ContentCampaign).where(ContentCampaign.user_id == user.get("id"))
        return ContentCampaignRepository(session=db_session, statement=stmt)

    return ContentCampaignRepository(session=db_session)

async def provide_media_repo(db_session: AsyncSession) -> MediaRegistryRepository:
    return MediaRegistryRepository(session=db_session)

async def provide_media_usage_repo(db_session: AsyncSession) -> MediaUsageRepository:
    return MediaUsageRepository(session=db_session)

async def provide_appointment_repo(db_session: AsyncSession) -> AppointmentRepository:
    return AppointmentRepository(session=db_session)

async def provide_scout_repo(db_session: AsyncSession) -> ContentScoutRepository:
    return ContentScoutRepository(session=db_session)

async def provide_system_review_repo(db_session: AsyncSession) -> SystemReviewRepository:
    return SystemReviewRepository(session=db_session)

async def provide_support_kb_repo(db_session: AsyncSession) -> SupportKnowledgeRepository:
    return SupportKnowledgeRepository(session=db_session)
