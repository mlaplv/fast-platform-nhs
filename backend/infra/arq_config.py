import os
from arq.connections import RedisSettings

def get_redis_settings() -> RedisSettings:
    """
    Elite V2.2: Unified Redis Configuration for arq Workers.
    Hardened for Docker: Prioritizes 'redis' service name over 'localhost'.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # CNS V82.50: Pre-parsing cleanup for complex env strings
    if redis_url.startswith("'") or redis_url.startswith('"'):
        redis_url = redis_url.strip("'\"")

    try:
        from urllib.parse import urlparse
        # Handle cases where scheme might be missing (e.g. "redis:6379")
        if "://" not in redis_url:
            host_parts = redis_url.split(":")[0]
            host = host_parts if host_parts and host_parts != "localhost" else "redis"
            port = 6379
            password = None
            database = 0
        else:
            url = urlparse(redis_url)
            # FORCE 'redis' hostname if inside Docker and resolved to localhost
            host = url.hostname
            if not host or host == "localhost":
                host = "redis"
            
            port = url.port or 6379
            password = url.password
            database = int(url.path.strip("/") or 0)

        import logging
        logger = logging.getLogger("arq-worker")
        logger.info(f"[Arq Config] Targeting Redis node: {host}:{port} (db={database})")

        return RedisSettings(
            host=host,
            port=port,
            password=password,
            database=database,
            conn_timeout=10,
        )
    except Exception as e:
        # Emergency Fallback to Docker internal standard
        return RedisSettings(host="redis", port=6379)
