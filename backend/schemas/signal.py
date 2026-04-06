"""
CNS Signal Schema (V70.0)
Single Source of Truth for system-wide signal definition.
Follows R105: Strict Schema Isolation.
"""
from enum import Enum
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, ConfigDict


class SignalSeverity(str, Enum):
    """
    Severity Level determines the Voice + UI modality automatically.
    CRITICAL = Interrupt Voice + Toast (Red)
    ACTION   = Patient Voice + Toast (Yellow) + Bell
    PROGRESS = Silent Ping only
    INFO     = Silent, Bell count only
    """
    CRITICAL = "CRITICAL"
    ACTION = "ACTION"
    PROGRESS = "PROGRESS"
    INFO = "INFO"


class SignalSchema(BaseModel):
    """Unified signal contract for all system notifications."""
    model_config = ConfigDict(strict=True)

    message: str
    severity: SignalSeverity
    signal_type: str = "SYSTEM"      # e.g. SYSTEM, SECURITY, CONTENT_PROGRESS
    payload: Optional[Dict[str, object]] = None
    persist: Optional[bool] = None  # Elite V2.2: If None, CRITICAL/ACTION persist:True, INFO/PROGRESS persist:False.
