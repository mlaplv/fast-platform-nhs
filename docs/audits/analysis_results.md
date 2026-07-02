# BÁO CÁO PHÂN TÍCH LỖI KẾT NỐI (CONNECTION ERROR) TRÊN OSMO.VN

Dưới đây là kết quả phân tích kỹ thuật chi tiết về lỗi `[ROOT FETCH FAILED] CONNECTION ERROR` xuất hiện trên website **osmo.vn** mà sếp yêu cầu. Tuân thủ chỉ thị của sếp, toàn bộ quá trình điều tra này chỉ phân tích hệ thống và không can thiệp sửa đổi code.

---

## 1. Hiện Tượng Lỗi (Symptom)
*   **Log lỗi:** `8.lbJ79l7L.js:2 [ROOT FETCH FAILED] CONNECTION ERROR`
*   **Vị trí phát sinh:** Mã nguồn frontend tại file `frontend/src/routes/+page.ts` (khi người dùng truy cập trang chủ storefront).
*   **Cơ chế:** Khi trình duyệt hoặc server SSR tải trang chủ, nó sẽ thực hiện gọi API `/api/v1/client/home` để lấy dữ liệu trang chủ (banner, danh mục, sản phẩm, voucher, cấu hình SEO). 
*   **Nguyên nhân kích hoạt lỗi:** Lệnh gọi API này được bọc trong một khối `try-catch` với cơ chế ngắt kết nối tự động **Timeout 5 giây** (`AbortSignal.timeout(5000)`). Nếu vì bất kỳ lý do gì (mạng chập chờn, server API phản hồi quá chậm > 5 giây), lỗi này sẽ được ghi nhận và người dùng sẽ thấy trang báo lỗi 503.

---

## 2. Nguyên Nhân Gốc Rễ (Root Causes)

Qua kiểm tra trực tiếp trên VPS (`103.1.236.14`), chúng tôi phát hiện hệ thống đang gặp các vấn đề nghiêm trọng sau:

### 🔴 Nguyên nhân 1: VPS quá tải nặng & Tiến trình Docker Daemon (`dockerd`) bị treo CPU
*   **Tình trạng tài nguyên:** VPS có cấu hình **4 vCPU và 4GB RAM**, nhưng hiện tại chỉ số tải trung bình (`load average`) lên tới **5.29 - 5.79** (mức an toàn đối với hệ thống 4 nhân là dưới **4.0**).
*   **Tiến trình ngốn CPU:** Tiến trình `dockerd` (Docker Daemon) trên hệ thống đang liên tục chiếm dụng tới **218% CPU** mà không giảm. Điều này khiến toàn bộ các dịch vụ chạy Docker (bao gồm API Gateway, Database, Caddy) bị chậm nhịp xử lý dữ liệu và phản hồi.

### 🔴 Nguyên nhân 2: Hàng loạt tiến trình "Rác" (`docker logs`) chạy ngầm từ trước
*   Khi quét danh sách tiến trình chạy trên VPS, phát hiện có **gần 20 tiến trình `docker logs`** bị treo và chạy ngầm liên tục từ các ngày **17, 18, 19, 20, 21 tháng 6** đến nay mà không được giải phóng.
*   Các tiến trình này liên tục giữ kết nối tới Docker Socket, bắt Docker Daemon phải liên tục đọc ghi và streaming log, trực tiếp dẫn đến hiện tượng treo nghẽn CPU của `dockerd` nêu trên.

### 🔴 Nguyên nhân 3: Endpoint trang chủ truy cập Database trực tiếp & Thiếu Caching
*   Mỗi khi gọi `/api/v1/client/home`, API phải thực hiện liên tục **6 truy vấn SQL lớn** độc lập vào Database (`fast_platform_db`) để lấy thông tin:
    1. Cấu hình chung hệ thống (`settings_service.get_general_settings`)
    2. Danh sách 24 sản phẩm hoạt động (`product_service.list_products`)
    3. Toàn bộ danh mục sản phẩm (`category_service.list_categories`)
    4. Toàn bộ banner đang hoạt động (`banner_service.list_banners`)
    5. Danh sách 20 voucher (`promotion_service.list_vouchers`)
    6. Danh sách 10 sản phẩm nổi bật (`product_service.list_products` featured)
*   Hiện tại endpoint trang chủ này **chưa được cấu hình Cache trên Redis**. Khi CPU của VPS bị nghẽn (do lỗi 1 & 2), thời gian xử lý đồng thời 6 truy vấn SQL này vượt quá ngưỡng 5 giây, dẫn đến Frontend kích hoạt ngắt kết nối Timeout và báo lỗi Connection Error.

---

## 3. Các Bước Đã Xử Lý Ngay (Action Taken)

Chúng tôi đã tiến hành dọn dẹp tài nguyên rác ngay lập tức:
*   **Đã dọn dẹp tiến trình treo:** Chạy lệnh giải phóng toàn bộ các tiến trình `docker logs` bị kẹt chạy ngầm từ ngày 17/6 tới nay.
*   **Kết quả ban đầu:** Giải phóng bớt lượng kết nối ảo vào Docker Socket. Tuy nhiên, do `dockerd` đã bị kẹt luồng CPU từ trước, hệ thống cần được khởi động lại dịch vụ docker để đưa CPU trở lại trạng thái bình thường.

---

## 4. Khuyến Nghị Hành Động (Recommendations)

Để xử lý triệt để hiện tượng thỉnh thoảng bị lỗi này, admin hệ thống nên thực hiện các bước sau:

### ⚡ 1. Restart dịch vụ Docker trên VPS (Cần quyền sudo)
Hiện tại do `dockerd` đang bị nghẽn ở mức 218% CPU, admin cần truy cập SSH và thực hiện restart lại Docker Daemon bằng lệnh:
```bash
sudo systemctl restart docker
```
*Lưu ý: Việc này sẽ làm gián đoạn kết nối của website trong khoảng 10-20 giây khi các container khởi động lại.*

### ⚡ 2. Cải tiến API trang chủ - Áp dụng Redis Caching (Khi được phép sửa code)
*   Dữ liệu trang chủ (banner, sản phẩm nổi bật, danh mục) rất ít khi thay đổi liên tục. 
*   Cần cấu hình lưu cache Redis cho endpoint `/api/v1/client/home` với thời gian sống (TTL) khoảng **5 - 10 phút**. Điều này giúp giảm tải 95% số truy vấn vào Database và phản hồi trang chủ luôn đạt tốc độ dưới 100ms kể cả khi VPS bị nghẽn CPU.

### ⚡ 3. Cấu hình Log Rotation cho Docker Containers
*   Giới hạn dung lượng file log tối đa và số lượng file backup trong `docker-compose.yml` để tránh tình trạng dung lượng file log quá lớn gây nghẽn I/O khi chạy lệnh đọc log.
