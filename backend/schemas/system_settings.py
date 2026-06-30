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


class SeoContextualLinksSettings(BaseModel):
    """Cấu hình bộ lọc link ngữ cảnh SEO/SGE."""
    auto_linking_enabled: bool = Field(default=False)
    brand_keywords: List[str] = Field(default_factory=lambda: [
        "miccosmo", "beppin", "white label", "hurry harry", 
        "virgin white", "oklab", "reborn", "placenta", "virgin",
        "hurry", "harry", "formulan", "phytorise", "rose healing",
        "apto", "meishoku", "detclear", "ceracolla", "organic rose",
        "pintup", "limerence", "osmo", "naris"
    ])
    generic_exclusions: List[str] = Field(default_factory=lambda: [
        # Vietnamese common stop words & product types
        "kem", "serum", "gel", "sữa rửa mặt", "sữa tắm", "nước hoa hồng", "mặt nạ", "kem dưỡng", "dưỡng da",
        "làm dịu", "cấp ẩm", "trị thâm", "ngừa lão hóa", "chăm sóc da", "tẩy tế bào chết", "nhạy cảm",
        "chính hãng", "nhập khẩu", "giá rẻ", "an toàn", "hiệu quả", "dưỡng ẩm", "dưỡng trắng",
        "chống nắng", "trị mụn", "giảm thâm", "se khít", "làm sạch", "tẩy trang", "dưỡng thể", "dưỡng tóc",
        # English generic terms & product types
        "essence", "cream", "soap", "lotion", "toner", "cleanser", "sunscreen",
        "white", "label", "premium", "body", "face", "skin", "hair", "wash", "oil", "mask",
        "natural", "perfect", "special", "rich", "gold", "clear", "clean", "scrub", "pack",
        "moisturizer", "moisturizing", "whitening", "brightening", "antiaging", "repair", "soothing",
        "care", "exfoliator", "exfoliating", "ml", "g", "gr"
    ])
    intent_keywords: List[str] = Field(default_factory=lambda: [
        "dùng", "sử dụng", "thoa", "bôi", "uống", "khắc phục", "điều trị", "chữa", 
        "cải thiện", "chăm sóc", "phục hồi", "tái tạo", "ngăn ngừa", "bảo vệ", "giảm", "trị",
        "rửa", "sạch", "dịu", "tẩy", "đắp", "thấm", "thẩm thấu"
    ])
    

class NewsTagSettings(BaseModel):
    """Cấu hình ánh xạ từ khóa cho các tag/chủ đề hot của tin tức."""
    tags_map: dict[str, List[str]] = Field(default_factory=lambda: {
        "DƯỠNG DA": ["skin", "aging", "cleansing", "hydration", "da", "dưỡng", "rửa", "cổ"],
        "CẢM HỨNG": ["inspiration", "story", "cảm hứng", "hành trình", "chia sẻ", "lối sống"],
        "XU HƯỚNG": ["trend", "strategies", "future", "xu hướng", "2026", "mới", "lão hóa"],
        "ƯU ĐÃI": ["deal", "discount", "voucher", "ưu đãi", "khuyến mãi", "quà"],
        "MẸO HAY": ["tips", "fundamentals", "how to", "mẹo", "hướng dẫn", "nguyên tắc", "cách"],
        "SỨC KHỎE": ["health", "healthy", "sức khỏe", "lão hóa", "dinh dưỡng"]
    })


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
    seo_contextual_links: SeoContextualLinksSettings = Field(default_factory=SeoContextualLinksSettings)
    news_tags: NewsTagSettings = Field(default_factory=NewsTagSettings)

class SystemSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    settings: SystemSettingsPayload

