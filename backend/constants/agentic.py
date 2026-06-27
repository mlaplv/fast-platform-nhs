import os

# R101: Concurrency Limits
ORCHESTRATOR_SEMAPHORE_LIMIT: int = int(os.getenv("ORCHESTRATOR_SEMAPHORE_LIMIT", "3"))

# R82.8: Perception Latency
STEP_ARTIFICIAL_LATENCY_SECONDS: float = float(os.getenv("STEP_ARTIFICIAL_LATENCY_SECONDS", "0.0"))

# R106: HTTP Client Limits
HTTP_MAX_CONNECTIONS: int = 500
HTTP_KEEPALIVE_CONNECTIONS: int = 100
HTTP_TIMEOUT_SECONDS: float = 30.0

# V61.0: Viral Cache Config
CONTENT_CACHE_MAXSIZE: int = 200
CONTENT_CACHE_TTL: int = 60 # 1 minute for hot state

# Campaign Config
MAX_SEARCH_RETRY_PER_STEP: int = 3
SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES: int = 15

# R110: Pure Vietnamese Search Locale (Fast-Platform Elite V2.2)
SEARCH_LOCALE_PARAMS: dict[str, str] = {
    "lr": os.getenv("GOOGLE_SEARCH_LR", "lang_vi"),
    "gl": os.getenv("GOOGLE_SEARCH_GL", "vn"),
    "hl": os.getenv("GOOGLE_SEARCH_HL", "vi"),
    "imgSize": "medium",
}
