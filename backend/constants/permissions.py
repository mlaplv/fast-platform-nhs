from enum import Enum

class PermissionEnum(str, Enum):
    """
    Elite V2.2 — Centralized Permission Registry.
    Source of truth cho tất cả security clearance tokens trong hệ thống.
    Enum values phải khớp chính xác với cột `code` trong bảng `permissions` (DB).
    """
    # System & Infrastructure
    SYS_ADMIN = "sys:admin"
    
    # Commerce & Catalog
    CATEGORY_READ = "category:read"
    CATEGORY_WRITE = "category:write"
    PRODUCT_READ = "product:read"
    PRODUCT_WRITE = "product:write"
    ORDER_READ = "order:read"
    ORDER_WRITE = "order:write"
    
    # Scheduling
    SCHEDULE_READ = "schedule:read"
    SCHEDULE_MANAGE = "schedule:manage"
    
    # AI & Training
    AI_TRAIN = "ai:train"
    AI_CONFIG = "ai:config"
    
    # Content & Media
    CONTENT_READ = "content:read"
    CONTENT_WRITE = "content:write"
    CONTENT_PUBLISH = "content:publish"
    MEDIA_READ = "media:read"
    MEDIA_WRITE = "media:write"
    
    # User Management
    USER_MANAGE = "user:manage"
    
    @classmethod
    def all_codes(cls) -> list[str]:
        """Trả về tất cả permission codes — dùng cho DB seed và API listing."""
        return [p.value for p in cls]

    @classmethod
    def by_code(cls, code: str) -> "PermissionEnum | None":
        """Lookup an enum member by its string code value."""
        return next((p for p in cls if p.value == code), None)
