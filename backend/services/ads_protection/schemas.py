"""
Ads Protection Schemas — Pydantic V2
Đảm bảo ép kiểu tĩnh 100%, không dùng 'any'.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IPReport(BaseModel):
    ip: str
    is_datacenter: bool
    is_vpn: bool
    is_tor: bool
    is_proxy: bool
    country: str
    org: str
    abuse_score: float  # 0.0 → 1.0
    fraud_score: float  # 0.0 → 1.0


class FraudSignal(BaseModel):
    name: str
    triggered: bool
    weight: float
    description: str


class ClickEvent(BaseModel):
    """Payload từ client-side script."""
    gclid: Optional[str] = None
    campaign_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    keyword: Optional[str] = None

    ip_address: str
    user_agent: str
    referrer: Optional[str] = None
    landing_url: str

    session_duration_ms: int = Field(default=0, ge=0)
    scroll_depth_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    mouse_events_count: int = Field(default=0, ge=0)
    touch_events_count: int = Field(default=0, ge=0)
    key_events_count: int = Field(default=0, ge=0)

    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    plugins_count: Optional[int] = None
    webdriver_detected: bool = False
    cookie_enabled: bool = True


class ClickFraudResult(BaseModel):
    gclid: Optional[str]
    ip_address: str
    fraud_score: float
    verdict: str  # "CLEAN" | "SUSPICIOUS" | "FRAUD"
    signals: list[FraudSignal]
    ip_report: IPReport
    timestamp: datetime
    session_fingerprint: str


class FraudSummaryTotals(BaseModel):
    all_clicks: int
    fraud: int
    suspicious: int
    clean: int
    fraud_rate_pct: float
    suspected_rate_pct: float
    
    # Google Ads API Data (Unified 2026)
    google_all_clicks: int = 0
    google_invalid_clicks: int = 0


class FraudBudgetInfo(BaseModel):
    avg_cpc_vnd: float
    estimated_wasted_vnd: float
    estimated_wasted_usd: float
    
    # Google Ads API Data (Unified 2026)
    google_estimated_wasted_vnd: float = 0.0


class OffendingIP(BaseModel):
    ip: str
    click_count: int


class HourlyFraudStat(BaseModel):
    hour: datetime
    fraud_rate: float
    total_clicks: int


class FraudSummary(BaseModel):
    period_hours: int
    generated_at: datetime
    totals: FraudSummaryTotals
    budget: FraudBudgetInfo
    top_offending_ips: list[OffendingIP]
    hourly_breakdown: list[HourlyFraudStat]
    insights: list[OptimizationInsight] = []


class OptimizationInsight(BaseModel):
    type: str
    priority: str
    title: str
    detail: str
    action: str
    estimated_saving_pct: float


class InvestigationReportRequest(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    avg_cpc_vnd: float = 5000.0
    force: bool = False


class InvestigationReportResult(BaseModel):
    status: str
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    total_fraud_clicks: Optional[int] = None
    estimated_wasted_vnd: Optional[float] = None
    csv_path: Optional[str] = None
    support_message_preview: Optional[str] = None


class GoogleInvalidClickMetric(BaseModel):
    campaign_name: str
    clicks: int = 0
    invalid_clicks: int = 0
    invalid_click_rate: float = 0.0
    cost_vnd: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CAMPAIGN MANAGER SCHEMAS — Google Ads API v24
# ─────────────────────────────────────────────────────────────────────────────

class CampaignBudget(BaseModel):
    """Ngân sách chiến dịch (đơn vị: VNĐ/ngày)."""
    daily_budget_vnd: float = Field(ge=10_000, description="Ngân sách ngày tối thiểu 10,000₫")
    delivery_method: str = Field(default="STANDARD", pattern="^(STANDARD|ACCELERATED)$")


class CampaignCreateRequest(BaseModel):
    """Payload tạo chiến dịch mới."""
    name: str = Field(min_length=3, max_length=128)
    budget: CampaignBudget
    bidding_strategy: str = Field(
        default="MAXIMIZE_CLICKS",
        pattern="^(MAXIMIZE_CLICKS|TARGET_CPA|TARGET_ROAS|MANUAL_CPC|MAXIMIZE_CONVERSIONS)$"
    )
    target_cpa_vnd: Optional[float] = Field(default=None, ge=1_000)
    target_roas: Optional[float] = Field(default=None, ge=0.01)
    start_date: str = Field(description="YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM-DD — để trống = không giới hạn")
    # Geo targeting
    geo_target_country: str = Field(default="VN")
    geo_target_cities: list[str] = Field(default_factory=list)
    # Language
    language_code: str = Field(default="vi")
    # Networks
    search_network: bool = True
    display_network: bool = False


class AdGroupCreateRequest(BaseModel):
    """Payload tạo Ad Group."""
    campaign_resource_name: str = Field(description="customers/{id}/campaigns/{id}")
    name: str = Field(min_length=3, max_length=128)
    cpc_bid_vnd: float = Field(ge=500, description="CPC tối thiểu 500₫")
    keywords: list[str] = Field(min_length=1, max_length=20)
    match_types: list[str] = Field(
        default_factory=lambda: ["EXACT"],
        description="BROAD | PHRASE | EXACT"
    )


class ResponsiveSearchAdCreate(BaseModel):
    """Payload tạo Responsive Search Ad."""
    ad_group_resource_name: str
    headlines: list[str] = Field(min_length=3, max_length=15, description="3-15 headlines, mỗi cái ≤ 30 ký tự")
    descriptions: list[str] = Field(min_length=2, max_length=4, description="2-4 descriptions, mỗi cái ≤ 90 ký tự")
    final_url: str = Field(description="Landing page URL - phải là HTTPS")
    display_path1: Optional[str] = Field(default=None, max_length=15)
    display_path2: Optional[str] = Field(default=None, max_length=15)
    call_to_action: Optional[str] = None


class CampaignStatusUpdate(BaseModel):
    """Thay đổi trạng thái campaign."""
    status: str = Field(pattern="^(ENABLED|PAUSED|REMOVED)$")
    reason: Optional[str] = Field(default=None, max_length=256)


class CampaignBudgetUpdate(BaseModel):
    """Cập nhật ngân sách."""
    daily_budget_vnd: float = Field(ge=10_000)


# ─── Response Models ──────────────────────────────────────────────────────────

class PolicyViolation(BaseModel):
    """Một vi phạm chính sách Google được phát hiện."""
    field: str           # "headline[0]" | "description[1]" | "final_url" ...
    rule: str            # tên rule (e.g. "HEADLINE_TOO_LONG")
    severity: str        # "ERROR" | "WARNING"
    message: str         # Mô tả vi phạm
    suggestion: str      # Gợi ý sửa chữa


class PolicyCheckResult(BaseModel):
    """Kết quả kiểm tra chính sách."""
    is_compliant: bool
    violations: list[PolicyViolation]
    score: float = Field(ge=0.0, le=100.0, description="Điểm tuân thủ 0-100")
    checked_rules: int


class CampaignInfo(BaseModel):
    """Thông tin campaign từ Google Ads API."""
    resource_name: str
    id: str
    name: str
    status: str
    daily_budget_vnd: float
    bidding_strategy: str
    start_date: str
    end_date: Optional[str]
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    avg_cpc_vnd: float = 0.0
    cost_vnd: float = 0.0
    conversions: float = 0.0
    policy_status: str = "ELIGIBLE"  # ELIGIBLE | LIMITED | DISAPPROVED
    landing_page_url: Optional[str] = None


class AdGroupInfo(BaseModel):
    """Thông tin Ad Group."""
    resource_name: str
    id: str
    name: str
    status: str
    cpc_bid_vnd: float
    impressions: int = 0
    clicks: int = 0
    cost_vnd: float = 0.0


class AdInfo(BaseModel):
    """Thông tin Ad."""
    resource_name: str
    id: str
    type: str
    status: str
    headlines: list[str]
    descriptions: list[str]
    final_url: str
    policy_summary: str = "ELIGIBLE"


class KeywordSuggestion(BaseModel):
    """Gợi ý từ khóa từ Keyword Planner."""
    keyword: str
    avg_monthly_searches: Optional[int]
    competition: str   # LOW | MEDIUM | HIGH
    avg_cpc_vnd: Optional[float]
    suggested_bid_vnd: Optional[float]


class CampaignOperationResult(BaseModel):
    """Kết quả thao tác trên campaign."""
    success: bool
    resource_name: Optional[str] = None
    operation: str   # "CREATE" | "UPDATE" | "REMOVE"
    message: str
    policy_check: Optional[PolicyCheckResult] = None


# ─────────────────────────────────────────────────────────────────────────────
# AI STRATEGIST SCHEMAS (Xohi Engine)
# ─────────────────────────────────────────────────────────────────────────────

class AISuggestionRequest(BaseModel):
    """Yêu cầu gợi ý từ AI."""
    task: str  # "CAMPAIGN" | "RSA" | "NEGATIVE_KEYWORDS"
    context: str # Nội dung mô tả sản phẩm/mục tiêu của Sếp


class AISuggestionResponse(BaseModel):
    """Kết quả gợi ý từ AI Chiến lược."""
    success: bool
    message: str
    
    # Dữ liệu gợi ý tùy theo task
    campaign_name: Optional[str] = None
    daily_budget_vnd: Optional[float] = None
    bidding_strategy: Optional[str] = None
    
    headlines: Optional[list[str]] = None
    descriptions: Optional[list[str]] = None
    
    negative_keywords: Optional[list[str]] = None
    
    competitor_analysis: Optional[str] = None  # Tóm tắt phân tích đối thủ
    policy_compliance_note: Optional[str] = None # Lưu ý về luật Google 2026

    # Neural Audit Scores (v2.6)
    seo_score: Optional[float] = None
    sge_score: Optional[float] = None
    quality_score: Optional[float] = None
