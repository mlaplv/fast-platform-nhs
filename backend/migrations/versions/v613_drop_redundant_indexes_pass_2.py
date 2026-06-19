"""v613 - Second pass DB index audit: drop 21 redundant/duplicate indexes across 19 tables

Revision ID: v613
Revises: v612
Create Date: 2026-06-19

=== PHÂN TÍCH TOÀN BỘ DB (PASS 2) ===

Mục tiêu: Loại bỏ các index đơn lẻ bị bao phủ hoàn toàn bởi composite index (hoặc composite index khác hiệu quả hơn) và các index trùng lặp 100%.

Bảng chi tiết các index cần drop:

1. click_fraud_events (8 indexes → 6 indexes)
   - ix_click_fraud_events_gclid (gclid) → TRÙNG LẶP với ix_cfe_gclid
   - ix_click_fraud_events_ip_address (ip_address) → Bị bao phủ bởi ix_cfe_ip_created(ip_address, created_at)

2. content_scouts (4 indexes → 3 indexes)
   - ix_content_scouts_tenant_id (tenant_id) → Bị bao phủ bởi ix_scouts_tenant_topic(tenant_id, topic)

3. media_usage (6 indexes → 5 indexes)
   - ix_media_usage_entity_type (entity_type) → Bị bao phủ bởi ix_media_usage_lookup(entity_type, entity_id)

4. product_bases (9 indexes → 8 indexes)
   - ix_product_bases_tenant_id (tenant_id) → Bị bao phủ bởi ix_products_tenant_deleted(tenant_id, deleted_at)

5. audit_logs (7 indexes → 5 indexes)
   - ix_audit_logs_actor_id (actor_id) → Bị bao phủ bởi ix_audit_logs_actor_time(actor_id, created_at)
   - ix_audit_logs_target_table (target_table) → Bị bao phủ bởi ix_audit_logs_target(target_table, target_id)

6. banners (3 indexes → 2 indexes)
   - ix_banners_tenant_id (tenant_id) → Bị bao phủ bởi ix_banners_tenant_active_order(tenant_id, is_active, deleted_at, order_index)

7. campaign_events (4 indexes → 3 indexes)
   - ix_campaign_events_tenant (tenant_id) → TRÙNG LẶP với ix_campaign_events_tenant_id

8. commission_ledger (7 indexes → 5 indexes)
   - ix_commission_ledger_affiliate_id (affiliate_id) → Bị bao phủ bởi ix_commission_ledger_aff_status(affiliate_id, status)
   - ix_commission_ledger_tenant_id (tenant_id) → Bị bao phủ bởi ix_commission_ledger_tenant_status(tenant_id, status)

9. commission_tiers (4 indexes → 3 indexes)
   - ix_commission_tiers_tenant_id (tenant_id) → Bị bao phủ bởi ix_commission_tiers_tenant_deleted(tenant_id, deleted_at)

10. appointments (5 indexes → 4 indexes)
    - ix_appointments_tenant_id (tenant_id) → Bị bao phủ bởi ix_appointments_tenant_deleted(tenant_id, deleted_at)

11. affiliate_profiles (4 indexes → 3 indexes)
    - ix_affiliate_profiles_tenant_id (tenant_id) → Bị bao phủ bởi ix_affiliate_profiles_tenant_deleted(tenant_id, deleted_at)

12. categories (4 indexes → 3 indexes)
    - ix_categories_tenant_id (tenant_id) → Bị bao phủ bởi ix_categories_tenant_deleted(tenant_id, deleted_at)

13. content_campaigns (5 indexes → 4 indexes)
    - ix_content_campaigns_tenant_id (tenant_id) → Bị bao phủ bởi ix_campaigns_tenant_deleted(tenant_id, deleted_at)

14. google_ads_campaign_logs (3 indexes → 2 indexes)
    - ix_google_ads_campaign_logs_campaign_id (campaign_id) → Bị bao phủ bởi ix_gacl_campaign_created(campaign_id, created_at)

15. notifications (4 indexes → 3 indexes)
    - ix_notifications_tenant_id (tenant_id) → Bị bao phủ bởi ix_notifications_tenant_deleted(tenant_id, deleted_at)

16. orders (8 indexes → 7 indexes)
    - ix_orders_tenant_id (tenant_id) → Bị bao phủ bởi ix_orders_tenant_deleted(tenant_id, deleted_at)

17. point_transactions (5 indexes → 4 indexes)
    - ix_point_transactions_tenant_id (tenant_id) → Bị bao phủ bởi ix_point_tx_tenant_user_time(tenant_id, user_id, created_at)

18. system_otps (5 indexes → 4 indexes)
    - ix_system_otps_identifier (identifier) → Bị bao phủ bởi ix_sys_otp_identifier_token(identifier, token)

19. unified_agent_tasks (8 indexes → 6 indexes)
    - ix_unified_agent_tasks_agent_id (agent_id) → Bị bao phủ bởi ix_unified_task_agent_status(agent_id, status)
    - ix_unified_agent_tasks_tenant_id (tenant_id) → Bị bao phủ bởi ix_unified_task_tenant_status(tenant_id, status)
"""
from alembic import op

revision = "v613"
down_revision = "v612"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. click_fraud_events
    op.drop_index("ix_click_fraud_events_gclid", table_name="click_fraud_events")
    op.drop_index("ix_click_fraud_events_ip_address", table_name="click_fraud_events")

    # 2. content_scouts
    op.drop_index("ix_content_scouts_tenant_id", table_name="content_scouts")

    # 3. media_usage
    op.drop_index("ix_media_usage_entity_type", table_name="media_usage")

    # 4. product_bases
    op.drop_index("ix_product_bases_tenant_id", table_name="product_bases")

    # 5. audit_logs
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target_table", table_name="audit_logs")

    # 6. banners
    op.drop_index("ix_banners_tenant_id", table_name="banners")

    # 7. campaign_events
    op.drop_index("ix_campaign_events_tenant", table_name="campaign_events")

    # 8. commission_ledger
    op.drop_index("ix_commission_ledger_affiliate_id", table_name="commission_ledger")
    op.drop_index("ix_commission_ledger_tenant_id", table_name="commission_ledger")

    # 9. commission_tiers
    op.drop_index("ix_commission_tiers_tenant_id", table_name="commission_tiers")

    # 10. appointments
    op.drop_index("ix_appointments_tenant_id", table_name="appointments")

    # 11. affiliate_profiles
    op.drop_index("ix_affiliate_profiles_tenant_id", table_name="affiliate_profiles")

    # 12. categories
    op.drop_index("ix_categories_tenant_id", table_name="categories")

    # 13. content_campaigns
    op.drop_index("ix_content_campaigns_tenant_id", table_name="content_campaigns")

    # 14. google_ads_campaign_logs
    op.drop_index("ix_google_ads_campaign_logs_campaign_id", table_name="google_ads_campaign_logs")

    # 15. notifications
    op.drop_index("ix_notifications_tenant_id", table_name="notifications")

    # 16. orders
    op.drop_index("ix_orders_tenant_id", table_name="orders")

    # 17. point_transactions
    op.drop_index("ix_point_transactions_tenant_id", table_name="point_transactions")

    # 18. system_otps
    op.drop_index("ix_system_otps_identifier", table_name="system_otps")

    # 19. unified_agent_tasks
    op.drop_index("ix_unified_agent_tasks_agent_id", table_name="unified_agent_tasks")
    op.drop_index("ix_unified_agent_tasks_tenant_id", table_name="unified_agent_tasks")


def downgrade() -> None:
    import sqlalchemy as sa

    # 1. click_fraud_events
    op.create_index("ix_click_fraud_events_gclid", "click_fraud_events", ["gclid"])
    op.create_index("ix_click_fraud_events_ip_address", "click_fraud_events", ["ip_address"])

    # 2. content_scouts
    op.create_index("ix_content_scouts_tenant_id", "content_scouts", ["tenant_id"])

    # 3. media_usage
    op.create_index("ix_media_usage_entity_type", "media_usage", ["entity_type"])

    # 4. product_bases
    op.create_index("ix_product_bases_tenant_id", "product_bases", ["tenant_id"])

    # 5. audit_logs
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_target_table", "audit_logs", ["target_table"])

    # 6. banners
    op.create_index("ix_banners_tenant_id", "banners", ["tenant_id"])

    # 7. campaign_events
    op.create_index("ix_campaign_events_tenant", "campaign_events", ["tenant_id"])

    # 8. commission_ledger
    op.create_index("ix_commission_ledger_affiliate_id", "commission_ledger", ["affiliate_id"])
    op.create_index("ix_commission_ledger_tenant_id", "commission_ledger", ["tenant_id"])

    # 9. commission_tiers
    op.create_index("ix_commission_tiers_tenant_id", "commission_tiers", ["tenant_id"])

    # 10. appointments
    op.create_index("ix_appointments_tenant_id", "appointments", ["tenant_id"])

    # 11. affiliate_profiles
    op.create_index("ix_affiliate_profiles_tenant_id", "affiliate_profiles", ["tenant_id"])

    # 12. categories
    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"])

    # 13. content_campaigns
    op.create_index("ix_content_campaigns_tenant_id", "content_campaigns", ["tenant_id"])

    # 14. google_ads_campaign_logs
    op.create_index("ix_google_ads_campaign_logs_campaign_id", "google_ads_campaign_logs", ["campaign_id"])

    # 15. notifications
    op.create_index("ix_notifications_tenant_id", "notifications", ["tenant_id"])

    # 16. orders
    op.create_index("ix_orders_tenant_id", "orders", ["tenant_id"])

    # 17. point_transactions
    op.create_index("ix_point_transactions_tenant_id", "point_transactions", ["tenant_id"])

    # 18. system_otps
    op.create_index("ix_system_otps_identifier", "system_otps", ["identifier"])

    # 19. unified_agent_tasks
    op.create_index("ix_unified_agent_tasks_agent_id", "unified_agent_tasks", ["agent_id"])
    op.create_index("ix_unified_agent_tasks_tenant_id", "unified_agent_tasks", ["tenant_id"])
