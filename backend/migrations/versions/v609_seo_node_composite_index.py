"""v609 - Add composite index to seo_nodes for faster entity lookups

Revision ID: v609
Revises: v608
Create Date: 2026-06-12
"""
from alembic import op

revision = "v609"
down_revision = "b9a7eec0272c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index for the most common query pattern:
    # register_node and match_entity both query by (entity_type, entity_id, tenant_id)
    op.create_index(
        "ix_seo_nodes_entity_tenant",
        "seo_nodes",
        ["entity_type", "entity_id", "tenant_id"],
        unique=False,
    )

    # Index for pillar-only queries (used by _get_active_pillars on every match)
    op.create_index(
        "ix_seo_nodes_pillar_tenant",
        "seo_nodes",
        ["is_pillar", "tenant_id"],
        postgresql_where="deleted_at IS NULL",
    )

    # Index on seo_edges for edge lookups by node (source + target are queried separately)
    op.create_index(
        "ix_seo_edges_source",
        "seo_edges",
        ["source_node_id"],
    )
    op.create_index(
        "ix_seo_edges_target",
        "seo_edges",
        ["target_node_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_seo_edges_target", table_name="seo_edges")
    op.drop_index("ix_seo_edges_source", table_name="seo_edges")
    op.drop_index("ix_seo_nodes_pillar_tenant", table_name="seo_nodes")
    op.drop_index("ix_seo_nodes_entity_tenant", table_name="seo_nodes")
