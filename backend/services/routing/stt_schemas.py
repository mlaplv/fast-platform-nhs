from typing import Dict, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict

@dataclass
class STTCorrectorDeps:
    """Dependencies for STT Corrector."""
    user_dictionary: Dict[str, str] = field(default_factory=dict)

class STTCorrectionItem(BaseModel):
    model_config = ConfigDict(strict=True)
    wrong_word: str = Field(description="The misspelled or misheard word exactly as it appeared in the input transcript.")
    right_word: str = Field(description="The correct target word.")

class STTCorrectionOutput(BaseModel):
    model_config = ConfigDict(strict=True)
    cleaned_text: str = Field(description="The corrected transcript. If no correction is needed, return the original.")
    suspected_correction: Optional[List[STTCorrectionItem]] = Field(
        default=None, 
        description="If you made a correction that is NOT in the user's dictionary and you are not 100% sure, return a list of correction pairs."
    )
