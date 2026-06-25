from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class BasicInfo(BaseModel):
    site_name: str = "SmartShop"
    slogan: str = ""
    subslogan: str = "Làn da trắng mịn không chỉ là vẻ đẹp, đó là sự tự tin và kiêu hãnh của mỗi người phụ nữ."
    description: str = "Mỹ Phẩm Cao Cấp Từ Nhật Bản"
    logo_desktop: Optional[str] = None
    logo_mobile: Optional[str] = None
    favicon: Optional[str] = None

class ContactInfo(BaseModel):
    company_name: str = ""
    tax_id: str = ""
    business_license: str = ""
    phone: str = ""
    hotline: str = ""
    email: str = ""
    address: str = ""
    working_hours: str = ""

class SocialMediaItem(BaseModel):
    platform: str
    url: str
    icon_url: Optional[str] = None

class SeoAnalytics(BaseModel):
    meta_title: str = ""
    meta_description: str = ""
    meta_keywords: str = ""
    google_analytics_id: str = ""
    facebook_pixel_id: str = ""
    google_tag_manager_id: str = ""
    google_search_console_id: str = ""

class GoogleMaps(BaseModel):
    map_iframe: str = ""
    api_key: str = ""

class MaintenanceMode(BaseModel):
    is_enabled: bool = False
    message: str = "Website is under maintenance."

class SupportBotSettings(BaseModel):
    helen_enabled: bool = True
    offline_message: str = "Dược sĩ tư vấn sẽ sớm phản hồi sếp. Vui lòng để lại lời nhắn ạ."
    zalo_integration_enabled: bool = True
    messenger_integration_enabled: bool = True

class ConversionSettings(BaseModel):
    fomo_enabled: bool = True


class EntropySettings(BaseModel):
    """SGE Shield V1.0: Admin config cho AI Footprint Entropy Injector."""
    enabled: bool = True
    # Tone override: None = random ngẫu nhiên, hoặc chọn 1 tone cố định
    tone_override: Optional[str] = None
    # Structure override: None = random ngẫu nhiên
    structure_override: Optional[str] = None
    # Schema mutation: Xác suất drop optional keys (0.0 = không drop, 1.0 = luôn drop)
    schema_drop_probability: float = 0.2
    # Lexical sanitizer: Bật/tắt lọc AI buzzwords
    lexical_sanitizer_enabled: bool = True


class CurrencySettings(BaseModel):
    symbol: str = "₫"
    position: str = "suffix" # "prefix" or "suffix"
    decimal_separator: str = "."
    thousand_separator: str = "."
    show_symbol: bool = True

class AutopilotSettings(BaseModel):
    scan_start_hour: int = Field(default=2, ge=0, le=23)
    scan_end_hour: int = Field(default=4, ge=0, le=23)

class OutboundLinkItem(BaseModel):
    keyword: str
    url: str

class OutboundLinksSettings(BaseModel):
    max_links_per_article: int = 2
    authority_map: List[OutboundLinkItem] = Field(default_factory=lambda: [
        OutboundLinkItem(keyword="Tiến sĩ Kenneth K. Hansraj", url="https://pubmed.ncbi.nlm.nih.gov/25393825/"),
        OutboundLinkItem(keyword="Hiệp hội Placenta Nhật Bản", url="https://www.jpla.jp/english/"),
        OutboundLinkItem(keyword="Miccosmo Japan Laboratory", url="https://www.miccosmo.co.jp/english/"),
        OutboundLinkItem(keyword="chiết xuất nhau thai cừu", url="https://www.jpla.jp/english/"),
        OutboundLinkItem(keyword="nhau thai cừu", url="https://www.jpla.jp/english/"),
        OutboundLinkItem(keyword="ceramide tinh khiết", url="https://pubmed.ncbi.nlm.nih.gov/31840425/"),
        OutboundLinkItem(keyword="dầu hạt jojoba", url="https://pubmed.ncbi.nlm.nih.gov/24442110/"),
        OutboundLinkItem(keyword="Harvard Health Publishing", url="https://www.health.harvard.edu"),
        OutboundLinkItem(keyword="Đại học Y Harvard", url="https://www.health.harvard.edu"),
        OutboundLinkItem(keyword="PubMed", url="https://pubmed.ncbi.nlm.nih.gov/"),
        OutboundLinkItem(keyword="ceramide", url="https://pubmed.ncbi.nlm.nih.gov/31840425/"),
        OutboundLinkItem(keyword="collagen", url="https://pubmed.ncbi.nlm.nih.gov/30681787/"),
    ])

class SystemSettingsPayload(BaseModel):
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    currency: CurrencySettings = Field(default_factory=CurrencySettings)
    social_media: List[SocialMediaItem] = Field(default_factory=list)
    seo_analytics: SeoAnalytics = Field(default_factory=SeoAnalytics)
    google_maps: GoogleMaps = Field(default_factory=GoogleMaps)
    maintenance: MaintenanceMode = Field(default_factory=MaintenanceMode)
    support_bot: SupportBotSettings = Field(default_factory=SupportBotSettings)
    conversions: ConversionSettings = Field(default_factory=ConversionSettings)
    entropy: EntropySettings = Field(default_factory=EntropySettings)
    autopilot: AutopilotSettings = Field(default_factory=AutopilotSettings)
    outbound_links: OutboundLinksSettings = Field(default_factory=OutboundLinksSettings)

class SystemSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    settings: SystemSettingsPayload
