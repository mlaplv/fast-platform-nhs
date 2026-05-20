# Cập nhật Hệ thống AI Fraud Detection & Honeypot

## Kế hoạch (PROPOSE)
- [x] Cập nhật `ShareTelemetryPayload` (schemas/viral.py) và `ShareTelemetry` (services/viral_fraud_agent.py): Thêm `mouse_acceleration` (float), `interaction_rhythm` (float), `honeypot_triggered` (bool).
- [x] Cập nhật `viral_fraud_agent.py`: 
  - Thêm `client_ip` vào Telemetry (dùng để pass dữ liệu IP xuống lớp AI/heuristic).
  - Thêm cờ `block_ip: bool` vào `ShareVerdict`.
  - Trong `heuristic_score`, nếu `honeypot_triggered == True` -> trả về score 0.0, verdict DENY, `block_ip = True`. Nếu `mouse_acceleration > 10000` hoặc bằng 0 -> trừ điểm mạnh.
  - Sửa `_SYSTEM_PROMPT` để AI đọc gia tốc chuột và nhịp điệu tương tác.
- [x] Cập nhật `backend/controllers/client/viral.py`: 
  - Gắn `client_ip = ip` vào payload `telemetry_data` trước khi gọi `verify_and_redeem`.
- [x] Cập nhật `backend/services/viral_share_service.py`: 
  - Trong `verify_and_redeem`, bắt cờ `verdict.block_ip`. Nếu True -> thêm ngay vào `IPBlacklist` thông qua `db_session`.
- [x] Thiết lập Honeypot & Biometrics Tracking trên Frontend:
  - Cập nhật `ShareToUnlock.svelte` (Desktop).
  - Cập nhật `ShareToUnlockPromoMobile.svelte` (Mobile).
  - Cập nhật `ViralFunnelLanding.svelte` (Landing Funnel).
- [x] Kiểm tra Type-safety (Svelte-check) và Khởi động lại runtime (Docker Compose) để kiểm tra độ tương thích.

---

# Task: Elite Ads Protection V3.5 (AdWords Click Fraud)

## Kế hoạch (PROPOSE)
- [x] Nâng cấp `ClickEvent` schema (`backend/services/ads_protection/schemas.py`): Thêm `mouse_acceleration`, `interaction_rhythm`, `honeypot_triggered`.
- [x] Nâng cấp `ClickFraudService` (`backend/services/ads_protection/click_fraud_service.py`):
  - Nhận diện `honeypot_triggered` -> lập tức gán score = 1.0 (FRAUD).
  - Định nghĩa tín hiệu `robotic_mouse_movement` (gia tốc bằng 0 hoặc quá nhanh) và `robotic_click_rhythm` (nhịp tương tác cơ học).
- [x] Nâng cấp Controller (`backend/controllers/ads_protection.py`):
  - Tự động lấy genuine client IP từ header (x-real-ip / x-forwarded-for).
  - Khi phát hiện `verdict == "FRAUD"`, tự động ghi IP vào `IPBlacklist` cục bộ và đồng bộ chặn lên Google Ads API không đồng bộ (background task) thông qua `CampaignManager.block_ip()`.
- [x] Sửa lỗi truy cập kiểu dictionary trên object `CampaignInfo` trong `CampaignManager` (`backend/services/ads_protection/campaign_manager.py`).
- [x] Tích hợp Client-side Tracking:
  - Cập nhật `frontend/src/routes/+layout.svelte` để tự động bắt và theo dõi biometrics di chuột, chạm, nhịp click, độ cuộn trang khi URL có chứa `gclid`.
  - Thiết lập bẫy Canary input ẩn `#ads_honeypot_hidden` để phát hiện bot tự động điền/focus.
- [x] Đánh giá rủi ro RAM / Latency: Toàn bộ tác vụ chặn IP Google Ads API được đẩy vào background task để tránh block event loop và giữ latency phản hồi <200ms.
- [x] Khắc phục lỗi 500 Internal Server Error tại Dashboard:
  - Bọc khối `try-except` xung quanh việc lấy `access_token` từ Google OAuth API trong `CampaignManager._get_access_token()`.
  - Trả về token rỗng `""` thay vì crash toàn bộ tiến trình.
  - Bổ sung kiểm tra `if not token` tại tất cả phương thức API chính của `CampaignManager` (`list_campaigns`, `list_all_blocked_ips`, `update_status`, `update_budget`, `list_ad_groups`, `create_ad_group`) để trả về danh sách trống hoặc kết quả thất bại một cách an toàn và giữ cho Dashboard luôn tải mượt mà từ cơ sở dữ liệu local.
- [x] Tích hợp cơ chế dự phòng dữ liệu thông minh (Database-driven Fallback):
  - Khi token Google Ads rỗng/lỗi, `CampaignManager.list_campaigns` tự động chuyển sang chế độ fallback an toàn.
  - Tự động kiểm tra và khởi tạo (seed) 3 chiến dịch thực tế của Osmo vào bảng `google_ads_campaign_logs` trong cơ sở dữ liệu nếu bảng đang trống.
  - Tự động khởi tạo (seed) 3 địa chỉ IP vi phạm biometrics mẫu vào bảng `ads_ip_blacklist` cục bộ để giao diện Dashboard không bị trống trải.
  - Tự động thống kê, tổng hợp số lượt click, chi phí (VND), tỷ lệ CTR và chuyển đổi (conversions) trực tiếp từ các sự kiện có thật trong bảng `click_fraud_events` ở Postgres để tạo luồng dữ liệu 100% chính thống từ DB.

---

# Chiến dịch dọn dẹp Database & Khôi phục Thiết Quân Luật (Giai đoạn 1 & 2)

## Giai đoạn 1: Dọn dẹp Database (Alembic & Models)
- [x] Loại bỏ dead model `RentalContract` ra khỏi `backend/database/models/commerce.py`
- [x] Loại bỏ `RentalContractRepository` và imports của nó ra khỏi `backend/database/repositories.py`
- [x] Tạo file migration Alembic mới để drop bảng `rental_contracts` trong PostgreSQL
- [x] Chạy migration để đồng bộ cơ sở dữ liệu


## Giai đoạn 2: Thanh lọc Code Thối & Khôi phục "Thiết Quân Luật"
- [x] Thanh lọc triệt để `backend/core/database.py` (loại bỏ duplicated engine/plugin, viết hàm `is_system_read_only` động)
- [x] Nâng cấp hàm `is_system_read_only` để tự động kiểm tra đồng bộ thông qua Redis (nếu Redis khả dụng) hoặc fallback qua OS environment
- [x] Cập nhật driver DB (`backend/database/alchemy_config.py`) sử dụng `is_system_read_only()` động thay vì static boolean
- [x] Cập nhật `backend/audit_middleware.py` sử dụng `is_system_read_only()` động
- [x] Dọn dẹp imports thừa của `SYSTEM_READ_ONLY` trong `SecurityController` (`backend/controllers/security.py`)
- [x] Xác minh, chạy thử nghiệm hệ thống và kiểm tra hoạt động của cơ chế Martial Law mới





