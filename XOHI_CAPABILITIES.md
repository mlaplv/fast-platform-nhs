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

## 4. HỆ THẦN KINH CHỦ ĐỘNG (V56.5 - NEW)

### ⚡ Proactive Event Bus (0-Latency)

XoHi không còn "quét bị động" (polling). Hệ thống sử dụng trục xương sống **Internal Event Bus**:

- **Phản ứng 0 giây:** Mọi hành động từ khách (Đặt hàng, Hủy đơn) được đẩy về bộ não XoHi ngay lập tức.
- **XoHi Responder:** Tự động phân tích và đưa ra phản hồi/cảnh báo tức thì.

### 🛡️ Anti-Spam Shield (Lá chắn Đối thủ)

Bảo vệ ngân sách Marketing và Stock hàng trước các cuộc tấn công phá hoại:

1.  **Device Fingerprinting:** Nhận diện "vân tay trình duyệt". Dù đối thủ đổi IP, XoHi vẫn nhận ra thiết bị cũ.
2.  **Velocity Guard:** Chặn đứng tool/robot đặt đơn hàng loạt (Flood attack).
3.  **Auto-Isolation:** Tự động gắn tag `SPAM` cho các đơn hàng nghi vấn, không cho phép trừ tồn kho thật và cảnh báo đỏ cho sếp.

### ⚡ Zero-Cold-Start (Instant Wake)

- Embedding models & Intent centroids được tải ngay khi boot app.
- **Response Time:** <100ms cho câu lệnh đầu tiên.

### 🇻🇳 Smart Vietnamese Search (Unaccent)

- Hỗ trợ tìm kiếm tiếng Việt không dấu. Match "ao thun" -> "Áo thun".
- Áp dụng cho Sản phẩm và Khách hàng.

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
