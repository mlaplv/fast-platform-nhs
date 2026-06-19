"""v616 – Optimize Analytics Database Performance

1. Autovacuum tuning for write-heavy log tables:
   - agent_telemetry_logs, click_fraud_events, audit_logs
   - vacuum_scale_factor = 0.05, analyze_scale_factor = 0.05

2. High-performance composite indexes for analytics queries:
   - ix_atl_tenant_created_duration (agent_telemetry_logs): Index-Only Scan for anomaly detector
   - ix_cfe_created_verdict (click_fraud_events): Time-range verdict aggregation
   - ix_cfe_verdict_created_ip (click_fraud_events): Top offending IPs dashboard

Revision ID: v616
Revises: v615
"""
from alembic import op

revision = "v616"
down_revision = "v615"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Autovacuum tuning ──────────────────────────────────────────────
    op.execute("""
        ALTER TABLE agent_telemetry_logs SET (
            autovacuum_vacuum_scale_factor = 0.05,
            autovacuum_analyze_scale_factor = 0.05
        );
    """)
    op.execute("""
        ALTER TABLE click_fraud_events SET (
            autovacuum_vacuum_scale_factor = 0.05,
            autovacuum_analyze_scale_factor = 0.05
        );
    """)
    op.execute("""
        ALTER TABLE audit_logs SET (
            autovacuum_vacuum_scale_factor = 0.05,
            autovacuum_analyze_scale_factor = 0.05
        );
    """)

    # ── 2. Composite indexes for analytics queries ────────────────────────
    # agent_telemetry_logs: Anomaly detector AVG(duration_ms) WHERE tenant+time
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_atl_tenant_created_duration
        ON agent_telemetry_logs (tenant_id, created_at, duration_ms);
    """)

    # click_fraud_events: Dashboard time-range verdict aggregation + hourly breakdown
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_cfe_created_verdict
        ON click_fraud_events (created_at, verdict);
    """)

    # click_fraud_events: Top offending IPs (Index-Only Scan)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_cfe_verdict_created_ip
        ON click_fraud_events (verdict, created_at, ip_address);
    """)


def downgrade() -> None:
    # ── Drop indexes ──────────────────────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_cfe_verdict_created_ip;")
    op.execute("DROP INDEX IF EXISTS ix_cfe_created_verdict;")
    op.execute("DROP INDEX IF EXISTS ix_atl_tenant_created_duration;")

    # ── Reset autovacuum to defaults ──────────────────────────────────────
    op.execute("ALTER TABLE audit_logs RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor);")
    op.execute("ALTER TABLE click_fraud_events RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor);")
    op.execute("ALTER TABLE agent_telemetry_logs RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor);")
