import os
import logging

logger = logging.getLogger("api-gateway")

class SmartKeyRotator:
    """R101/R106: Intelligent Key Management for LLM Tiers."""
    def __init__(self):
        raw_keys = os.getenv("GEMINI_API_KEY", "")
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self.index = 0
        
        if not self.keys:
            logger.warning("[KeyRotator] No GEMINI_API_KEY found in environment!")

    def get_key(self) -> str:
        if not self.keys:
            return ""
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

    def get_count(self) -> int:
        return len(self.keys)
