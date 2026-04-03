import os
import json
import logging
from typing import List, Any

logger = logging.getLogger("api-gateway")

def get_env_json(key: str, default: List[Any] = None) -> List[Any]:
    """
    Elite V2.2: Safe JSON parsing for Environment Variables (SSOT).
    Supports arrays of keys/CXs for rotation.
    """
    val = os.getenv(key)
    if not val:
        return default or []
    
    try:
        # Handle JSON format: '["key1", "key2"]'
        if val.startswith("[") and val.endswith("]"):
            return json.loads(val)
        
        # Handle legacy comma-separated format: 'key1, key2'
        return [k.strip() for k in val.split(",") if k.strip()]
    except Exception as e:
        logger.error(f"[Config] Failed to parse JSON env {key}: {e}")
        return default or []
