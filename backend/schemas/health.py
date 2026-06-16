from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class HealthStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    system: str = "Fast-Platform Gateway"
    status: str = "online"

class AnomalyItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    type: str
    message: str
    time: str

class AnomalyResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    count: int
    anomalies: List[AnomalyItem]

# --- SOC Monitor Schemas V2.3 ---

class MonitorControlRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    enable: bool
    auto_disable_minutes: int = 60

class MonitorStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    enabled: bool
    enabled_at: Optional[str]
    active_connections: int
    auto_disable_minutes: int

class ConnectionRegistryItem(BaseModel):
    model_config = ConfigDict(strict=True)
    session_id: str
    conn_type: str
    path: str
    ip: str
    user_agent: str
    connected_at: str
    last_ping_at: str
    age_seconds: int

class ConnectionListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    count: int
    connections: List[ConnectionRegistryItem]

class DbPoolStatus(BaseModel):
    model_config = ConfigDict(strict=True)
    pool_size: int
    checkedin: int
    checkedout: int
    overflow: int
    invalid: int
    pool_timeout: float
    recycle_interval: float

class DbLeakStats(BaseModel):
    model_config = ConfigDict(strict=True)
    total_leaks_detected: int
    last_leak_duration_ms: int
    last_leak_time: Optional[str]

class DbSlowQueryStats(BaseModel):
    model_config = ConfigDict(strict=True)
    total_slow_queries: int
    last_slow_query_sql: str
    last_slow_query_duration_ms: int
    last_slow_query_time: Optional[str]

class DbHealthResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    pool: DbPoolStatus
    leaks: DbLeakStats
    slow_queries: DbSlowQueryStats

class DbLockEntry(BaseModel):
    model_config = ConfigDict(strict=True)
    pid: int
    query: str
    state: str
    wait_event_type: Optional[str]
    wait_event: Optional[str]
    duration_seconds: Optional[float]

class DbLockPair(BaseModel):
    model_config = ConfigDict(strict=True)
    blocked_pid: int
    blocked_query: str
    blocking_pid: int
    blocking_query: str

class DbLocksResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    active_queries: List[DbLockEntry]
    blocking_pairs: List[DbLockPair]

class DbBloatEntry(BaseModel):
    model_config = ConfigDict(strict=True)
    tablename: str
    total_size: str
    dead_rows: int
    live_rows: int
    dead_ratio_pct: float
    last_vacuum: Optional[str]
    last_autovacuum: Optional[str]
    last_analyze: Optional[str]
    needs_vacuum: bool

class DbBloatResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    tables: List[DbBloatEntry]
    total_needs_vacuum: int

class SystemSnapshotResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    ram_process_rss_mb: float
    ram_vps_total_mb: float
    ram_vps_used_mb: float
    ram_vps_used_percent: float
    cpu_percent: float
    db_pool_checkedout: int
    redis_used_memory_mb: float
    redis_maxmemory_mb: float
    redis_peak_memory_mb: float
    event_bus_subscribers: int
    sse_connections_count: int

class LiveHealthControlRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    enable: bool
    duration_minutes: int = 30

class LiveHealthControlResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    enabled: bool
    expires_at: Optional[str]

class VacuumRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    table: str


