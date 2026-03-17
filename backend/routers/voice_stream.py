# backend/api/v1/controllers/voice_stream.py
"""
Voice Stream Controller Proxy (Elite V2.2)
Rule 01 compliance: Moved implementation to .voice.core
"""
from .voice.core import stt_websocket

__all__ = ["stt_websocket"]
