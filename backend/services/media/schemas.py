from typing import List, Dict, TypedDict, Optional, Union, Any
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

class MediaUpdateMetadata(TypedDict, total=False):
    alt_text: str
    is_public: bool
    media_metadata: Dict[str, object]

class QuickEditParams(TypedDict, total=False):
    x: int
    y: int
    w: int
    h: int
    preset: str  # 'square', 'banner', etc.

class QuickEditResponse(BaseModel):
    status: str = "success"
    data: MediaAssetResponse

class BulkDownloadResponseData(BaseModel):
    zip_url: str

class BulkDownloadResponse(BaseModel):
    status: str = "success"
    data: BulkDownloadResponseData

class CommandAction(TypedDict):
    """Phase 12: Unified Command Dispatch Schema"""
    verb: str  # 'open', 'create', 'edit', 'delete', 'select'
    entity: str  # 'media', 'product', 'category', 'order'
    args: Optional[str]
    metadata: Dict[str, object]
