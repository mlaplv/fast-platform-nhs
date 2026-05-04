# Báo Cáo Kiến Trúc Bảo Mật - Fast Platform (Elite V2.2)

> [!IMPORTANT]
> Tài liệu này mô tả chi tiết các chốt chặn bảo mật, phân quyền và chiến lược chống tấn công (Từ Botnet đến AI) hiện đang được áp dụng trên Fast Platform, đặc biệt tập trung vào phân khu Quản trị (`admin.osmo`) và Bảo mật Dữ liệu Khách hàng tại Storefront.

---

## 🛡️ 1. Bảo Mật Cấp Admin (`admin.osmo`)

Kiến trúc bảo mật Admin được thiết kế theo mô hình **Zero-Trust** và **Defense-in-Depth** (Phòng thủ chiều sâu), cách ly hoàn toàn với luồng truy cập public.

### A. Cô Lập Không Gian Mạng (Domain Guard V2.2)
- **Kiểm soát Origin Tuyệt đối:** Middleware `DomainGuardMiddleware` giám sát chặt chẽ Header `Host` và `X-Forwarded-Host`. Mọi truy cập vào các API đặc quyền (`ADMIN_ONLY_PREFIXES` như `/api/v1/users`, `/api/v1/settings`) **bắt buộc** phải xuất phát từ `admin.osmo` hoặc `api.osmo`.
- **Chặn Đột Biến Dữ Liệu (Mutation Lockdown):** Các tài nguyên dùng chung như Sản phẩm, Bài viết chỉ cho phép Storefront (`osmo`) thực thi lệnh Đọc (GET). Mọi thao tác Ghi/Sửa/Xóa (`POST`, `PATCH`, `PUT`, `DELETE`) bị chặn đứng nếu không đến từ Admin Domain.
- **Frontend Tenant Routing:** Trên SvelteKit (`hooks.server.ts`), hệ thống bẻ lái (Redirect 308) mọi nỗ lực truy cập các Route Quản trị (`/admin/*`) từ Storefront Domain nhằm ngăn chặn triệt để "Tenant Leakage" (Rò rỉ giao diện).

### B. Phân Quyền & Quản Trị Phiên (PBAC & Stateless Revocation)
- **Đánh Giá PBAC Siêu Tốc (<10ms):** `PolicyEvaluator` xác thực quyền hạn linh hoạt qua sự kết hợp giữa **Role** và **Permission** cực kỳ chi tiết (VD: `category:write`, `order:read`).
- **Thu Hồi Quyền Tức Thì (Instant Revocation):** Bất chấp việc sử dụng Stateless JWT, các thao tác thay đổi dữ liệu luôn bị kiểm tra `security_stamp` tại Database. Kẻ gian dù lấy cắp được Token vẫn sẽ bị chặn đứng ngay lập tức nếu Admin đổi mật khẩu hoặc thu hồi quyền truy cập.
- **Đặc Quyền Kỹ Thuật:** Role `SUPER_ADMIN` được thiết kế để bypass toàn bộ Domain Guard và PBAC, phục vụ cho kịch bản "Live Edit" tức thời.

### C. Chống Khai Thác & Tấn Công Nút Cổ Chai (Anti-DDoS & Exploit)
> [!CAUTION]
> Các chốt chặn này được kích hoạt ở tầng Network/ASGI, bảo vệ các tiến trình Core và Worker của AI khỏi tình trạng ngập lụt bộ nhớ.

- **Chống Bom JSON (OOM Protection):** `BodyLimitMiddleware` giới hạn và cắt đứt các Payload vượt quá **10MB** trước khi Pydantic tiến hành Parse dữ liệu.
- **Chống Treo Hệ Thống (Deadlock Shield):** `StallDetectorMiddleware` ngắt kết nối và trả về `504 Gateway Timeout` đối với bất kỳ request nào treo quá 10 giây (ngoại trừ các endpoint Streaming AI/Voice).
- **Kiểm Toán Pháp Y (Forensic Audit):** `AuditMiddleware` lưu lại toàn bộ lịch sử thay đổi (Mutation) dưới dạng JSON chuẩn Forensic gồm `actor_id`, `action`, `status`, `ms`, và `domain` để phục vụ điều tra an ninh.

---

## 🛡️ 2. Bảo Mật Client & Dữ Liệu Tài Khoản

Hệ thống Storefront được thiết kế để cân bằng giữa trải nghiệm mua sắm mượt mà ("Liquid Glass UX") và sự an toàn dữ liệu cá nhân (PII) cao nhất.

### A. Quản Trị Danh Tính Khách Hàng
- **Cookie Bảo Mật Kép:** Access Token được thiết lập qua Cookie với cờ `HttpOnly`, `Secure` và `SameSite=Lax`, bị ràng buộc cứng với Root Domain (`.osmo`) để chặn XSS (Cross-Site Scripting).
- **Trình Giám Sát Tự Hủy (Watchdog Timer):** Tiến trình ngầm trên trình duyệt (`permissions.svelte.ts`) liên tục kiểm tra hạn sử dụng (EXP) của JWT mỗi 10 giây. Khi Token hết hạn, Watchdog tự động kích hoạt chiến dịch "Tiêu thổ" - dọn sạch `localStorage`, `sessionStorage`, `Cookies` và điều hướng về trang đăng nhập.
- **Xác Thực Không Mật Khẩu (Passwordless OTP):** Mã OTP sinh ra bằng thuật toán sinh số ngẫu nhiên chuẩn mã hóa (`secrets`), tuổi thọ ngắn (5 phút), mã hóa Hash tại DB và được xử lý qua Background Worker (Redis/Arq) nhằm chống nghẽn I/O.

### B. Mộc Danh Tính Mua Hàng (Identity Shield V3.0)
Đây là kiến trúc bảo vệ cốt lõi cho kịch bản mua hàng không cần đăng nhập (Stealth Checkout):
> [!TIP]
> **Identity Shield V3.0** đảm bảo khách hàng tra cứu đơn hàng nhanh chóng mà không làm rò rỉ dữ liệu cá nhân cho kẻ tấn công (dù kẻ tấn công có biết mã đơn hàng và số điện thoại).

- Ngay khi đặt hàng thành công, hệ thống cấy một Cookie mã hóa `__ox` (`HttpOnly=True`, `Secure=True`) vào trình duyệt của khách hàng.
- Khi tra cứu trạng thái đơn hàng (yêu cầu bí mật là Số Điện Thoại), hệ thống đối chiếu Cookie `__ox`.
- **Nếu KHÔNG khớp thiết bị (Untrusted Device):** Tự động che giấu (Masking) Tên và Địa Chỉ của khách hàng, chỉ hiển thị tiến trình giao hàng.

### C. Chống Gian Lận Đơn Hàng (Quân Sự & AI Level)
Hệ thống `AntiSpamService` là lá chắn thép chống lại Botnet và đối thủ cạnh tranh tọc mạch:
- **Khóa Mạng Động (Atomic Lua Velocity):** Sử dụng LUA Script trên Redis để thực thi đếm giới hạn (Rate Limit) nguyên tử tuyệt đối. Chống lại hoàn toàn các đợt tấn công **Concurrent Botnet** (nhiều IP spam cùng 1 mili-giây).
- **Phát Hiện Đội Hình Spam (Cluster Detection):** Tự động cộng điểm rủi ro nếu phát hiện nhiều IP xài chung 1 số điện thoại (Identity Rotation) hoặc 1 IP bắn lệnh mua quá nhanh (<5s) (Rapid Fire).
- **Thẩm Định AI (Trinity Bridge):** 
  > [!WARNING]
  > Khi điểm rủi ro nằm trong vùng xám (40 - 70 điểm), Agent AI (`trinity_bridge`) sẽ được triệu hồi. 
  
  AI phân tích ngữ nghĩa của Tên và Địa chỉ để phát hiện "Hành vi gõ phím bừa" (Keyboard Mashing) hoặc chứa các từ ngữ lăng mạ/troll của đối thủ cạnh tranh, từ đó đưa ra quyết định Block cuối cùng.

### D. Hệ Thống Giám Sát Tự Trị (Anomaly Detector)
Một tiến trình Scalar Query (tối ưu hóa RAM, bỏ qua ORM Hydration) chạy định kỳ để giám sát "nhịp tim" của nền tảng:
- Cảnh báo bùng nổ đơn hàng giả mạo (Order Volume Spike).
- Cảnh báo tấn công hủy đơn hàng (Cancel Spike).
- Cảnh báo sụt giảm doanh thu bất thường (< 70% so với hôm qua).
- Giám sát độ trễ phản hồi của AI (AI Latency Spike).

---

> _Báo cáo được thực hiện bởi AI Agent 2026 - (2026-04-25)_
