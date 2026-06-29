from typing import List, Dict, TypedDict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

class FocalPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    x: float = Field(0.5, ge=0.0, le=1.0)
    y: float = Field(0.5, ge=0.0, le=1.0)

class MediaMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    embedding: Optional[List[float]] = None
    ai_tags: List[str] = Field(default_factory=list)
    ai_description: Optional[str] = None
    focal_point: FocalPoint = Field(default_factory=FocalPoint)
    original_source: Optional[str] = None
    sentiment: Optional[str] = None
    analyzed_at: Optional[str] = None

    @field_validator('focal_point', mode='before')
    @classmethod
    def validate_focal_point(cls, v):
        if v is None:
            return FocalPoint()
        return v

class MediaAssetResponse(BaseModel):
    """R105 Strict Typing for Media Asset"""
    model_config = ConfigDict(from_attributes=True, strict=True)
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
    created_at: Optional[str] = None
    is_linked: bool = False
    
    # Legacy - maintained for compatibility
    linked_post_id: Optional[str] = None
    linked_post_type: Optional[str] = None
    
    media_metadata: MediaMetadata = Field(default_factory=MediaMetadata)

    @field_validator("id", "campaign_id", "owner_id", mode="before")
    @classmethod
    def stringify_ids(cls, v):
        if v is None:
            return None
        return str(v)

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, v):
        from datetime import datetime
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else None

class MediaListResponseData(BaseModel):
    model_config = ConfigDict(strict=True)
    items: List[MediaAssetResponse]
    total: int
    limit: int
    offset: int

class MediaListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    data: MediaListResponseData

class MimeTypeBreakdown(BaseModel):
    model_config = ConfigDict(strict=True)
    type: str
    count: int
    size: int

class MediaStatsResponseData(BaseModel):
    model_config = ConfigDict(strict=True)
    total_count: int
    total_size: int
    total_trash_count: int
    breakdown: List[MimeTypeBreakdown]
    storage_provider: str

class MediaStatsResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    data: MediaStatsResponseData

class MediaDetailResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    data: MediaAssetResponse

class MediaUpdateMetadata(BaseModel):
    model_config = ConfigDict(strict=True)
    alt_text: Optional[str] = None
    is_public: Optional[bool] = None
    media_metadata: Optional[MediaMetadata] = None

class QuickEditParams(BaseModel):
    model_config = ConfigDict(strict=True)
    x: Optional[int] = 0
    y: Optional[int] = 0
    w: Optional[int] = None
    h: Optional[int] = None
    preset: Optional[str] = "square"  # 'square', 'banner', etc.
    # Watermark positioning (percentage 0.0 - 1.0)
    logo_enabled: Optional[bool] = True
    logo_x: Optional[float] = None
    logo_y: Optional[float] = None
    logo_scale: Optional[float] = 0.12
    # Text Overlay positioning
    text: Optional[str] = None
    text_x: Optional[float] = None
    text_y: Optional[float] = None
    text_scale: Optional[float] = 0.05
    text_color: Optional[str] = "#FFFFFF"

class QuickEditResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    data: MediaAssetResponse

class BulkDownloadResponseData(BaseModel):
    model_config = ConfigDict(strict=True)
    zip_url: str

class BulkDownloadResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    data: BulkDownloadResponseData

class QuickEditRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    action: str
    params: Optional[QuickEditParams] = None
    source_url: Optional[str] = None # V75: Support on-the-fly registration
    campaign_id: Optional[str] = None # V76: Pass context for AI bypass logic

class BulkDeleteRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ids: List[str]
    permanent: bool = False

class BulkDownloadRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ids: List[str]

class BulkUpdateItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    metadata: MediaUpdateMetadata

class BulkUpdateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    updates: List[BulkUpdateItem]

class FetchRemoteRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    url: str
    campaign_id: Optional[str] = None

class MediaListResult(BaseModel):
    model_config = ConfigDict(strict=True)
    items: List[MediaAssetResponse]
    total: int
    limit: int
    offset: int

class MediaStatsResult(BaseModel):
    model_config = ConfigDict(strict=True)
    total_count: int
    total_size: int
    total_trash_count: int
    breakdown: List[MimeTypeBreakdown]
    storage_provider: str

class AIVisionStatusRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    enabled: bool

class MediaLinkToPostRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    asset_ids: List[str]
    post_id: str
    post_type: str

class CommandAction(TypedDict):
    """Phase 12: Unified Command Dispatch Schema"""
    verb: str  # 'open', 'create', 'edit', 'delete', 'select'
    entity: str  # 'media', 'product', 'category', 'order'
    args: Optional[str]
    metadata: Dict[str, object]
    consumed: Optional[bool]


class GeminiPreviewRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    prompt: str
    aspect_ratio: Optional[str] = "16:9"
    previous_preview_path: Optional[str] = None


class GeminiPreviewResponseData(BaseModel):
    model_config = ConfigDict(strict=True)
    file_path: str
    prompt: str


class GeminiPreviewResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    data: GeminiPreviewResponseData


class GeminiSaveRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    file_path: str
    prompt: str
    campaign_id: Optional[str] = None
