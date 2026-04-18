from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class BasicInfo(BaseModel):
    site_name: str = "SmartShop"
    description: str = ""
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

class SystemSettingsPayload(BaseModel):
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    social_media: List[SocialMediaItem] = Field(default_factory=list)
    seo_analytics: SeoAnalytics = Field(default_factory=SeoAnalytics)
    google_maps: GoogleMaps = Field(default_factory=GoogleMaps)
    maintenance: MaintenanceMode = Field(default_factory=MaintenanceMode)
    support_bot: SupportBotSettings = Field(default_factory=SupportBotSettings)
    conversions: ConversionSettings = Field(default_factory=ConversionSettings)

class SystemSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    settings: SystemSettingsPayload
