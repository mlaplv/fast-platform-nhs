from typing import List, Dict, TypedDict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

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

    @field_validator('focal_point', mode='before')
    @classmethod
    def validate_focal_point(cls, v):
        if v is None:
            return FocalPoint()
        return v

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
    def from_record(cls, obj: Union[object, Dict[str, Any]]) -> "MediaAssetResponse":
        """
        R1.5: Mapping linh hoạt từ DB Record (Dict) hoặc ORM Model (Legacy).
        """
        from datetime import datetime

        def get_val(o, key, default=None):
            if isinstance(o, dict):
                return o.get(key, default)
            return getattr(o, key, default)

        created_at = get_val(obj, "created_at")
        if isinstance(created_at, datetime):
            created_at_str = created_at.isoformat()
        else:
            created_at_str = str(created_at) if created_at else None

        meta_raw = get_val(obj, "media_metadata", {})
        if isinstance(meta_raw, str):
            import json
            try:
                meta_dict = json.loads(meta_raw)
            except:
                meta_dict = {}
        else:
            meta_dict = meta_raw or {}

        data = {
            "id": str(get_val(obj, "id")),
            "filename": get_val(obj, "filename"),
            "file_path": get_val(obj, "file_path"),
            "file_size": get_val(obj, "file_size"),
            "mime_type": get_val(obj, "mime_type"),
            "dimensions": get_val(obj, "dimensions"),
            "blurhash": get_val(obj, "blurhash"),
            "alt_text": get_val(obj, "alt_text"),
            "is_public": bool(get_val(obj, "is_public")),
            "campaign_id": str(get_val(obj, "campaign_id")) if get_val(obj, "campaign_id") else None,
            "owner_id": str(get_val(obj, "owner_id")) if get_val(obj, "owner_id") else None,
            "created_at": created_at_str,
            "media_metadata": MediaMetadata.model_validate(meta_dict)
        }
        return cls.model_validate(data)

    @classmethod
    def from_orm_model(cls, obj: object) -> "MediaAssetResponse":
        """Legacy Alias."""
        return cls.from_record(obj)

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
    source_url: Optional[str] = None # V75: Support on-the-fly registration

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
