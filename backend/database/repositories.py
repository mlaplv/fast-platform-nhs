from sqlalchemy.ext.asyncio import AsyncSession
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from backend.database.models import (
    User, VoiceProfile, Role, Permission, Category, Article, Order,
    ProductBase, ProductVariant, RentalContract, ProductEmbedding,
    ArticleEmbedding, Draft, AgentTelemetryLog, ChatMessage, Notification,
    ContentCampaign, MediaRegistry
)

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

class RentalContractRepository(SQLAlchemyAsyncRepository[RentalContract]):
    model_type = RentalContract

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

async def provide_article_repo(db_session: AsyncSession) -> ArticleRepository:
    return ArticleRepository(session=db_session)

async def provide_voice_repo(db_session: AsyncSession) -> VoiceProfileRepository:
    return VoiceProfileRepository(session=db_session)

async def provide_chat_repo(db_session: AsyncSession) -> ChatMessageRepository:
    return ChatMessageRepository(session=db_session)

async def provide_telemetry_repo(db_session: AsyncSession) -> AgentTelemetryLogRepository:
    return AgentTelemetryLogRepository(session=db_session)

async def provide_campaign_repo(db_session: AsyncSession) -> ContentCampaignRepository:
    return ContentCampaignRepository(session=db_session)

async def provide_media_repo(db_session: AsyncSession) -> MediaRegistryRepository:
    return MediaRegistryRepository(session=db_session)
