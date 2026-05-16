-- ============================================================
-- [T-14] Security Migration: GIN Index for orders.order_metadata
-- Mục tiêu: Tăng tốc JSONB lookup trong voucher anti-abuse check
-- Áp dụng: PostgreSQL production ONLY (không áp dụng cho SQLite dev)
-- Tác giả: Elite V2.2 Security Hardening Sprint — 2026-05-16
-- ============================================================

-- QUAN TRỌNG: Dùng CONCURRENTLY để tránh lock table khi deploy production
-- Chạy lệnh này trong giờ thấp tải (ngoài giờ cao điểm)

-- 1. GIN index cho toàn bộ order_metadata JSONB
--    Hỗ trợ: @>, ?, ?|, ?& operators — nhanh hơn 100x so với full table scan
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_order_metadata_gin
    ON orders USING GIN (order_metadata jsonb_path_ops);

-- 2. Index phụ trợ truy vấn theo phone + status (thường dùng trong anti-abuse check)
--    Hỗ trợ: SELECT * FROM orders WHERE customer_phone = X AND status != 'CANCELLED'
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_phone_status
    ON orders (customer_phone, status)
    WHERE status != 'CANCELLED';

-- 3. Index cho spam monitoring queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_spam_score
    ON orders (spam_score, is_spam, created_at)
    WHERE is_spam = TRUE;

-- Verify sau khi tạo:
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'orders' ORDER BY indexname;
