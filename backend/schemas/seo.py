"""
SEO Pillar & Cluster — Pydantic Schemas
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ─── Node Schemas ─────────────────────────────────────────────────────────────

class RegisterNodeRequest(BaseModel):
    """Đăng ký một Article hoặc Product vào SEO graph."""
    entity_type: Literal["article", "product", "ARTICLE", "PRODUCT"]
    entity_id: str
    is_pillar: bool = False
    pillar_topic: Optional[str] = None
    node_label: str
    node_slug: str
    node_url: Optional[str] = None
    ai_summary: Optional[str] = None


class UpdateNodeRequest(BaseModel):
    is_pillar: Optional[bool] = None
    pillar_topic: Optional[str] = None
    node_label: Optional[str] = None
    node_url: Optional[str] = None
    ai_summary: Optional[str] = None


class SeoNodeResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    is_pillar: bool
    pillar_topic: Optional[str]
    node_label: str
    node_slug: str
    node_url: Optional[str]
    ai_summary: Optional[str]
    created_at: str
    updated_at: str


# ─── Edge Schemas ─────────────────────────────────────────────────────────────

class CreateEdgeRequest(BaseModel):
    """Tạo edge thủ công giữa hai node."""
    source_node_id: str
    target_node_id: str
    link_type: Literal["pillar_cluster", "related", "manual", "ai_suggested"] = "manual"
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    ai_reasoning: Optional[str] = None
    is_confirmed: bool = True  # manual luôn là confirmed


class CreateBulkEdgeRequest(BaseModel):
    """Tạo nhiều edge thủ công cùng lúc giữa một source node và nhiều target nodes."""
    source_node_id: str
    target_node_ids: List[str]
    link_type: Literal["pillar_cluster", "related", "manual", "ai_suggested"] = "manual"
    is_confirmed: bool = True


class UpdateEdgeRequest(BaseModel):
    """Override edge — dùng khi admin kéo thả node trên graph."""
    source_node_id: Optional[str] = None
    target_node_id: Optional[str] = None
    link_type: Optional[Literal["pillar_cluster", "related", "manual", "ai_suggested"]] = None
    is_confirmed: Optional[bool] = None
    override_by: Optional[str] = None


class SeoEdgeResponse(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    link_type: str
    ai_confidence: Optional[float]
    ai_reasoning: Optional[str]
    is_confirmed: bool
    override_by: Optional[str]


# ─── Graph Payload (Network Graph JSON) ───────────────────────────────────────

class GraphNodeItem(BaseModel):
    """Node item trong force-graph payload."""
    id: str
    entity_type: str
    entity_id: str
    label: str
    slug: str
    url: Optional[str]
    is_pillar: bool
    pillar_topic: Optional[str]
    group: Literal["pillar", "cluster", "unclassified"]
    # force-graph visual properties
    val: int           # Node size — pillar=20, cluster scaled by edge count
    color: str         # Hex color — computed server-side by group
    ai_confidence: Optional[float] = None
    is_confirmed: Optional[bool] = None


class GraphLinkItem(BaseModel):
    """Edge item trong force-graph payload."""
    id: str
    source: str        # source node id
    target: str        # target node id
    link_type: str
    ai_confidence: Optional[float]
    is_confirmed: bool
    curvature: float = 0.2
    # Visual — AI suggested = dashed/highlighted, confirmed = solid
    color: str         # Server-side computed


class SeoGraphResponse(BaseModel):
    """Root payload tương thích force-graph / d3-force."""
    meta: dict
    nodes: List[GraphNodeItem]
    links: List[GraphLinkItem]


# ─── AI Match Request ─────────────────────────────────────────────────────────

class TriggerMatchRequest(BaseModel):
    """Trigger AI matching thủ công cho một entity."""
    entity_type: Literal["article", "product", "ARTICLE", "PRODUCT"]
    entity_id: str


class MatchResultResponse(BaseModel):
    node_id: str
    matched_pillar_id: Optional[str]
    match_tier: Literal["auto", "ai_suggested", "unclassified"]
    ai_confidence: Optional[float]
    ai_reasoning: Optional[str]


# ─── System Toggle ────────────────────────────────────────────────────────────

class SeoSystemToggleRequest(BaseModel):
    """On/off auto-matching trigger."""
    auto_match_on_publish: bool
    nightly_reconciliation: bool


# ─── Contextual Link Schemas (SGE Entity-Contextual Linking) ──────────────────

class ContextualLinkResponse(BaseModel):
    """Response cho từng contextual link suggestion."""
    id: str
    source_article_id: str
    target_node_id: str
    target_url: str
    original_sentence: str
    linked_sentence: str
    anchor_text: str
    matched_entity_type: str
    matched_entity_name: str
    ai_confidence: float
    ai_reasoning: Optional[str]
    sentence_index: int
    status: str
    reviewed_by: Optional[str]
    content_hash: str
    link_rel: Optional[str]
    created_at: str
    # Denormalized Pillar info for UI display
    target_label: Optional[str] = None


class ContextualLinkUpdateRequest(BaseModel):
    """Approve/Reject/Edit một contextual link suggestion."""
    status: Optional[Literal["approved", "rejected"]] = None
    anchor_text: Optional[str] = None  # Admin override anchor text
    link_rel: Optional[str] = None  # nofollow, sponsored, etc.


class ContextualLinkApplyResponse(BaseModel):
    """Response khi apply approved links vào article content."""
    applied_count: int
    article_id: str
    skipped_stale: int  # Số link bị skip vì content_hash không khớp


class ContextualLinkListResponse(BaseModel):
    """Response cho danh sách contextual links của một bài viết."""
    article_id: str
    article_title: str
    content_hash: str
    is_stale: bool  # True nếu article.content đã thay đổi sau lần phân tích cuối
    links: List[ContextualLinkResponse]
    stats: dict  # {pending: N, approved: N, rejected: N, applied: N}
