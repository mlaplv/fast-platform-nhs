# XOHI NEXUS CAPABILITIES (V56.0)

> Tóm tắt toàn bộ năng lực của Trợ lý XoHi — Từ nhận diện cơ bản đến tự hành cao cấp.

---

## 1. TRUY VẤN DỮ LIỆU (DATA_QUERY/READ)

XoHi hỗ trợ báo cáo nhanh bằng giọng nói cho 6 nhóm thực thể chính bằng cách quét trực tiếp Database (Zero-ORM):

- **Doanh thu (Revenue):**
  - "Doanh thu hôm nay bao nhiêu?"
  - "Doanh số tháng này thế nào sếp?"
  - "Tổng thu nhập tuần này."
- **Đơn hàng (Orders):**
  - "Có bao nhiêu đơn hàng mới?"
  - "Đếm số đơn hàng đang chờ xử lý."
  - "Xem đơn hàng đã hủy hôm nay."
- **Sản phẩm (Products):**
  - "Kho còn bao nhiêu sản phẩm?"
  - "Có sản phẩm nào hết hàng không?"
  - "Thống kê tồn kho sản phẩm Áo thun."
- **Khách hàng & Nhân viên (Users):**
  - "Hệ thống có bao nhiêu nhân viên?"
  - "Tìm khách hàng tên Nguyễn Văn A."
  - "Tổng số tài khoản đang hoạt động."
- **Danh mục & Tin tức (Category/News):**
  - "Có bao nhiêu bài viết mới?"
  - "Thống kê danh mục sản phẩm."

---

## 2. ĐIỀU HƯỚNG GIAO DIỆN (UI_NAV)

XoHi điều khiển giao diện Dashboard thay sếp:

- **Biểu đồ:** "Mở biểu đồ doanh thu", "XoHi ơi, xem Chart."
- **Quản lý:**
  - "Vào trang đơn hàng."
  - "Mở quản lý sản phẩm."
  - "Xem danh sách khách hàng."
  - "Mở cấu hình XoHi."

---

## 3. THAY ĐỔI DỮ LIỆU TỰ HÀNH (MUTATE - MiniForm)

Giao thức Mini-Form (R65) giúp sếp ra lệnh thay đổi dữ liệu bằng giọng nói:

- **Thêm mới:** "Tạo sản phẩm tên là Áo khoác giá 500k."
- **Sửa đổi:** "Sửa tên khách hàng này thành Trần B."
- **Xóa bỏ:** "Xóa bài viết vừa rồi."
- **Cơ chế:** AI tự điền Form -> Hiện Modal -> Sếp chỉ cần nhấn **"Xác nhận"**.

---

## 4. SIÊU NĂNG LỰC TỰ HÀNH (V56.0 - NEW)

### 🛰️ Autonomous Heartbeat (Anomaly Detection)

Hệ thống tự động quét 15 phút/lần (Background Task) để cảnh báo sếp:

1.  **Ccancelled Spike:** Đơn hủy tăng >200% so với trung bình.
2.  **Volume Spike:** Lượng đơn hàng mới tăng đột biến.
3.  **Revenue Drop:** Doanh thu hôm nay thấp hơn 70% so với cùng giờ hôm qua.

- _Thông báo sẽ xuất hiện tại Heartbeat Sidebar._

### ⚡ Zero-Cold-Start (Instant Wake)

- Embedding models & Intent centroids được tải ngay khi boot app.
- **Response Time:** <100ms cho câu lệnh đầu tiên (không còn độ trễ startup).

### 🇻🇳 Smart Vietnamese Search (Unaccent)

- Hỗ trợ tìm kiếm tiếng Việt không dấu.
- "ao thun" match "Áo thun", "nguyen" match "Nguyễn".
- Áp dụng đồng bộ cho Sản phẩm và Khách hàng.

### 🧠 Modality Recovery & Memory

- **Inheritance:** Nhớ ngữ cảnh (Timeframe/Target) của câu hỏi trước.
- **STT Correction:** Tự học từ vựng sếp sửa để nắn chỉnh STT vĩnh viễn.

---

## 5. THÔNG SỐ KỸ THUẬT (V56.0)

- **Routing Tier:** T1 (Heuristic) -> T1.5 (Semantic) -> T2 (Agent Cloud).
- **Resource:** Encoder Singleton tiết kiệm ~180MB RAM.
- **Security:** RBAC Many-to-Many, Tenant Isolation 100%.

---

_V56.0: ARCHITECT PROFESSOR — XoHi Nexus Awakening._
