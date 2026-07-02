"""v615 - Table-level autovacuum parameters and pgvector HNSW indexes

Revision ID: v615
Revises: v614
Create Date: 2026-06-19

=== PHÂN TÍCH ===
1. Autovacuum Tuning:
   - system_reviews và media_registry là các bảng có hoạt động cập nhật và dọn dẹp thường xuyên. Thiết lập table-level autovacuum_vacuum_scale_factor = 0.05 và autovacuum_analyze_scale_factor = 0.05 giúp dọn dẹp các dead tuples sớm hơn khi chỉ có 5% số dòng thay đổi (thay vì 20% và 10% mặc định).

2. pgvector HNSW Indexing:
   - Đồng bộ cột embedding của seo_pillar_embeddings sang kiểu vector(384) (do HNSW yêu cầu kích thước vector xác định).
   - Tạo các chỉ mục HNSW (Hierarchical Navigable Small World) sử dụng toán tử vector_cosine_ops trên 4 bảng vector embeddings để hỗ trợ tìm kiếm tương đồng ngữ nghĩa cực nhanh khi hệ thống mở rộng quy mô trên 10,000 dòng.
"""
from alembic import op

revision = "v615"
down_revision = "v614"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Thiết lập autovacuum cho các bảng ghi nhiều
    op.execute("ALTER TABLE system_reviews SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.05)")
    op.execute("ALTER TABLE media_registry SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.05)")

    # 2. Đồng bộ cột embedding của seo_pillar_embeddings và support_knowledge_embeddings sang kiểu vector(384)
    op.execute("ALTER TABLE seo_pillar_embeddings ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)")
    op.execute("ALTER TABLE support_knowledge_embeddings ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)")

    # 3. Tạo chỉ mục HNSW cho tìm kiếm vector ngữ nghĩa
    op.execute("CREATE INDEX IF NOT EXISTS ix_article_embeddings_hnsw ON article_embeddings USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_product_embeddings_hnsw ON product_embeddings USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_pillar_embeddings_hnsw ON seo_pillar_embeddings USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_support_knowledge_embeddings_hnsw ON support_knowledge_embeddings USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    # 1. Reset cấu hình autovacuum về mặc định
    op.execute("ALTER TABLE system_reviews RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor)")
    op.execute("ALTER TABLE media_registry RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor)")

    # 2. Khôi phục cột embedding của seo_pillar_embeddings và support_knowledge_embeddings về kiểu text
    op.execute("ALTER TABLE seo_pillar_embeddings ALTER COLUMN embedding TYPE text USING embedding::text")
    op.execute("ALTER TABLE support_knowledge_embeddings ALTER COLUMN embedding TYPE text USING embedding::text")

    # 3. Drop các chỉ mục HNSW
    op.execute("DROP INDEX IF EXISTS ix_article_embeddings_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_product_embeddings_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_seo_pillar_embeddings_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_support_knowledge_embeddings_hnsw")
