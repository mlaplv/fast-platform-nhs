from typing import List, Dict, TypedDict, Optional, Union
from pydantic import BaseModel, Field

class MediaMetadata(TypedDict, total=False):
    embedding: Optional[List[float]]
    ai_tags: List[str]
    ai_description: str
    focal_point: Dict[str, float]  # {'x': 0.5, 'y': 0.5}
    original_source: str
    sentiment: str

class MediaAssetResponse(BaseModel):
    """R105 Strict Typing for Media Asset"""
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
    created_at: str
    media_metadata: Dict[str, object] = Field(default_factory=dict)

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
    media_metadata: Optional[Dict[str, object]] = None

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
    items: List[Any] # List[MediaRegistry] - Registry instances (Elite R105: Any cast required at router)
    total: int
    limit: int
    offset: int

class MediaStatsResult(BaseModel):
    total_count: int
    total_size: int
    breakdown: List[Dict[str, Any]]
    storage_provider: str

class CommandAction(TypedDict):
    """Phase 12: Unified Command Dispatch Schema"""
    verb: str  # 'open', 'create', 'edit', 'delete', 'select'
    entity: str  # 'media', 'product', 'category', 'order'
    args: Optional[str]
    metadata: Dict[str, object]
    consumed: Optional[bool]
