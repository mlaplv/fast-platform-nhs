from typing import Dict, List
from pydantic import BaseModel, Field


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
    greeting_template: str
    capabilities: List[CapabilityMetadata]

class VoiceSettingsPayload(BaseModel):
    """Payload for updating user voice settings"""
    wake_words: List[str] = Field(description="List of wake words")
    sleep_words: List[str] = Field(description="List of sleep words")
    capabilities: Dict[str, bool] = Field(default_factory=dict, description="Mapped AI capabilities (READ, MUTATE, ANALYZE)")
    greeting_template: str = Field(default="Dạ, em nghe đây sếp {name}.", description="Optional greeting template")
