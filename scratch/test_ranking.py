import asyncio
import os
import sys
import logging

# Add workspace to path
sys.path.append("/app")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

from backend.services.ai_engine.core.trinity_models import TrinityModels
from backend.services.ai_engine.core.key_rotator import key_rotator

async def test():
    # Mocking rotator for sync scoring test
    tm = TrinityModels(rotator=key_rotator, default_model="gemini-1.5-flash", fallback_model="gemini-1.5-flash")
    
    test_models = [
        "gemini-1.5-flash",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-3.1-pro",
        "gemini-2.0-flash"
    ]
    
    print("--- MODEL RANKING (AFTER ELITE V2.2 PRIORITIZATION) ---")
    results = []
    for m in test_models:
        score = tm._score_model_sync(m)
        results.append((m, score))
    
    # Sort by score
    results.sort(key=lambda x: x[1], reverse=True)
    
    for m, s in results:
        print(f"Model: {m:<25} | Score: {s}")

if __name__ == "__main__":
    asyncio.run(test())
