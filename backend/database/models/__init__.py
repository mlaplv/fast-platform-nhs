from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin
from backend.database.models.auth import User, VoiceProfile, Role, Permission, user_roles, role_permissions
from backend.database.models.content import Category, Article, ArticleEmbedding, ContentCampaign, CampaignEvent, Appointment, ContentScout
from backend.database.models.media import MediaRegistry, MediaUsage
from backend.database.models.commerce import Order, ProductBase, ProductVariant, RentalContract, ProductEmbedding
from backend.database.models.system import Draft, Notification, AgentTelemetryLog, ChatMessage, SystemSetting, SystemReview, SupportKnowledge, SupportKnowledgeCategory, UnifiedAgentTask
from backend.database.models.system_otp import SystemOTP
from backend.database.models.promotion import Banner, Voucher, ComboDeal

__all__ = [
    "Base",
    "AuditMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    "User",
    "VoiceProfile",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "Category",
    "Article",
    "ArticleEmbedding",
    "ContentCampaign",
    "CampaignEvent",
    "MediaRegistry",
    "MediaUsage",
    "Order",
    "ProductBase",
    "ProductVariant",
    "RentalContract",
    "ProductEmbedding",
    "Draft",
    "Notification",
    "AgentTelemetryLog",
    "ChatMessage",
    "SystemSetting",
    "Banner",
    "Appointment",
    "ContentScout",
    "SystemReview",
    "SupportKnowledge",
    "SupportKnowledgeCategory",
    "SystemOTP",
    "Voucher",
    "ComboDeal",
    "UnifiedAgentTask",
]
