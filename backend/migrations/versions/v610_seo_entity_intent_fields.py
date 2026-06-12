"""v610 - Add intent_type and entities_json to seo_nodes for SGE entity-based matching

Revision ID: v610
Revises: v609
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "v610"
down_revision = "v609"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # intent_type: phân loại search intent của node
    # Values: informational_why | informational_how | informational_what | comparison | transactional | pillar | unknown
    op.add_column(
        "seo_nodes",
        sa.Column("intent_type", sa.String(50), nullable=True, server_default=None),
    )

    # entities_json: structured entity list extracted by AI
    # Format: [{"type": "Brand", "name": "Miccosmo", "confidence": 0.95}, ...]
    op.add_column(
        "seo_nodes",
        sa.Column("entities_json", JSONB, nullable=True, server_default=None),
    )

    # pillar_url_override: allow explicit pillar URL for schema linking
    op.add_column(
        "seo_nodes",
        sa.Column("pillar_url_override", sa.String(1000), nullable=True, server_default=None),
    )

    # Index for intent-based filtering
    op.create_index("ix_seo_nodes_intent_type", "seo_nodes", ["intent_type", "tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_seo_nodes_intent_type", table_name="seo_nodes")
    op.drop_column("seo_nodes", "pillar_url_override")
    op.drop_column("seo_nodes", "entities_json")
    op.drop_column("seo_nodes", "intent_type")
