from typing import List, Dict, TypedDict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, AliasGenerator
from pydantic.alias_generators import to_camel

# Elite V2.2: Standardized Config for Zero-Hydration & CamelCase
ELITE_CONFIG = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    alias_generator=AliasGenerator(
        serialization_alias=to_camel,
    )
)

class FocalPoint(BaseModel):
    model_config = ELITE_CONFIG
    x: float = Field(0.5, ge=0.0, le=1.0)
    y: float = Field(0.5, ge=0.0, le=1.0)

class MediaMetadata(BaseModel):
    model_config = ELITE_CONFIG
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
    """Elite V2.2: Strict Typing & CamelCase for Media Asset"""
    model_config = ELITE_CONFIG
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
    created_at: Union[str, float, None] = None
    media_metadata: MediaMetadata = Field(default_factory=MediaMetadata)

    @classmethod
    def from_record(cls, obj: Union[object, Dict[str, object]]) -> "MediaAssetResponse":
        """
        Mapping linh hoạt từ DB Record (Dict) hoặc ORM Model (Legacy).
        Đảm bảo giữ snake_case đầu vào, Pydantic sẽ lo phần alias đầu ra.
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

        # Trả về dict với keys gốc (snake_case), Pydantic sẽ tự serialize sang camelCase
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

class MediaListResponseData(BaseModel):
    model_config = ELITE_CONFIG
    items: List[MediaAssetResponse]
    total: int
    limit: int
    offset: int

class MediaListResponse(BaseModel):
    model_config = ELITE_CONFIG
    status: str = "success"
    data: MediaListResponseData

class MimeTypeBreakdown(BaseModel):
    model_config = ELITE_CONFIG
    type: str
    count: int
    size: int

class MediaStatsResponseData(BaseModel):
    model_config = ELITE_CONFIG
    total_count: int
    total_size: int
    breakdown: List[MimeTypeBreakdown]
    storage_provider: str

class MediaStatsResponse(BaseModel):
    model_config = ELITE_CONFIG
    status: str = "success"
    data: MediaStatsResponseData

class MediaDetailResponse(BaseModel):
    model_config = ELITE_CONFIG
    status: str = "success"
    data: MediaAssetResponse

class MediaUpdateMetadata(BaseModel):
    model_config = ELITE_CONFIG
    alt_text: Optional[str] = None
    is_public: Optional[bool] = None
    media_metadata: Optional[MediaMetadata] = None

class QuickEditParams(BaseModel):
    model_config = ELITE_CONFIG
    x: Optional[int] = 0
    y: Optional[int] = 0
    w: Optional[int] = None
    h: Optional[int] = None
    preset: Optional[str] = "square"

class QuickEditResponse(BaseModel):
    model_config = ELITE_CONFIG
    status: str = "success"
    data: MediaAssetResponse

class BulkDownloadResponseData(BaseModel):
    model_config = ELITE_CONFIG
    zip_url: str

class BulkDownloadResponse(BaseModel):
    model_config = ELITE_CONFIG
    status: str = "success"
    data: BulkDownloadResponseData

class QuickEditRequest(BaseModel):
    model_config = ELITE_CONFIG
    action: str
    params: Optional[QuickEditParams] = None
    source_url: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    model_config = ELITE_CONFIG
    ids: List[str]
    permanent: bool = False

class BulkDownloadRequest(BaseModel):
    model_config = ELITE_CONFIG
    ids: List[str]

class FetchRemoteRequest(BaseModel):
    model_config = ELITE_CONFIG
    url: str
    campaign_id: Optional[str] = None

class MediaListResult(BaseModel):
    model_config = ELITE_CONFIG
    items: List[MediaAssetResponse]
    total: int
    limit: int
    offset: int

class MediaStatsResult(BaseModel):
    model_config = ELITE_CONFIG
    total_count: int
    total_size: int
    breakdown: List[MimeTypeBreakdown]
    storage_provider: str

class CommandAction(TypedDict):
    verb: str
    entity: str
    args: Optional[str]
    metadata: Dict[str, object]
    consumed: Optional[bool]
