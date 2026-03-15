from typing import List, Dict, TypedDict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class FocalPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    x: float = Field(0.5, ge=0.0, le=1.0)
    y: float = Field(0.5, ge=0.0, le=1.0)

class MediaMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    embedding: Optional[List[float]] = None
    ai_tags: List[str] = Field(default_factory=list)
    ai_description: Optional[str] = None
    focal_point: FocalPoint = Field(default_factory=FocalPoint)
    original_source: Optional[str] = None
    sentiment: Optional[str] = None
    analyzed_at: Optional[str] = None

class MediaAssetResponse(BaseModel):
    """R105 Strict Typing for Media Asset"""
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    dimensions: Optional[str] = None
    blurhash: Optional[str] = None
    alt_text: Optional[str] = None
    is_public: bool
    campaign_id: Optional[str] = None
    owner_id: Optional[str] = None
    created_at: Union[str, float, None] = None # Will be handled by validator if needed, or let Litestar serialize
    media_metadata: MediaMetadata = Field(default_factory=MediaMetadata)

    @classmethod
    def from_orm_model(cls, obj: object) -> "MediaAssetResponse":
        """Custom mapper to handle complex fields like datetime and JSON dicts."""
        from datetime import datetime

        # We handle the attribute access manually if not using from_attributes=True fully
        # or use it to simplify the common cases.
        data = {
            "id": str(getattr(obj, "id")),
            "filename": getattr(obj, "filename"),
            "file_path": getattr(obj, "file_path"),
            "file_size": getattr(obj, "file_size"),
            "mime_type": getattr(obj, "mime_type"),
            "dimensions": getattr(obj, "dimensions"),
            "blurhash": getattr(obj, "blurhash"),
            "alt_text": getattr(obj, "alt_text"),
            "is_public": getattr(obj, "is_public"),
            "campaign_id": str(getattr(obj, "campaign_id")) if getattr(obj, "campaign_id") else None,
            "owner_id": str(getattr(obj, "owner_id")) if getattr(obj, "owner_id") else None,
            "created_at": getattr(obj, "created_at").isoformat() if isinstance(getattr(obj, "created_at"), datetime) else str(getattr(obj, "created_at")),
            "media_metadata": MediaMetadata.model_validate(getattr(obj, "media_metadata") or {})
        }
        return cls.model_validate(data)

class MediaListResponseData(BaseModel):
    items: List[MediaAssetResponse]
    total: int
    limit: int
    offset: int

class MediaListResponse(BaseModel):
    status: str = "success"
    data: MediaListResponseData

class MimeTypeBreakdown(BaseModel):
    type: str
    count: int
    size: int

class MediaStatsResponseData(BaseModel):
    total_count: int
    total_size: int
    breakdown: List[MimeTypeBreakdown]
    storage_provider: str

class MediaStatsResponse(BaseModel):
    status: str = "success"
    data: MediaStatsResponseData

class MediaDetailResponse(BaseModel):
    status: str = "success"
    data: MediaAssetResponse

class MediaUpdateMetadata(BaseModel):
    alt_text: Optional[str] = None
    is_public: Optional[bool] = None
    media_metadata: Optional[MediaMetadata] = None

class QuickEditParams(BaseModel):
    x: Optional[int] = 0
    y: Optional[int] = 0
    w: Optional[int] = None
    h: Optional[int] = None
    preset: Optional[str] = "square"  # 'square', 'banner', etc.

class QuickEditResponse(BaseModel):
    status: str = "success"
    data: MediaAssetResponse

class BulkDownloadResponseData(BaseModel):
    zip_url: str

class BulkDownloadResponse(BaseModel):
    status: str = "success"
    data: BulkDownloadResponseData

class QuickEditRequest(BaseModel):
    action: str
    params: Optional[QuickEditParams] = None

class BulkDeleteRequest(BaseModel):
    ids: List[str]
    permanent: bool = False

class BulkDownloadRequest(BaseModel):
    ids: List[str]

class FetchRemoteRequest(BaseModel):
    url: str
    campaign_id: Optional[str] = None

class MediaListResult(BaseModel):
    items: List[MediaAssetResponse]
    total: int
    limit: int
    offset: int

class MediaStatsResult(BaseModel):
    total_count: int
    total_size: int
    breakdown: List[MimeTypeBreakdown]
    storage_provider: str

class CommandAction(TypedDict):
    """Phase 12: Unified Command Dispatch Schema"""
    verb: str  # 'open', 'create', 'edit', 'delete', 'select'
    entity: str  # 'media', 'product', 'category', 'order'
    args: Optional[str]
    metadata: Dict[str, object]
    consumed: Optional[bool]
