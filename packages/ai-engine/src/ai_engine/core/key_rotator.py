import os
import random
import logging

logger = logging.getLogger("ai-engine")

class SmartKeyRotator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartKeyRotator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        raw_keys = os.getenv("GEMINI_API_KEY", "")
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        
        if not self.keys:
            logger.error("[SmartKeyRotator] No Gemini API keys found in environment!")
            # Fallback to TIER3_API_KEY if exists (legacy support)
            legacy_key = os.getenv("TIER3_API_KEY")
            if legacy_key:
                self.keys = [legacy_key]

        # 6-CHAMBER SHUFFLE: Randomize the initial order
        random.shuffle(self.keys)
        self.index = 0
        self._initialized = True
        logger.info(f"[SmartKeyRotator] Initialized with {len(self.keys)} keys.")

    def get_next_key(self) -> str:
        if not self.keys:
            return ""
        
        # Round-Robin algorithm
        key = self.keys[self.index % len(self.keys)]
        self.index += 1
        return key

    def get_all_keys(self):
        return self.keys
