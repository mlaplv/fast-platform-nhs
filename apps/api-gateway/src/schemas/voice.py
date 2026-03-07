from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from src.constants.voice import DEFAULT_GREETING, DEFAULT_FAREWELL

class VoiceResponse(BaseModel):
    """Response from voice processing pipeline"""
    audio_url: str = Field(default="", description="URL to generated TTS audio file")
    text: str = Field(description="Clean text response (VoiceSanitizer output)")
    transcript: str = Field(description="Original STT transcript from audio")
    ui_action: str = Field(default="", description="Widget action: show_revenue_chart, etc.")
    data: Dict[str, object] = Field(default_factory=dict, description="Payload for UI widget")

class CapabilityMetadata(BaseModel):
    id: str
    name: str
    desc: str
    active: bool = False
    color: str = "text-gray-400"
    icon: str = "Brain"

class VoiceSettingsResponse(BaseModel):
    wake_words: List[str]
    sleep_words: List[str]
    greeting_template: str = Field(default=DEFAULT_GREETING)
    farewell_template: str = Field(default=DEFAULT_FAREWELL)
    is_campaign_mode: bool = Field(default=False)
    capabilities: List[CapabilityMetadata]
    chat_settings: Dict[str, object] = Field(default_factory=dict)

class VoiceSettingsPayload(BaseModel):
    """Payload for updating user voice settings"""
    wake_words: List[str] = Field(default_factory=list, description="List of wake words")
    sleep_words: List[str] = Field(default_factory=list, description="List of sleep words")
    capabilities: Dict[str, bool] = Field(default_factory=dict, description="Mapped AI capabilities (READ, MUTATE, ANALYZE)")
    greeting_template: str = Field(default=DEFAULT_GREETING, description="Optional greeting template")
    farewell_template: str = Field(default=DEFAULT_FAREWELL, description="Optional farewell template")
    is_campaign_mode: Optional[bool] = Field(default=None, description="Global Campaign Mode toggle")
    chat_settings: Optional[Dict[str, object]] = Field(default=None, description="Advanced chat persistence settings")

class CampaignModePayload(BaseModel):
    """Payload for global campaign mode toggle"""
    is_campaign_mode: bool = Field(description="Enable Ad Campaign Fortress Mode")

class LexiconOverridePayload(BaseModel):
    wrong_word: str = Field(description="The misspelled or misheard word")
    right_word: str = Field(description="The correct target word")

class LexiconStopwordPayload(BaseModel):
    word: str = Field(description="The filler word to strip out")
