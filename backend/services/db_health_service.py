"""
Database Health Service (SOC Monitor V2.3)
===========================================
Queries SQLAlchemy engine state, in-memory leak/slow stats, and Postgres system views.
Robust fallback for SQLite/non-Postgres engines.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.alchemy_config import _DB_STATS, alchemy_config
from backend.schemas.health import (
    DbPoolStatus,
    DbLeakStats,
    DbSlowQueryStats,
    DbHealthResponse,
    DbLockEntry,
    DbLockPair,
    DbLocksResponse,
    DbBloatEntry,
    DbBloatResponse,
)

logger = logging.getLogger("api-gateway.soc-db")

# Table whitelist for safe VACUUM ANALYZE trigger (no lock)
VACUUM_WHITELIST: set[str] = {
    "unified_agent_tasks",
    "support_chat_history",
    "notifications",
    "seo_contextual_links",
    "system_reviews",
}


class DbHealthService:
    """
    Service to report database pooling, leak detection, locks, and table fragmentation.
    """

    @staticmethod
    def get_pool_status() -> DbPoolStatus:
        engine = alchemy_config.get_engine()
        pool = engine.pool
        pool_type = type(pool).__name__

        # Defaults (e.g., for StaticPool/NullPool in SQLite/tests)
        pool_size = 1
        checkedin = 0
        checkedout = 0
        overflow = 0
        invalid = 0
        pool_timeout = 10.0
        recycle_interval = -1.0

        if pool_type == "QueuePool":
            # Extract QueuePool specific attributes safely
            pool_size = int(getattr(pool, "_size", 12))
            # checkedout is the number of connections in active use
            checkedout = int(getattr(pool, "_checkedout", 0))
            # overflow is active connections above pool_size
            overflow = int(getattr(pool, "_overflow", 0))
            # checkedin is count of idle connections currently in the pool
            try:
                checkedin = int(pool.checkedin())
            except Exception:
                checkedin = pool_size - checkedout
            
            # invalid connection counter
            invalid = int(getattr(pool, "_invalidated", 0))
            pool_timeout = float(getattr(pool, "_timeout", 10.0))
            recycle_interval = float(getattr(pool, "_recycle", 300.0))
        elif pool_type == "StaticPool":
            pool_size = 1
            checkedin = 1 if getattr(pool, "_connection", None) is not None else 0
            checkedout = 1 - checkedin

        return DbPoolStatus(
            pool_size=pool_size,
            checkedin=checkedin,
            checkedout=checkedout,
            overflow=overflow,
            invalid=invalid,
            pool_timeout=pool_timeout,
            recycle_interval=recycle_interval,
        )

    @classmethod
    def get_db_health(cls) -> DbHealthResponse:
        """Combine Pool, Leak Counter, and Slow Query Counter."""
        pool_status = cls.get_pool_status()

        leak_stats = DbLeakStats(
            total_leaks_detected=int(_DB_STATS["leak_count"]),
            last_leak_duration_ms=int(_DB_STATS["last_leak_duration_ms"]),
            last_leak_time=_DB_STATS["last_leak_time"],
        )

        slow_query_stats = DbSlowQueryStats(
            total_slow_queries=int(_DB_STATS["slow_query_count"]),
            last_slow_query_sql=str(_DB_STATS["last_slow_query_sql"]),
            last_slow_query_duration_ms=int(_DB_STATS["last_slow_query_duration_ms"]),
            last_slow_query_time=_DB_STATS["last_slow_query_time"],
        )

        return DbHealthResponse(
            pool=pool_status,
            leaks=leak_stats,
            slow_queries=slow_query_stats,
        )

    @staticmethod
    async def get_active_locks(db_session: AsyncSession) -> DbLocksResponse:
        """
        Query pg_stat_activity to find active transactions, execution duration,
        and potential locking issues (blocking PIDs).
        """
        engine = alchemy_config.get_engine()
        dialect_name = engine.dialect.name

        if dialect_name != "postgresql":
            # Silent fallback for non-Postgres environments (e.g., SQLite dev/test)
            return DbLocksResponse(active_queries=[], blocking_pairs=[])

        # Query 1: Active queries running right now (excluding idling and current connection)
        active_query_stmt = text("""
            SELECT 
                pid, 
                query, 
                state, 
                wait_event_type, 
                wait_event,
                EXTRACT(EPOCH FROM (now() - query_start))::float AS duration_seconds
            FROM pg_stat_activity
            WHERE state != 'idle' 
              AND pid != pg_backend_pid()
            ORDER BY duration_seconds DESC NULLS LAST
            LIMIT 20;
        """)

        # Query 2: Blocked vs Blocking transactions
        blocking_query_stmt = text("""
            SELECT
                blocked.pid AS blocked_pid,
                blocked.query AS blocked_query,
                blocking.pid AS blocking_pid,
                blocking.query AS blocking_query
            FROM pg_stat_activity blocked
            JOIN pg_stat_activity blocking 
                ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
            WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0;
        """)

        active_queries: List[DbLockEntry] = []
        blocking_pairs: List[DbLockPair] = []

        try:
            # Execute active queries list
            res_active = await db_session.execute(active_query_stmt)
            for r in res_active.all():
                active_queries.append(
                    DbLockEntry(
                        pid=int(r[0]),
                        query=str(r[1]),
                        state=str(r[2]),
                        wait_event_type=str(r[3]) if r[3] else None,
                        wait_event=str(r[4]) if r[4] else None,
                        duration_seconds=float(r[5]) if r[5] is not None else None,
                    )
                )

            # Execute blocking detection list
            res_blocking = await db_session.execute(blocking_query_stmt)
            for r in res_blocking.all():
                blocking_pairs.append(
                    DbLockPair(
                        blocked_pid=int(r[0]),
                        blocked_query=str(r[1]),
                        blocking_pid=int(r[2]),
                        blocking_query=str(r[3]),
                    )
                )

        except Exception as e:
            logger.error(f"[DbHealth] Failed to query locks system views: {e}")

        return DbLocksResponse(
            active_queries=active_queries,
            blocking_pairs=blocking_pairs,
        )

    @staticmethod
    async def get_table_bloat(db_session: AsyncSession) -> DbBloatResponse:
        """
        Query pg_stat_user_tables to detect table bloat and fragmentation.
        Returns a list of tables with their size, dead row counts, and ratio.
        """
        engine = alchemy_config.get_engine()
        dialect_name = engine.dialect.name

        if dialect_name != "postgresql":
            return DbBloatResponse(tables=[], total_needs_vacuum=0)

        # Query user tables fragmentation ranking (greater than 1000 live rows)
        bloat_stmt = text("""
            SELECT
                relname AS tablename,
                pg_size_pretty(pg_total_relation_size(quote_ident(relname))) AS total_size,
                n_dead_tup AS dead_rows,
                n_live_tup AS live_rows,
                ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1)::float AS dead_ratio_pct,
                last_vacuum,
                last_autovacuum,
                last_analyze
            FROM pg_stat_user_tables
            WHERE (n_live_tup + n_dead_tup) > 100
            ORDER BY n_dead_tup DESC
            LIMIT 15;
        """)

        tables: List[DbBloatEntry] = []
        total_needs_vacuum = 0

        try:
            res = await db_session.execute(bloat_stmt)
            for r in res.all():
                dead_ratio = float(r[4]) if r[4] is not None else 0.0
                needs_vac = dead_ratio > 10.0 or int(r[2]) > 5000  # >10% dead rows or >5k dead tuples
                if needs_vac:
                    total_needs_vacuum += 1

                tables.append(
                    DbBloatEntry(
                        tablename=str(r[0]),
                        total_size=str(r[1]),
                        dead_rows=int(r[2]),
                        live_rows=int(r[3]),
                        dead_ratio_pct=dead_ratio,
                        last_vacuum=r[5].isoformat() if r[5] else None,
                        last_autovacuum=r[6].isoformat() if r[6] else None,
                        last_analyze=r[7].isoformat() if r[7] else None,
                        needs_vacuum=needs_vac,
                    )
                )
        except Exception as e:
            logger.error(f"[DbHealth] Failed to query table bloat views: {e}")

        return DbBloatResponse(
            tables=tables,
            total_needs_vacuum=total_needs_vacuum,
        )

    @staticmethod
    async def trigger_vacuum(db_session: AsyncSession, tablename: str) -> bool:
        """
        Runs non-locking VACUUM ANALYZE on a whitelisted table.
        Runs in background thread or transaction-free connection block.
        Note: VACUUM cannot be run inside a transaction block in Postgres.
        Therefore, we must execute it using an independent, autocommit connection.
        """
        if tablename not in VACUUM_WHITELIST:
            logger.warning(f"[DbHealth] Blocked VACUUM attempt on non-whitelisted table: {tablename}")
            return False

        engine = alchemy_config.get_engine()
        dialect_name = engine.dialect.name

        if dialect_name != "postgresql":
            # SQLite does VACUUM differently without tables. Just return true.
            return True

        logger.warning(f"[DbHealth] Running VACUUM ANALYZE on whitelisted table: {tablename}")
        
        # Open a completely fresh raw connection to bypass SQLAlchemy's transaction manager
        raw_conn = await engine.raw_connection()
        try:
            # Get underlying asyncpg connection and run statement directly
            # asyncpg connection is wrapped by sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_connection
            asyncpg_conn = raw_conn.driver_connection
            await asyncpg_conn.execute(f"VACUUM ANALYZE {tablename}")
            logger.info(f"[DbHealth] Successfully executed VACUUM ANALYZE on {tablename}")
            return True
        except Exception as e:
            logger.error(f"[DbHealth] Failed to run VACUUM on table {tablename}: {e}")
            return False
        finally:
            await raw_conn.close()


db_health_service = DbHealthService()
