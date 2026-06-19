"""v614 - Align JSON to JSONB: migrate remaining JSON columns to JSONB

Revision ID: v614
Revises: v613
Create Date: 2026-06-19

=== PHÂN TÍCH ===
Nhiều cột JSON trong database hiện tại vẫn đang dùng kiểu raw text 'json' mặc dù:
- Một số model (như Order, ProductBase, ProductVariant) đã khai báo kiểu JSONB trong code.
- Kiểu 'jsonb' lưu trữ dạng nhị phân phân rã, giúp tiết kiệm bộ nhớ, tăng tốc độ truy vấn đáng kể (không phải parse lại chuỗi mỗi khi select), và hỗ trợ các hàm jsonb/index tối ưu của PostgreSQL.

MỤC TIÊU:
- Đồng bộ toàn bộ các cột 'json' còn lại trong database sang kiểu 'jsonb' để đạt hiệu suất và nén tốt nhất.
- Đảm bảo cast an toàn bằng cách sử dụng `postgresql_using="column::jsonb"`.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "v614"
down_revision = "v613"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. articles
    op.alter_column("articles", "article_metadata", type_=JSONB, postgresql_using="article_metadata::jsonb", existing_nullable=True)

    # 2. campaign_events
    op.alter_column("campaign_events", "payload", type_=JSONB, postgresql_using="payload::jsonb", existing_nullable=True)

    # 3. content_campaigns
    op.alter_column("content_campaigns", "gold_metadata", type_=JSONB, postgresql_using="gold_metadata::jsonb", existing_nullable=True)
    op.alter_column("content_campaigns", "topic_data", type_=JSONB, postgresql_using="topic_data::jsonb", existing_nullable=True)
    op.alter_column("content_campaigns", "assets_data", type_=JSONB, postgresql_using="assets_data::jsonb", existing_nullable=True)
    op.alter_column("content_campaigns", "outline_data", type_=JSONB, postgresql_using="outline_data::jsonb", existing_nullable=True)

    # 4. content_scouts
    op.alter_column("content_scouts", "report_data", type_=JSONB, postgresql_using="report_data::jsonb", existing_nullable=True)

    # 5. chat_messages
    op.alter_column("chat_messages", "content", type_=JSONB, postgresql_using="content::jsonb", existing_nullable=True)

    # 6. orders
    op.alter_column("orders", "items", type_=JSONB, postgresql_using="items::jsonb", existing_nullable=True)
    op.alter_column("orders", "history", type_=JSONB, postgresql_using="history::jsonb", existing_nullable=True)
    op.alter_column("orders", "order_metadata", type_=JSONB, postgresql_using="order_metadata::jsonb", existing_nullable=True)

    # 7. product_bases
    op.alter_column("product_bases", "images", type_=JSONB, postgresql_using="images::jsonb", existing_nullable=True)
    op.alter_column("product_bases", "attributes", type_=JSONB, postgresql_using="attributes::jsonb", existing_nullable=True)
    op.alter_column("product_bases", "tier_variations", type_=JSONB, postgresql_using="tier_variations::jsonb", existing_nullable=True)

    # 8. product_variants
    op.alter_column("product_variants", "tier_index", type_=JSONB, postgresql_using="tier_index::jsonb", existing_nullable=True)

    # 9. support_knowledge
    op.alter_column("support_knowledge", "tags", type_=JSONB, postgresql_using="tags::jsonb", existing_nullable=True)

    # 10. system_settings
    op.alter_column("system_settings", "value", type_=JSONB, postgresql_using="value::jsonb", existing_nullable=True)

    # 11. voice_profiles
    op.alter_column("voice_profiles", "wake_words", type_=JSONB, postgresql_using="wake_words::jsonb", existing_nullable=True)
    op.alter_column("voice_profiles", "sleep_words", type_=JSONB, postgresql_using="sleep_words::jsonb", existing_nullable=True)
    op.alter_column("voice_profiles", "capabilities", type_=JSONB, postgresql_using="capabilities::jsonb", existing_nullable=True)
    op.alter_column("voice_profiles", "chat_settings", type_=JSONB, postgresql_using="chat_settings::jsonb", existing_nullable=True)
    op.alter_column("voice_profiles", "stt_anchors", type_=JSONB, postgresql_using="stt_anchors::jsonb", existing_nullable=True)
    op.alter_column("voice_profiles", "ai_models", type_=JSONB, postgresql_using="ai_models::jsonb", existing_nullable=True)
    op.alter_column("voice_profiles", "discovered_models", type_=JSONB, postgresql_using="discovered_models::jsonb", existing_nullable=True)

    # 12. unified_agent_tasks
    op.alter_column("unified_agent_tasks", "payload", type_=JSONB, postgresql_using="payload::jsonb", existing_nullable=True)
    op.alter_column("unified_agent_tasks", "result", type_=JSONB, postgresql_using="result::jsonb", existing_nullable=True)

    # 13. users
    op.alter_column("users", "extra_metadata", type_=JSONB, postgresql_using="extra_metadata::jsonb", existing_nullable=True)

    # 14. drafts
    op.alter_column("drafts", "payload", type_=JSONB, postgresql_using="payload::jsonb", existing_nullable=True)

    # 15. appointments
    op.alter_column("appointments", "metadata_json", type_=JSONB, postgresql_using="metadata_json::jsonb", existing_nullable=True)
    op.alter_column("appointments", "recurring_metadata", type_=JSONB, postgresql_using="recurring_metadata::jsonb", existing_nullable=True)


def downgrade() -> None:
    import sqlalchemy as sa

    # 1. articles
    op.alter_column("articles", "article_metadata", type_=sa.JSON(), postgresql_using="article_metadata::json", existing_nullable=True)

    # 2. campaign_events
    op.alter_column("campaign_events", "payload", type_=sa.JSON(), postgresql_using="payload::json", existing_nullable=True)

    # 3. content_campaigns
    op.alter_column("content_campaigns", "gold_metadata", type_=sa.JSON(), postgresql_using="gold_metadata::json", existing_nullable=True)
    op.alter_column("content_campaigns", "topic_data", type_=sa.JSON(), postgresql_using="topic_data::json", existing_nullable=True)
    op.alter_column("content_campaigns", "assets_data", type_=sa.JSON(), postgresql_using="assets_data::json", existing_nullable=True)
    op.alter_column("content_campaigns", "outline_data", type_=sa.JSON(), postgresql_using="outline_data::json", existing_nullable=True)

    # 4. content_scouts
    op.alter_column("content_scouts", "report_data", type_=sa.JSON(), postgresql_using="report_data::json", existing_nullable=True)

    # 5. chat_messages
    op.alter_column("chat_messages", "content", type_=sa.JSON(), postgresql_using="content::json", existing_nullable=True)

    # 6. orders
    op.alter_column("orders", "items", type_=sa.JSON(), postgresql_using="items::json", existing_nullable=True)
    op.alter_column("orders", "history", type_=sa.JSON(), postgresql_using="history::json", existing_nullable=True)
    op.alter_column("orders", "order_metadata", type_=sa.JSON(), postgresql_using="order_metadata::json", existing_nullable=True)

    # 7. product_bases
    op.alter_column("product_bases", "images", type_=sa.JSON(), postgresql_using="images::json", existing_nullable=True)
    op.alter_column("product_bases", "attributes", type_=sa.JSON(), postgresql_using="attributes::json", existing_nullable=True)
    op.alter_column("product_bases", "tier_variations", type_=sa.JSON(), postgresql_using="tier_variations::json", existing_nullable=True)

    # 8. product_variants
    op.alter_column("product_variants", "tier_index", type_=sa.JSON(), postgresql_using="tier_index::json", existing_nullable=True)

    # 9. support_knowledge
    op.alter_column("support_knowledge", "tags", type_=sa.JSON(), postgresql_using="tags::json", existing_nullable=True)

    # 10. system_settings
    op.alter_column("system_settings", "value", type_=sa.JSON(), postgresql_using="value::json", existing_nullable=True)

    # 11. voice_profiles
    op.alter_column("voice_profiles", "wake_words", type_=sa.JSON(), postgresql_using="wake_words::json", existing_nullable=True)
    op.alter_column("voice_profiles", "sleep_words", type_=sa.JSON(), postgresql_using="sleep_words::json", existing_nullable=True)
    op.alter_column("voice_profiles", "capabilities", type_=sa.JSON(), postgresql_using="capabilities::json", existing_nullable=True)
    op.alter_column("voice_profiles", "chat_settings", type_=sa.JSON(), postgresql_using="chat_settings::json", existing_nullable=True)
    op.alter_column("voice_profiles", "stt_anchors", type_=sa.JSON(), postgresql_using="stt_anchors::json", existing_nullable=True)
    op.alter_column("voice_profiles", "ai_models", type_=sa.JSON(), postgresql_using="ai_models::json", existing_nullable=True)
    op.alter_column("voice_profiles", "discovered_models", type_=sa.JSON(), postgresql_using="discovered_models::json", existing_nullable=True)

    # 12. unified_agent_tasks
    op.alter_column("unified_agent_tasks", "payload", type_=sa.JSON(), postgresql_using="payload::json", existing_nullable=True)
    op.alter_column("unified_agent_tasks", "result", type_=sa.JSON(), postgresql_using="result::json", existing_nullable=True)

    # 13. users
    op.alter_column("users", "extra_metadata", type_=sa.JSON(), postgresql_using="extra_metadata::json", existing_nullable=True)

    # 14. drafts
    op.alter_column("drafts", "payload", type_=sa.JSON(), postgresql_using="payload::json", existing_nullable=True)

    # 15. appointments
    op.alter_column("appointments", "metadata_json", type_=sa.JSON(), postgresql_using="metadata_json::json", existing_nullable=True)
    op.alter_column("appointments", "recurring_metadata", type_=sa.JSON(), postgresql_using="recurring_metadata::json", existing_nullable=True)
