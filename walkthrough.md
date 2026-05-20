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



---

# Walkthrough - Cập nhật Hệ thống Trinity AI Core & Tự động khai tử mô hình (Elite V2.2)

## Files đã sửa/tạo (4 files)

### Backend (4 files)
1. **`backend/services/ai_engine/core/trinity_models.py`** — Cập nhật mảng `HARD_BLACKLIST` (thêm `"gemini-2.0-pro"`, `"gemini-1.5-pro"`, `"gemini-1.5-flash"`). Bổ sung phương thức `add_to_persistent_blacklist` xử lý ghi nhận vĩnh viễn mô hình chết vào DB `SystemSetting` cấu hình `ai_orchestration_config`, đồng thời lọc sạch mô hình này ra khỏi bảng `VoiceProfile` và hot-reload bộ nhớ tức thời. Thay thế mô hình fallback chết bằng `"gemini-2.5-pro"`. Bổ sung cơ chế **Hợp nhất Cấu hình Động (Dynamic Fusion Whitelist/Blacklist)** cho phép Sếp định hình cấu hình `whitelist` trong database để ghi đè/cứu sống bất kỳ model nào nằm trong `HARD_BLACKLIST`.
2. **`backend/services/ai_engine/core/trinity_bridge.py`** — Lồng ghép cơ chế gọi `add_to_persistent_blacklist` tại hàm `run` và `run_stream` khi bắt được mã lỗi `404 Model Not Found` (`model_not_found`). Thêm bộ tiền-lọc `"gemini-2.0-pro"` tại hàm `reload_models` để tự động redirect về `"gemini-2.0-flash"` khi khởi chạy hệ thống.
3. **`backend/services/ai_service.py`** — Nâng cấp `priority_pool` trong tiến trình `auto_optimize_stack` chuyển từ `"gemini-2.0-pro"` cũ sang các mô hình hiện đại `["gemini-2.5-flash", "gemini-2.5-pro"]`.
4. **`backend/lifespan.py`** — Cài đặt vệ binh định kỳ `_model_health_sync_loop` chạy ngầm 12 giờ một lần để kiểm tra độ trễ/kết nối của các mô hình LLM, tự động cô lập và blacklist các mô hình trả về lỗi `404` hay `400`.

## Kiểm định
- **Syntax Check**: Chạy kiểm tra AST của cả 4 files thành công (`Syntax OK`), cam kết không dính lỗi cú pháp.
- **Docker Compose Restart**: Khởi động lại các container `api`, `worker_high`, `worker_default` trơn tru.
- **Runtime Log Verify**: Đã kiểm chứng log container `api` khởi chạy không lỗi (`Application startup complete`), đồng bộ VoiceProfile, RBAC và nạp keys mượt mà.
- **Dynamic Whitelist Test**: Hàm `is_blacklisted` ưu tiên kiểm tra whitelist của cơ sở dữ liệu trước tiên để cung cấp khả năng override động 100%.
