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

---

# Walkthrough - Dọn dẹp Database & Khôi phục Thiết Quân Luật (Giai đoạn 1 & 2)

## Files đã sửa/tạo (6 files)

### Database Cleanup (Giai đoạn 1)
1. **`backend/database/models/commerce.py`** — Loại bỏ hoàn toàn model `RentalContract` mồ côi và mối quan hệ `rentals` khỏi `ProductBase`.
2. **`backend/database/models/__init__.py`** — Loại bỏ `RentalContract` khỏi imports và danh sách xuất khẩu `__all__`.
3. **`backend/database/repositories.py`** — Loại bỏ `RentalContractRepository` và import tương ứng.
4. **`backend/migrations/versions/fe0e6bbf45b5_drop_rental_contracts.py`** — Tệp migration Alembic mới drop bảng `rental_contracts` ở `upgrade()` và khôi phục ở `downgrade()`.

### Code Cleanup & Lockdown Sync (Giai đoạn 2)
5. **`backend/core/database.py`** — Thanh lý triệt để code thối trùng lặp cấu hình DB, chuyển biến tĩnh `SYSTEM_READ_ONLY` thành hàm check động `is_system_read_only()` linh hoạt.
6. **`backend/database/alchemy_config.py`** — Chuyển từ kiểm tra biến tĩnh sang gọi hàm dynamic `is_system_read_only()` tại event `before_cursor_execute` để khóa DB tức thời ở runtime.
7. **`backend/audit_middleware.py`** — Tích hợp kiểm tra đồng bộ trạng thái Martial Law từ Redis bất đồng bộ trên mỗi HTTP request để cập nhật môi trường runtime, và chuyển sang dùng `is_system_read_only()` động để khóa API Mutation tức thời.
8. **`backend/controllers/security.py`** — Dọn dẹp import thừa `SYSTEM_READ_ONLY`.

## Kiểm định
- **Alembic Migration**: Chạy thành công lệnh `alembic upgrade head`, dịch chuyển database lên phiên bản `fe0e6bbf45b5 (head)` và drop bảng `rental_contracts` thành công trong Postgres.
- **Khởi động Litestar Engine**: Uvicorn khởi chạy và hot-reload thành công 100% không bắn ra bất cứ lỗi syntax hay import nào. Tự động đồng bộ RBAC và sẵn sàng phục vụ.



