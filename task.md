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





---

# Cập nhật Hệ thống Trinity AI Core & Tự động khai tử mô hình (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] Cập nhật `HARD_BLACKLIST` trong `backend/services/ai_engine/core/trinity_models.py` loại bỏ `"gemini-2.0-pro"`, `"gemini-1.5-pro"`, `"gemini-1.5-flash"`.
- [x] Xây dựng phương thức `add_to_persistent_blacklist` trong `TrinityModels` để lưu mô hình chết/lỗi vào DB SystemSetting `ai_orchestration_config`, xóa mô hình chết khỏi cấu hình `VoiceProfile.primary_model` và `VoiceProfile.ai_models` waterfall, đồng thời hot-reload bộ nhớ.
- [x] Tích hợp cơ chế tự động gọi `add_to_persistent_blacklist` trong `TrinityBridge.run` và `TrinityBridge.run_stream` khi gặp lỗi `404 Model Not Found` (`model_not_found`).
- [x] Khai tử hoàn toàn `priority_pool` hardcode khỏi `auto_optimize_stack` (`backend/services/ai_service.py`) để tự động hóa 100% việc dựng thác nước động dựa trên điểm số thực tế.
- [x] Đưa thẳng `gemini-2.0-flash-lite` vào `HARD_BLACKLIST` trong `trinity_models.py` để khai tử vĩnh viễn và triệt để dòng model hết hạn này khỏi hệ thống ngay lập tức.
- [x] Loại bỏ hoàn toàn các chuỗi hardcode `"gemini-2.0-flash"` / `"gemini-2.0-flash-lite"` làm fallback khi dọn dẹp profile lỗi hay khi danh sách winners rỗng, chuyển đổi hoàn chỉnh sang sử dụng động `trinity_bridge.primary_model` và `trinity_bridge.fallback_model`.
- [x] Cập nhật đồng bộ cấu hình model khởi đầu `AI_PRIMARY_MODEL=gemini-3.5-flash` và model dự phòng `AI_FALLBACK_MODEL=gemini-3.1-flash-lite` trong `.env` và `trinity_bridge.py`.
- [x] Thiết lập tác vụ định kỳ `_model_health_sync_loop` chạy ngầm mỗi 12 giờ tại `backend/lifespan.py` để ping kiểm tra và tự động khai tử/blacklist các mô hình lỗi thời/chết.
- [x] Xây dựng cơ chế Hợp nhất Cấu hình Động (Dynamic Fusion Blacklist & Whitelist override) cho phép Sếp định cấu hình `whitelist` trong cơ sở dữ liệu để ghi đè hoàn toàn danh sách đen tĩnh `HARD_BLACKLIST`.

---

# Nâng cấp Bảo mật Helen: Chống Prompt Injection & Kiểm soát Hai Chiều (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] Nâng cấp các mẫu Regex của `InputGuard` để phát hiện và ngăn chặn triệt để hành vi chèn thẻ hệ thống.
- [x] Tích hợp `InputGuard` tại cổng tiếp nhận đầu tiên của `_chat_internal` và `process_brain_logic`.
- [x] Tích hợp `InputGuard` vào `GuardrailHandler.handle` làm lá chắn vòng trong.
- [x] Nâng cấp `_sanitize_response` để phát hiện rò rỉ prompt nội bộ và thay bằng fallback an toàn.
- [x] Kiểm tra AST cả 4 file đạt Syntax OK.

---

# Bảo mật Cấp Quân Đội Helen (Military-Grade Audit — 12 fixes)

## Kế hoạch (PROPOSE đã duyệt)

### Priority 1 (CRITICAL + HIGH)
- [x] **[C-1]** Enforce giá từ DB: loại `p_raw.get("price")` khỏi PricingEngine, dùng `p_map`/`v_map` từ DB độc quyền.
- [x] **[C-2]** Sanitize `product_metadata` trước khi nhúc vào LLM context: strip HTML, giới hạn 500 ký tự, scan qua `InputGuard`.
- [x] **[H-1]** Thêm `cap_cart_items` field validator trong `SupportRequest` (max 50 items, cắt ngay tại Pydantic gate).
- [x] **[H-2]** Scan lịch sử chat giải mã qua `input_guard.validate()` trong `_fetch_chat_context` trước khi inject vào LLM.
- [x] **[H-3]** Mở rộng `_SYSTEM_LEAK_PATTERNS` (7 patterns), xóa false-positive `bắt buộc phải`.
- [x] **[H-4]** Fix bare `except: return ""` → `except Exception as _e: logger.warning(...)`.
- [x] **[H-5 - Hang Fix]** `trinity_bridge.py`: Áp dụng Global Timeout Enforcer. Track `start_time`, nếu `remaining_t <= 0` chặn hoàn toàn vòng lặp fallback models. Đảm bảo cam kết thời gian phản hồi (chặn đứng lỗi "xử lý vô tận").
- [x] **[H-6 - Hang Fix]** `lead_extractor.py`: Thêm `timeout=12.0` vào `trinity_bridge.run` (cũ là 90s mặc định -> gây treo queue).
- [x] **[H-7 - Hotfix]** `input_guard.py`: Whitelist thẻ `[system_consult]` (sử dụng Negative Lookahead regex) để không block tính năng tư vấn chuyên sâu của nút Quick Reply.

### Priority 2 (MEDIUM + LOW)
- [x] **[M-1]** Trusted IP resolution: ưu tiên `x-real-ip` (Nginx-inject), không tin `x-forwarded-for` có thể giả mạo.
- [x] **[M-2]** Mask phone trong `urgent_support` signal: `{phone[:3]}****{phone[-3:]}`.
- [x] **[M-3]** Validate UUID format cho `before_id` trước DB query.
- [x] **[M-4]** Thêm `max_age=86400*30` (30 ngày) cho session cookie.
- [x] **[L-1]** Thay "sếp" → "Quý khách" trong error messages của controller.
- [x] **[L-2]** Strip HTML + trim `name`/`short_description` trước khi inject vào LLM context.

---

# Task: Khắc phục Thiếu Quà tặng trên Trang Success Đơn hàng (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Backend Data Fix]** Viết script Python để cập nhật trực tiếp DB:
  - Cập nhật trường `attributes` của ProductVariant `v_ea1b5d6f82ea` ("Dứt điểm") để lưu quà tặng chuẩn: `"gifts": [{"name": "Miccosmo Beppin Body Virgin White Serum 30g (Tặng thêm)", "qty": 1, "image": "/uploads/2026/04/535e0488-bca7-4035-935d-a8c3c022ab63.webp"}]`.
  - Cập nhật đơn hàng lỗi `5464b1da-4196-4302-b7a1-69351ff7319b` (SĐT `0949901122`) để bổ sung thông tin quà tặng vào trong item và `order_metadata` giúp dữ liệu flow chính thống từ DB.
- [x] **[Frontend Desktop Success]** Cập nhật `/frontend/src/routes/(client)/(store)/checkout/success/[id]/+page.svelte`:
  - Sửa lỗi hiển thị ảnh sản phẩm (sử dụng `item.image_url || item.image` thay vì chỉ check `item.image_url` cũ làm hiển thị icon hộp các-tông `📦`).
  - Thiết kế khu vực hiển thị quà tặng khuyến mãi đính kèm của từng sản phẩm ngay bên dưới tên sản phẩm với phong cách "Glassmorphism" cao cấp (nền đỏ/hồng nhạt mịn màng, icon Hộp quà `Gift` từ Lucide, chữ đỏ đậm sắc nét).
  - Ép kiểu tĩnh 100% (cấm dùng `any`).
- [x] **[Frontend Mobile Success]** Cập nhật `/frontend/src/lib/components/mobile/sections/SuccessMobile.svelte`:
  - Đồng bộ logic hiển thị quà tặng với giao diện Mobile: bổ sung khối danh sách quà tặng cực kỳ tinh tế và nhỏ gọn dưới mỗi sản phẩm.
  - Sửa lỗi hiển thị ảnh sản phẩm trên mobile (hiển thị hình ảnh thay vì chỉ có tên sản phẩm thô sơ).
- [x] **[Kiểm tra & Nghiệm thu]** Chạy `svelte-check` để đảm bảo type-safety tuyệt đối, kiểm tra log và quay video visual giao diện sau khi sửa để xác thực.

---

# Task: Hiển thị Voucher & Chi tiết Giảm giá trên Trang Success (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Frontend Price Calc Fix]** Khắc phục lỗi dual-key resolver cho `voucherDiscount`, `comboDiscount`, và `shippingFee` ở cả trang Desktop và Mobile bằng cách kiểm tra cả `order_metadata` và `orderMetadata` từ API để hiển thị đúng số tiền được chiết khấu thay vì mặc định về 0.
- [x] **[Frontend Desktop Display]** Hiển thị danh sách Voucher đã áp dụng (`voucher_ids`) dưới dạng các nhãn vé Coupon màu đỏ/hồng nhạt nét đứt (`🎟️ CODE`) sang trọng, tăng tính minh bạch.
- [x] **[Frontend Mobile Display]** Tích hợp bảng phân rã giá chi tiết (Tạm tính, Vận chuyển, Vouchers áp dụng) vào trang Mobile Success giúp giao diện minh bạch và đồng nhất với bản Desktop.

---

# Task: Căn giữa và Thu sát Figcaption sát ảnh Mô tả Sản phẩm (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Frontend Desktop Align]** Bổ sung luật `:global(.prose-osmo figcaption)` trong `Desktop.svelte` để căn giữa chú thích, định dạng màu sắc `#6b7280` và font in nghiêng.
- [x] **[Frontend Desktop Margin Fix]** Tối ưu khoảng cách margin của hình ảnh và hình bao `figure` (`margin-bottom: 0.25rem`) giúp chú thích sát lên hình ảnh.
- [x] **[Frontend Mobile Align]** Đồng bộ luật CSS tương tự vào `Mobile.svelte` và `ProductMobileSpecs.svelte` để căn giữa và thu hẹp khoảng cách chú thích dưới hình ảnh trên giao diện mobile.
- [x] **[Quy trình quản trị]** Hoàn thiện bằng chứng trong `walkthrough.md`.

---

# Task: Khắc phục vỡ layout / xuống dòng số thứ tự Bước 3 (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Analysis]** Xác định nguyên nhân do thẻ `<p>` block-level bẻ dòng số thứ tự `::before` của thẻ `<li>`.
- [x] **[Frontend Style Fix]** Bổ sung thuộc tính `display: inline !important` và `margin-bottom: 0 !important` cho `:global(.prose-osmo li p)` trong `Desktop.svelte`, `Mobile.svelte`, và `ProductMobileSpecs.svelte`.
- [x] **[Quy trình quản trị]** Hoàn thành tài liệu chứng thực trong `walkthrough.md`.

---

# Task: Hardening layout Box Cam Kết "3 Không" (Commitment Box) (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Analysis]** Phân tích box Cam kết bị vỡ layout do tiêu đề "LÀNH TÍNH & AN TOÀN" bị nén và chữ bị cắt ngắn `...` (truncate) vì text subtitle quá dài.
- [x] **[Desktop Layout Hardening]** Chuyển đổi header box trong `Sections.svelte` và `Description.svelte` sang `flex-col sm:flex-row`, áp dụng `whitespace-nowrap shrink-0` cho tiêu đề và gỡ bỏ `truncate` ở các dòng nội dung để cho phép wrap tự nhiên.
- [x] **[Mobile Layout Hardening]** Đồng bộ và tối ưu hóa hiển thị box Cam kết trong `ProductMobileSpecs.svelte` để tránh co nén chữ trên thiết bị di động.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Khắc phục lỗi hiển thị/rò rỉ bảng Markdown từ AI (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Backend Safety Net]** Viết bộ chuyển đổi regex `_md_table_to_html` để biến đổi các bảng Markdown (`| --- |`) thành các bảng HTML chuẩn (`<table>`) trong kết quả trả về của AI.
- [x] **[Integration]** Tích hợp bộ chuyển đổi này vào hàm `clean_ai_html` của `NeuralRewriter` và `PlagiarismRefiner` để xử lý triệt để bất kể AI có bất tuân chỉ dẫn prompt.
- [x] **[Unit Testing]** Viết test case `backend/tests/unit/test_md_table_converter.py` chạy thử nghiệm để chứng minh thuật toán hoạt động hoàn hảo và không gây hồi quy (regression).
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Loại bỏ hoàn toàn Box Cam kết ra khỏi hệ thống (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Backend Instruction Fix]** Cập nhật `rewriter.py` loại bỏ phần `<h2>Cam kết</h2>` và các chỉ thị hướng dẫn AI sinh ra khối cam kết ở cuối mô tả sản phẩm.
- [x] **[Backend Post-Processing]** Sửa đổi `NeuralRewriter.clean_ai_html()` để tự động lọc bỏ bất cứ khối `Cam kết` nào được sinh ra bởi AI khi viết lại sản phẩm.
- [x] **[Frontend Global Elimination]** Sửa đổi hàm `parseDescriptionAndCommitments` trong `product.ts` để luôn trả về `commitments: null` và tự động dọn sạch các thẻ cam kết cũ có sẵn trong Database, giúp ẩn triệt để Box Cam kết trên giao diện Desktop và Mobile mà không làm vỡ các phần layout khác.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Khắc phục nút đặt hàng che nội dung trên Mobile Product Details Modal (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Frontend Layout Fix]** Phân tích và khắc phục lỗi overlap của nút đặt hàng (CTA) trên Mobile Product Details Modal (`MobileProductDetailsModal.svelte`):
  - Giải thích rõ tại sao `margin-bottom: 20px` trên `.elite-prose` không có tác dụng.
  - Tích hợp thêm một khoảng đệm an toàn (`div` spacer với chiều cao `120px` hoặc `h-32`) ở cuối cùng của container cuộn (`contentRef`) để chừa đủ khoảng trống cho nút CTA bay lơ lửng (`absolute bottom-10` cao `65px`).
- [x] **[Syntax Verification]** Chạy `svelte-check` hoặc phân tích tĩnh để đảm bảo mã Svelte 5 không dính lỗi cú pháp.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Thu hẹp phạm vi đọc TTS chỉ đọc vùng mô tả chi tiết (.elite-prose) (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Frontend TTS Scope Fix]** Cập nhật logic lấy dữ liệu text trong hàm `toggleSpeech` của `MobileProductDetailsModal.svelte`:
  - Thay vì lấy toàn bộ `contentRef.innerText` (làm đọc cả tên thương hiệu, xuất xứ, mã vạch, thành phần phụ), ta sẽ chỉ lấy `.elite-prose` bằng truy vấn `.querySelector('.elite-prose')`.
- [x] **[Storefront Mobile TTS Integration]** Tích hợp Web Audio TTS Engine chuyên nghiệp vào `ProductMobileSpecs.svelte` (nằm trong `Mobile.svelte`):
  - Thiết lập đầy đủ trạng thái `isReading`, `isBuffering`, `currentAudio` và các hàm `toggleSpeech`, `stopSpeech`, `sanitizeTtsText`.
  - Thiết kế nút **Neural Voice Capsule** nằm sát ngay cạnh tiêu đề "Chi tiết" ở dạng flex layout cực kỳ thoáng và cân đối.
  - Bổ sung hiệu ứng CSS giọng nói chuyển động.
- [x] **[Syntax Verification]** Chạy `svelte-check` để đảm bảo không lỗi kiểu hoặc cú pháp Svelte 5.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Loại bỏ figcaption (chú thích ảnh) khỏi nội dung đọc TTS (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Modal & Page TTS Scoping Fix]** Cập nhật logic trích xuất văn bản trong cả hai file:
  - `MobileProductDetailsModal.svelte`
  - `ProductMobileSpecs.svelte`
  - Phương pháp: Clone node trong bộ nhớ (`cloneNode(true)`), duyệt qua và xóa bỏ tất cả các thẻ `figcaption` trước khi lấy `.innerText`. Đảm bảo không ảnh hưởng đến giao diện thật.
- [x] **[Syntax Verification]** Chạy `svelte-check` để đảm bảo không lỗi kiểu hoặc cú pháp Svelte 5.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Chuẩn hóa phát âm số La Mã (I, II, III...) sang tiếng Việt cho TTS (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Roman Numerals Translation]** Cập nhật hàm `sanitizeTtsText` trong cả hai file:
  - `MobileProductDetailsModal.svelte`
  - `ProductMobileSpecs.svelte`
  - Phương pháp: Định nghĩa bảng tra cứu Roman numerals từ XX xuống I và dùng biểu thức chính quy (Regex) với ranh giới từ `\b` để thay thế chính xác các ký tự số La Mã viết hoa độc lập thành chữ số tiếng Việt tương ứng (VD: II -> hai).
- [x] **[Syntax Verification]** Chạy `svelte-check` để đảm bảo không lỗi kiểu hoặc cú pháp Svelte 5.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Nút nghe chỉ hiện khi scroll xuống phần mô tả chi tiết (.elite-prose) ở Modal (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Scroll Visibility TTS Button]** Cấy thêm biến trạng thái scroll và logic hiển thị nút nghe tại `MobileProductDetailsModal.svelte`:
  - Khai báo state `showSpeechButton` và reactive derived rune `shouldShowSpeech = $derived(showSpeechButton || isReading || isBuffering)`.
  - Trong hàm `handleScroll`, lấy vị trí offset `.elite-prose` và tự động kích hoạt `showSpeechButton = target.scrollTop >= proseEl.offsetTop - 150`.
  - Tích hợp hiệu ứng CSS Smooth Transition (`opacity-0 scale-90` sang `opacity-100 scale-100`) trên nút Neural Voice Capsule để tránh hiện tượng layout shift và mang lại cảm giác mượt mà cực cao.
- [x] **[Syntax Verification]** Chạy `svelte-check` để đảm bảo không lỗi kiểu hoặc cú pháp Svelte 5.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

# Task: Làm sạch và tối ưu hóa backend/main.py (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Environment Loading]** Tải file cấu hình `.env` động bằng cách tìm đúng thư mục gốc thông qua `Path(__file__).resolve().parents[1]` và tự động fallback về `load_dotenv()` nếu không tìm thấy file thay vì crash server bằng `FileNotFoundError`.
- [x] **[Logging & Warnings]** Gộp và cấu hình lọc các cảnh báo thư viện như `pydantic` hay `pydantic_ai` một cách gọn gàng; tối ưu việc nạp logger namespaced.
- [x] **[CORS Optimization]** Xây dựng hàm helper `_build_allowed_origins` để kiểm soát CORS origin động, bảo mật và tin cậy cao hơn.
- [x] **[Rate Limit Config]** Chuyển đổi định cấu hình giới hạn tần suất yêu cầu sang kiểu `timedelta(minutes=1)` chuẩn chỉ và có kiểu tĩnh an toàn.
- [x] **[Routing Grouping]** Tách biệt và gom nhóm các Router thành các mảng rõ ràng (`admin_routes`, `client_routes`, `public_routes`) và gộp lại trong instance `Litestar`.
- [x] **[Middleware Ordering]** Tối ưu hóa thứ tự thực thi của Middleware (`AuthMiddleware` lên đầu) để lọc request không an toàn trước khi đi vào các tầng sâu hơn.

---

# Task: Cấu hình full width cho .metric-desc trên Mobile (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Frontend Style Fix]** Bổ sung thuộc tính `width: 100%` và `max-width: 100%` cho `.metric-desc` lồng bên trong `.hero-center-layout` dưới media query `@media (max-width: 768px)` trong file `HeroBanner.css`.
- [x] **[Quy trình quản trị]** Hoàn thành tài liệu chứng thực trong `walkthrough.md`.

---

# Task: Loại bỏ padding/margin left của metrics container (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] **[Frontend Style Fix]** Cập nhật `HeroBanner.css`: Thay đổi `padding-left: 1.5rem;` thành `padding-left: 0;` cho `.metrics-arc-container` ở `@media (min-width: 768px)`.
- [x] **[Quy trình quản trị]** Cập nhật tài liệu minh chứng trong `walkthrough.md`.

---

# Task: Tối ưu responsive HeroBanner iPad Air & iPad Mini (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] Phân tích và đưa ra phương án fix cho kích thước `@media (min-width: 768px) and (max-width: 820px)`.
- [x] Tối ưu hóa CSS (`HeroBanner.css`) theo quy tắc sạch sẽ, gộp breakpoint, loại bỏ code thối nhưng giữ lại `!important` để ghi đè Tailwind.
- [x] Tăng kích thước font chữ và kích thước hình ảnh của cinematic-frame sau khi phát hiện quá nhỏ.
- [x] Điều chỉnh `padding-top: 0 !important` cho màn hình iPad Mini 768px (`@media (max-width: 768px)`).
- [x] Đảm bảo không thay đổi layout gốc, giữ nguyên các thuộc tính cấu trúc trên desktop (>1024px) và mobile (<=768px).

---

# Task: Tối ưu hiển thị Slide Biến Thể Sản Phẩm trên Tablet (768px, 820px, 1024px) (Elite V2.2)

## Kế hoạch (PROPOSE)
- [x] Cập nhật `OfferGrid.css` trong block `@media (max-width: 1024px)` để bật flex container cho `.package-grid > div` giúp tự động giãn chiều cao.
- [x] Gỡ bỏ giới hạn chiều cao tĩnh bằng `height: auto !important` cho `.package-grid > div` và `.package-card`.
- [x] Cấu hình chiều rộng linh hoạt `width: 85%; max-width: 420px; min-width: 290px;` cho `.package-grid > div` trên tablet/mobile.
- [x] Thiết lập `flex-grow: 1` cho `.package-card` để tự động kéo giãn hết cỡ chiều cao cột và đẩy cụm CTA xuống đáy đồng bộ.
- [x] Giảm kích thước text header chính `.offer-grid-headline` xuống `clamp(20px, 4vw, 30px) !important` trên tablet/mobile.
- [x] Giảm chiều cao hình ảnh `.variant-image-hero` từ `280px` xuống `220px` trên tablet/mobile.

