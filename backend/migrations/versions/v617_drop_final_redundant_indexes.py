"""v617 – Drop 7 remaining redundant single-column indexes

These single-column indexes are fully covered by existing composite/unique indexes:

1. ix_agent_telemetry_logs_tenant_id (tenant_id) → ix_atl_tenant_created_duration(tenant_id, created_at, duration_ms)
2. ix_appointments_start_time (start_time) → ix_appointments_time_range(start_time, ...)
3. ix_articles_tenant_id (tenant_id) → ix_articles_tenant_deleted(tenant_id, deleted_at)
4. ix_click_fraud_events_verdict (verdict) → ix_cfe_verdict_created(verdict, created_at)
5. ix_media_usage_asset_id (asset_id) → ix_media_usage_asset_entity(asset_id, ...)
6. ix_seo_edges_source_node_id (source_node_id) → uq_seo_edge_source_target(source_node_id, target_node_id)
7. ix_seo_nodes_entity_type (entity_type) → uq_seo_node_entity_tenant(entity_type, ...)

Revision ID: v617
Revises: v616
"""
from alembic import op

revision = "v617"
down_revision = "v616"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. agent_telemetry_logs
    op.drop_index("ix_agent_telemetry_logs_tenant_id", table_name="agent_telemetry_logs")

    # 2. appointments
    op.drop_index("ix_appointments_start_time", table_name="appointments")

    # 3. articles
    op.drop_index("ix_articles_tenant_id", table_name="articles")

    # 4. click_fraud_events
    op.drop_index("ix_click_fraud_events_verdict", table_name="click_fraud_events")

    # 5. media_usage
    op.drop_index("ix_media_usage_asset_id", table_name="media_usage")

    # 6. seo_edges
    op.drop_index("ix_seo_edges_source_node_id", table_name="seo_edges")

    # 7. seo_nodes
    op.drop_index("ix_seo_nodes_entity_type", table_name="seo_nodes")


def downgrade() -> None:
    op.create_index("ix_seo_nodes_entity_type", "seo_nodes", ["entity_type"])
    op.create_index("ix_seo_edges_source_node_id", "seo_edges", ["source_node_id"])
    op.create_index("ix_media_usage_asset_id", "media_usage", ["asset_id"])
    op.create_index("ix_click_fraud_events_verdict", "click_fraud_events", ["verdict"])
    op.create_index("ix_articles_tenant_id", "articles", ["tenant_id"])
    op.create_index("ix_appointments_start_time", "appointments", ["start_time"])
    op.create_index("ix_agent_telemetry_logs_tenant_id", "agent_telemetry_logs", ["tenant_id"])
