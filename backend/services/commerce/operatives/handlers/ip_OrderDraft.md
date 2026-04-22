# HELEN ORDER DRAFT PROTOCOL (IP-ORDERDRAFT) - ELITE V5.3

> **CHỈ THỊ TỐI CAO:** Quản lý giỏ hàng (Draft Order) là xương sống của tỷ lệ chuyển đổi (CR). Helen phải vận hành như một chuyên gia Shopee: Ghi nhớ bền bỉ, bù đắp thông tin thiếu hụt (Slot-filling), và chốt đơn ngay khi đủ dữ liệu (Shadow Checkout).

---

## 🧠 CƠ CHẾ GHI NHỚ (STATE MANAGEMENT)

Hệ thống sử dụng kiến trúc **Hybrid Persistence** để đảm bảo không bao giờ rơi vào lỗi "Mất trí nhớ" (Dementia Loop):

1.  **OrderDraft Model (Pydantic):** Chứa `items`, `customer_phone`, `customer_address`, `is_definite_intent`.
2.  **Redis Storage (L0 Cache):** Lưu trữ draft theo `session_id` với TTL 24h. Được truy xuất tức thì qua `xohi_memory`.
3.  **Chat History (L1 Recovery):** Nếu Redis gặp sự cố, `LeadExtractor` sẽ quét ngược 10 tin nhắn gần nhất để khôi phục SĐT/Địa chỉ.

---

## 🛠️ QUY TRÌNH XỬ LÝ 3 KỊCH BẢN (CORE CASES)

### 1️⃣ Khách cho SĐT - Thiếu Địa chỉ
- **Hành động:** `OrderHandler` trích xuất SĐT -> Lưu vào Draft.
- **Phản xạ:** 
    - Đánh dấu Draft là `Partial`.
    - Phản hồi: *"Dạ SĐT em lưu 1 bản rồi ạ. Anh/Chị cho em xin thêm **Địa chỉ cụ thể** để Helen gửi hàng về tận cửa luôn nhé! 🌸"*
- **Mục tiêu:** Giữ chân khách cung cấp nốt thông tin cuối cùng.

### 2️⃣ Khách cho Địa chỉ - Thiếu SĐT
- **Hành động:** `LocationResolver` chuẩn hóa địa chỉ -> Lưu vào Draft.
- **Phản xạ:**
    - Nếu địa chỉ mơ hồ (ví dụ: Phú Lâm), Helen hỏi xác nhận Tỉnh/Thành phố.
    - Nếu địa chỉ rõ ràng, phản hồi: *"Dạ địa chỉ thì Helen đã thấy rồi. Anh/Chị cho em xin thêm **Số Điện Thoại** để shipper liên lạc nha! 🌸"*

### 3️⃣ Khách cho cả SĐT & Địa chỉ (Full Info)
- **Hành động:** **Shadow Checkout (V3.0)** kích hoạt ngay lập tức.
- **Phản xạ:**
    - Tạo đơn hàng thực tế trong DB.
    - Xóa sạch Draft trong Redis (Cleanup).
    - Phản hồi: *"Dạ Helen chúc mừng Anh/Chị đã đặt hàng thành công! 🌸... Mã đơn: **XXXX**..."* kèm theo thông tin ngày giao dự kiến.

---

## ⚓ STICKY INTENT & SLOT-FILLING (V4.1)

Để tối ưu hóa trải nghiệm "Zero-Friction", Helen áp dụng giao thức **Sticky Intent**:

- **Khóa mục tiêu:** Một khi Draft đã có sản phẩm, Helen sẽ ưu tiên hiểu các tin nhắn tiếp theo là thông tin bổ sung cho đơn hàng (SĐT, Địa chỉ) thay vì quay lại bước tư vấn sản phẩm.
- **Deterministic Recovery:** Nếu khách nhắn lộn xộn (ví dụ: *"về địa chỉ 336/28/19 nguyễn văn luông, phú lâm 0949901122"*), hệ thống sẽ dùng Regex bóc tách SĐT ra khỏi chuỗi địa chỉ một cách chính xác tuyệt đối.

---

## 🚀 ĐỀ XUẤT NÂNG CAO (SALES ASSASSIN)

1.  **Upsell Combo (Martial Combo Protocol):** Nếu khách mua lẻ 1, Helen tự động gợi ý Combo 2+1 hoặc 4+1 để tối ưu giá.
2.  **Voucher Intelligence:** Luôn báo cho khách biết họ đã được áp dụng mã giảm giá tốt nhất hiện có trước khi chốt đơn.
3.  **Ambiguity Guard:** Khi gặp địa chỉ trùng tên ở nhiều tỉnh, phải dừng lại hỏi rõ Tỉnh/Thành phố thay vì mặc định sai lệch.

---
**Phiên bản:** Micsmo Elite V5.3 (Order Draft Intelligence)
**Cập nhật cuối:** 2026-04-22
**Tác giả:** Trinity Neural Core via Antigravity Agent
