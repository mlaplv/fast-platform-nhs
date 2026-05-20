# Bằng chứng triển khai (Walkthrough) - AI Fraud Detection & Honeypot

## Files đã sửa (7 files)

### Backend (4 files)
1. **`backend/schemas/viral.py`** — Thêm `mouse_acceleration`, `interaction_rhythm`, `honeypot_triggered` vào `ShareTelemetryPayload`.
2. **`backend/services/viral_fraud_agent.py`** — Thêm biometric fields vào `ShareTelemetry` + `client_ip`. Thêm `block_ip` vào `ShareVerdict`. Cập nhật `heuristic_score` (Honeypot → instant DENY + block). Cập nhật `_SYSTEM_PROMPT` cho AI.
3. **`backend/controllers/client/viral.py`** — Gắn `client_ip = ip` vào telemetry dict trước khi gọi service.
4. **`backend/services/viral_share_service.py`** — Bắt `verdict.block_ip` → ghi `IPBlacklist` vào DB realtime.

### Frontend (3 files)
5. **`frontend/.../ShareToUnlock.svelte`** (Desktop) — Thêm mousemove tracking, click rhythm variance, honeypot button element, gửi 3 trường mới.
6. **`frontend/.../ShareToUnlockPromoMobile.svelte`** (Mobile) — Thêm touchmove tracking, click rhythm variance, honeypot input element, gửi 3 trường mới.
7. **`frontend/.../ViralFunnelLanding.svelte`** (Funnel) — Thêm mousemove tracking, click rhythm variance, honeypot input element, gửi 3 trường mới.

## Kiểm định
- **DB Migration**: KHÔNG CẦN — `IPBlacklist` model đã tồn tại sẵn (`ads_ip_blacklist` table).
- **Svelte Check**: 0 lỗi mới từ code vừa sửa. Tất cả 1155 errors đều là legacy từ checkout/success, track, vouchers.
- **Docker Restart**: API khởi động thành công (`Application startup complete`), UI build thành công (chỉ CSS warnings cũ).
- **Alembic Auto-sync**: Schema đồng bộ — `Will assume transactional DDL` — không phát sinh migration mới.

---

# Walkthrough - Elite Ads Protection V3.5 (AdWords Click Fraud)

## Files đã sửa/tạo (5 files)

### Backend (4 files)
1. **`backend/services/ads_protection/schemas.py`** — Thêm `mouse_acceleration`, `interaction_rhythm`, `honeypot_triggered` vào `ClickEvent`.
2. **`backend/services/ads_protection/click_fraud_service.py`** — Tích hợp tín hiệu `honeypot_triggered` (gán score = 1.0), `robotic_mouse_movement` và `robotic_click_rhythm`.
3. **`backend/controllers/ads_protection.py`** — Lấy IP thực của client qua headers, tự động chặn IP cục bộ (`IPBlacklist`) và đẩy lệnh chặn lên Google Ads API không đồng bộ (background task) khi có kết quả `FRAUD`.
4. **`backend/services/ads_protection/campaign_manager.py`** — Sửa lỗi dictionary access `camp['resource_name']` thành `camp.resource_name`. Đồng thời, sửa lỗi bộc lộ exception khi lấy `access_token` bằng cách wrap `try-except` trả về `""` và thêm kiểm tra `if not token` để tránh lỗi 500 khi API credentials không hợp lệ/hết hạn. Tích hợp cơ chế tự động seed chiến dịch và IP bị chặn mẫu, đồng thời tự động tổng hợp số liệu thống kê click từ các bản ghi có thật trong Postgres (`click_fraud_events`).
5. **`backend/controllers/ads_protection.py`** — Cập nhật controller `/campaigns` truyền `db_session` để kích hoạt cơ chế fallback dữ liệu Postgres.

### Frontend (1 file)
6. **`frontend/src/routes/+layout.svelte`** — Theo dõi sinh trắc học tương tác và Canary Trap honeypot khi phát hiện URL chứa `gclid`, tự động báo cáo telemetry về endpoint `/validate-click`.


