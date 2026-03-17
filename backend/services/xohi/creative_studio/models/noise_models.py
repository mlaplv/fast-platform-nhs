from typing import List, Dict
from pydantic import BaseModel, Field, ConfigDict

class NoiseDictionary(BaseModel):
    """
    R105: Static Typing for Hybrid Noise Shield Resources.
    Ensures zero-guesswork during runtime cleaning.
    """
    model_config = ConfigDict(strict=True)
    static_keywords: Dict[str, List[str]] = Field(default_factory=dict)
    fuzzy_patterns: Dict[str, List[str]] = Field(default_factory=dict)
    semantic_categories: List[str] = Field(default_factory=list)
