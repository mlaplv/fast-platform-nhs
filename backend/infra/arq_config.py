import os
from arq.connections import RedisSettings

def get_redis_settings() -> RedisSettings:
    """
    Elite V2.2: Unified Redis Configuration for arq Workers.
    Reuses environment variables from XoHiMemory.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Parse redis_url to arq-compatible RedisSettings
    # Example: redis://:password@localhost:6379/0
    try:
        from urllib.parse import urlparse
        url = urlparse(redis_url)
        return RedisSettings(
            host=url.hostname or "localhost",
            port=url.port or 6379,
            password=url.password,
            database=int(url.path.strip("/") or 0),
            conn_timeout=10,
        )
    except Exception:
        # Fallback to defaults
        return RedisSettings(host="127.0.0.1", port=6379)
