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
