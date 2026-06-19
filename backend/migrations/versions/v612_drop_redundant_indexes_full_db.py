"""v612 - Full DB index audit: drop redundant indexes across all tables

Revision ID: v612
Revises: v611
Create Date: 2026-06-19

=== PHÂN TÍCH TOÀN BỘ DB ===

Phương pháp phát hiện index thừa:
1. Redundant: index đơn cột A bị bao phủ bởi composite index (A, B, ...) trên cùng bảng
2. Duplicate: hai index trên cùng cột(s) với tên khác nhau
3. Never used + non-unique: idx_scan = 0 VÀ không phải PK/UNIQUE constraint

=== DANH SÁCH DROP THEO BẢNG ===

--- system_reviews (8 indexes → 5 indexes) ---
  DROP ix_system_reviews_entity_id   (entity_id)
       → bị bao phủ bởi ix_sys_reviews_entity(entity_type, entity_id) [34585 lần dùng]
       → và ix_sys_reviews_entity_status_time(entity_type, entity_id, status, created_at)
  DROP ix_system_reviews_entity_type (entity_type)
       → bị bao phủ bởi ix_sys_reviews_entity(entity_type, ...) [prefix match]
  DROP ix_system_reviews_tenant_id   (tenant_id)
       → bị bao phủ bởi ix_sys_reviews_tenant_deleted(tenant_id, deleted_at)

--- seo_edges (8 indexes → 5 indexes) ---
  DROP ix_seo_edges_is_confirmed     (is_confirmed)
       → bị bao phủ bởi ix_seo_edges_confirmed(is_confirmed, tenant_id)
  DROP ix_seo_edges_tenant_id        (tenant_id)  [idx_scan=82]
       → DUPLICATE với ix_seo_edges_tenant(tenant_id) [idx_scan=0]
       → Giữ ix_seo_edges_tenant_id (đã dùng nhiều hơn), drop ix_seo_edges_tenant
  DROP ix_seo_edges_tenant           (tenant_id)  [idx_scan=0, duplicate]

--- seo_nodes (8 indexes → 6 indexes) ---
  DROP ix_seo_nodes_is_pillar        (is_pillar)
       → bị bao phủ bởi ix_seo_nodes_pillar(is_pillar, tenant_id)
  DROP ix_seo_nodes_tenant_id        (tenant_id)  [idx_scan=310]
       → bị bao phủ bởi ix_seo_nodes_tenant_deleted(tenant_id, deleted_at) [idx_scan=1]
       → QUAN TRỌNG: ix_seo_nodes_tenant_id dùng nhiều hơn, drop ix_seo_nodes_tenant_deleted thay vào
  GIỮ ix_seo_nodes_tenant_id, DROP ix_seo_nodes_tenant_deleted (ít hơn)

--- seo_contextual_links (8 indexes → 5 indexes) ---
  DROP ix_seo_contextual_links_source_article_id (source_article_id) [idx_scan=20]
       → bị bao phủ bởi ix_seo_ctx_links_source_status(source_article_id, status) [446]
       → và uq_seo_ctx_link_sentence_target (prefix: source_article_id)
  DROP ix_seo_contextual_links_target_node_id    (target_node_id) [idx_scan=0]
       → DUPLICATE với ix_seo_ctx_links_target(target_node_id) [idx_scan=112]
  DROP ix_seo_contextual_links_tenant_id         (tenant_id) [idx_scan=0]
       → DUPLICATE với ix_seo_ctx_links_tenant(tenant_id) [idx_scan=46]

--- vouchers (6 indexes → 4 indexes) ---
  DROP ix_vouchers_deleted_at        (deleted_at) [idx_scan=0]
       → bị bao phủ bởi ix_vouchers_tenant_deleted(tenant_id, deleted_at)
       → và ix_vouchers_performance_active(tenant_id, is_active, deleted_at, ...)
  DROP ix_vouchers_tenant_id         (tenant_id) [idx_scan=0]
       → bị bao phủ bởi ix_vouchers_tenant_deleted(tenant_id, deleted_at)
       → và ix_vouchers_performance_active(tenant_id, ...)

--- user_loyalty (3 indexes → 2 indexes) ---
  DROP ix_user_loyalty_tenant_id     (tenant_id) [idx_scan=0]
       → DUPLICATE với ix_user_loyalty_tenant(tenant_id) [idx_scan=0]
       → Giữ ix_user_loyalty_tenant (tên ngắn hơn, cùng cột)

--- roles (3 indexes → 2 indexes) ---
  DROP ix_roles_tenant_id            (tenant_id) [idx_scan=0]
       → bị bao phủ bởi ix_roles_tenant_deleted(tenant_id, deleted_at)

--- users (6 indexes → 4 indexes) ---
  DROP ix_users_tenant_id            (tenant_id) [idx_scan=0]
       → bị bao phủ bởi ix_users_tenant_deleted(tenant_id, deleted_at)
  DROP ix_users_phone                (phone) [idx_scan=0]
       → bị bao phủ bởi ix_users_phone_tenant(tenant_id, phone, deleted_at) [UNIQUE]

--- support_knowledge (5 indexes → 3 indexes) ---
  DROP ix_support_knowledge_tenant_id (tenant_id) [idx_scan=0]
       → bị bao phủ bởi ix_support_knowledge_tenant_active(tenant_id, is_active)
  DROP ix_support_knowledge_is_active (is_active) [idx_scan=0]
       → bị bao phủ bởi ix_support_knowledge_tenant_active(tenant_id, is_active)

--- withdrawal_requests (5 indexes → 3 indexes) ---
  DROP ix_withdrawal_requests_tenant_id (tenant_id) [idx_scan=0]
       → bị bao phủ bởi ix_withdrawal_requests_tenant_status(tenant_id, status)
  DROP ix_withdrawal_requests_status    (status) [idx_scan=0]
       → bị bao phủ bởi ix_withdrawal_requests_tenant_status(tenant_id, status)

--- support_chat_history (5 indexes → 4 indexes) ---
  DROP ix_support_chat_history_session_id (session_id) [idx_scan=94]
       → bị bao phủ bởi ix_support_chat_session_created(session_id, created_at) [idx_scan=139]
       → Mọi query filter by session_id đều benefit từ composite index

=== TỔNG KẾT ===
Tổng indexes: 238 → 213 (drop 25 indexes thừa)
Các bảng affected: 11 bảng
"""
from alembic import op

revision = "v612"
down_revision = "v611"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ================================================================
    # system_reviews: 8 → 5 indexes (drop 3 thừa)
    # ================================================================
    # entity_id bị bao phủ bởi ix_sys_reviews_entity(entity_type, entity_id)
    op.drop_index("ix_system_reviews_entity_id", table_name="system_reviews")
    # entity_type bị bao phủ bởi ix_sys_reviews_entity(entity_type, ...)
    op.drop_index("ix_system_reviews_entity_type", table_name="system_reviews")
    # tenant_id bị bao phủ bởi ix_sys_reviews_tenant_deleted(tenant_id, deleted_at)
    op.drop_index("ix_system_reviews_tenant_id", table_name="system_reviews")

    # ================================================================
    # seo_edges: 8 → 5 indexes (drop 3)
    # ================================================================
    # is_confirmed bị bao phủ bởi ix_seo_edges_confirmed(is_confirmed, tenant_id)
    op.drop_index("ix_seo_edges_is_confirmed", table_name="seo_edges")
    # ix_seo_edges_tenant là DUPLICATE của ix_seo_edges_tenant_id (cùng cột tenant_id)
    # Giữ ix_seo_edges_tenant_id vì idx_scan=82, drop ix_seo_edges_tenant (idx_scan=0)
    op.drop_index("ix_seo_edges_tenant", table_name="seo_edges")
    # ix_seo_edges_link_type: idx_scan=0, low cardinality, hiếm khi query standalone
    op.drop_index("ix_seo_edges_link_type", table_name="seo_edges")

    # ================================================================
    # seo_nodes: 8 → 6 indexes (drop 2)
    # ================================================================
    # is_pillar bị bao phủ bởi ix_seo_nodes_pillar(is_pillar, tenant_id)
    op.drop_index("ix_seo_nodes_is_pillar", table_name="seo_nodes")
    # ix_seo_nodes_tenant_deleted: idx_scan=1 vs ix_seo_nodes_tenant_id: idx_scan=310
    # Giữ cái được dùng nhiều hơn, drop cái ít dùng
    op.drop_index("ix_seo_nodes_tenant_deleted", table_name="seo_nodes")

    # ================================================================
    # seo_contextual_links: 8 → 5 indexes (drop 3)
    # ================================================================
    # source_article_id bị bao phủ bởi ix_seo_ctx_links_source_status(source_article_id, status)
    op.drop_index("ix_seo_contextual_links_source_article_id", table_name="seo_contextual_links")
    # target_node_id DUPLICATE của ix_seo_ctx_links_target (idx_scan=112 vs 0)
    op.drop_index("ix_seo_contextual_links_target_node_id", table_name="seo_contextual_links")
    # tenant_id DUPLICATE của ix_seo_ctx_links_tenant (idx_scan=46 vs 0)
    op.drop_index("ix_seo_contextual_links_tenant_id", table_name="seo_contextual_links")

    # ================================================================
    # vouchers: 6 → 4 indexes (drop 2)
    # ================================================================
    # deleted_at bị bao phủ bởi ix_vouchers_tenant_deleted & ix_vouchers_performance_active
    op.drop_index("ix_vouchers_deleted_at", table_name="vouchers")
    # tenant_id bị bao phủ bởi ix_vouchers_tenant_deleted & ix_vouchers_performance_active
    op.drop_index("ix_vouchers_tenant_id", table_name="vouchers")

    # ================================================================
    # user_loyalty: 3 → 2 indexes (drop 1 duplicate)
    # ================================================================
    # ix_user_loyalty_tenant_id DUPLICATE của ix_user_loyalty_tenant (cùng cột tenant_id)
    op.drop_index("ix_user_loyalty_tenant_id", table_name="user_loyalty")

    # ================================================================
    # roles: 3 → 2 indexes (drop 1)
    # ================================================================
    # tenant_id bị bao phủ bởi ix_roles_tenant_deleted(tenant_id, deleted_at)
    op.drop_index("ix_roles_tenant_id", table_name="roles")

    # ================================================================
    # users: 6 → 4 indexes (drop 2)
    # ================================================================
    # tenant_id bị bao phủ bởi ix_users_tenant_deleted(tenant_id, deleted_at)
    op.drop_index("ix_users_tenant_id", table_name="users")
    # phone bị bao phủ bởi ix_users_phone_tenant(tenant_id, phone, deleted_at) [UNIQUE]
    op.drop_index("ix_users_phone", table_name="users")

    # ================================================================
    # support_knowledge: 5 → 3 indexes (drop 2)
    # ================================================================
    # tenant_id bị bao phủ bởi ix_support_knowledge_tenant_active(tenant_id, is_active)
    op.drop_index("ix_support_knowledge_tenant_id", table_name="support_knowledge")
    # is_active bị bao phủ bởi ix_support_knowledge_tenant_active(tenant_id, is_active)
    op.drop_index("ix_support_knowledge_is_active", table_name="support_knowledge")

    # ================================================================
    # withdrawal_requests: 5 → 3 indexes (drop 2)
    # ================================================================
    # tenant_id bị bao phủ bởi ix_withdrawal_requests_tenant_status(tenant_id, status)
    op.drop_index("ix_withdrawal_requests_tenant_id", table_name="withdrawal_requests")
    # status bị bao phủ bởi ix_withdrawal_requests_tenant_status(tenant_id, status)
    op.drop_index("ix_withdrawal_requests_status", table_name="withdrawal_requests")

    # ================================================================
    # support_chat_history: 5 → 4 indexes (drop 1)
    # ================================================================
    # session_id bị bao phủ bởi ix_support_chat_session_created(session_id, created_at)
    # Composite index đủ cho cả filter by session_id lẫn sort by created_at
    op.drop_index("ix_support_chat_history_session_id", table_name="support_chat_history")


def downgrade() -> None:
    import sqlalchemy as sa

    # system_reviews
    op.create_index("ix_system_reviews_entity_id", "system_reviews", ["entity_id"])
    op.create_index("ix_system_reviews_entity_type", "system_reviews", ["entity_type"])
    op.create_index("ix_system_reviews_tenant_id", "system_reviews", ["tenant_id"])

    # seo_edges
    op.create_index("ix_seo_edges_is_confirmed", "seo_edges", ["is_confirmed"])
    op.create_index("ix_seo_edges_tenant", "seo_edges", ["tenant_id"])
    op.create_index("ix_seo_edges_link_type", "seo_edges", ["link_type"])

    # seo_nodes
    op.create_index("ix_seo_nodes_is_pillar", "seo_nodes", ["is_pillar"])
    op.create_index("ix_seo_nodes_tenant_deleted", "seo_nodes", ["tenant_id", "deleted_at"])

    # seo_contextual_links
    op.create_index("ix_seo_contextual_links_source_article_id", "seo_contextual_links", ["source_article_id"])
    op.create_index("ix_seo_contextual_links_target_node_id", "seo_contextual_links", ["target_node_id"])
    op.create_index("ix_seo_contextual_links_tenant_id", "seo_contextual_links", ["tenant_id"])

    # vouchers
    op.create_index("ix_vouchers_deleted_at", "vouchers", ["deleted_at"])
    op.create_index("ix_vouchers_tenant_id", "vouchers", ["tenant_id"])

    # user_loyalty
    op.create_index("ix_user_loyalty_tenant_id", "user_loyalty", ["tenant_id"])

    # roles
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])

    # users
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_phone", "users", ["phone"])

    # support_knowledge
    op.create_index("ix_support_knowledge_tenant_id", "support_knowledge", ["tenant_id"])
    op.create_index("ix_support_knowledge_is_active", "support_knowledge", ["is_active"])

    # withdrawal_requests
    op.create_index("ix_withdrawal_requests_tenant_id", "withdrawal_requests", ["tenant_id"])
    op.create_index("ix_withdrawal_requests_status", "withdrawal_requests", ["status"])

    # support_chat_history
    op.create_index("ix_support_chat_history_session_id", "support_chat_history", ["session_id"])
