# 🚀 Hướng Dẫn Vận Hành Hệ Thống Lan Truyền & Tương Tác (Viral 2026)

Tài liệu này chi tiết cách cấu hình và cơ chế hoạt động của bộ công cụ **Viral 2026** và chiến dịch **Share-to-Unlock** (Bảo mật cấp quân đội) trên nền tảng `osmo.vn`.

---

## 1. Bộ Công Cụ Tương Tác (Viral 2026 Core)

Mục tiêu: Tạo hiệu ứng FOMO (Sợ bỏ lỡ) và tăng uy tín sản phẩm (Social Proof) tức thì.

### 1.1. Lượt thích ban đầu (Social Proof)
- **Cơ chế:** Hiển thị số lượt thả tim trên thanh Viral Bar. 
- **Tác dụng:** Giúp khách hàng tin tưởng sản phẩm ngay khi vừa vào trang.
- **Cấu hình:** Nhập số lượng mong muốn tại ô `Lượt thích ban đầu`.

### 1.2. Đồng hồ Flash Sale
- **Cơ chế:** Đếm ngược thời gian thực đến thời điểm kết thúc.
- **Tác dụng:** Thúc đẩy hành vi chốt đơn nhanh chóng để hưởng ưu đãi.
- **Lưu ý:** Phải bật toggle `Kích hoạt` và chọn `Thời gian kết thúc`.

### 1.3. Thanh tiến trình Gamification
- **Cơ chế:** Hiển thị mục tiêu cộng đồng (ví dụ: "Đã có 800/1000 lượt chia sẻ").
- **Tác dụng:** Tạo tâm lý đám đông, khuyến khích khách hàng cùng nhau "mở khóa" phần thưởng lớn.

---

## 2. Chiến Dịch Share-to-Unlock (Elite V2.6 Security)

Đây là hệ thống được thiết kế để chống lại mọi hình thức gian lận (fake share, F12, replay attack).

### 2.1. Quy trình 3 bước (Intent-Verify-Unlock)
1. **Bước 1 (Intent):** Khách hàng nhấn nút "Chia sẻ". Client gửi request lên Server để tạo một `One-Time Token` được ký bằng HMAC-SHA256.
2. **Bước 2 (Verify):** Sau khi khách hàng thực hiện chia sẻ qua các nền tảng (Zalo, Facebook...), hệ thống sẽ xác thực Token. 
3. **Bước 3 (Unlock):** Chỉ khi Server xác nhận Token hợp lệ, mã Voucher thực sự mới được truy vấn từ Database và trả về cho Client.

### 2.2. Cơ chế Bảo mật "Quân đội"
- **HMAC-SHA256 Signing:** Token không thể bị giả mạo hay chỉnh sửa bởi người dùng.
- **Redis Rate Limiting:** Chặn các IP cố tình spam chia sẻ (Mặc định: 10 lần/giờ).
- **Anti-Replay Protection:** Mỗi token chỉ có giá trị sử dụng một lần và hết hạn sau 24h.
- **Data Isolation:** Tuyệt đối không để lộ mã Voucher hoặc ID Voucher trong mã nguồn HTML (Client side). Hệ thống chỉ trả về Token tạm thời.

---

## 3. Hướng Dẫn Cấu Hình Trong Admin Panel

Để kích hoạt cho một sản phẩm, hãy vào mục **Metadata** của sản phẩm đó:

1. **Bật Chiến dịch:** Chuyển trạng thái sang `Đang bật`.
2. **ID Voucher:** Nhập **chính xác** mã ID của Voucher đã tạo trong mục "Khuyến mãi" (Ví dụ: `VIRAL50K`).
3. **Tiêu đề Voucher (Label):** Nội dung hiển thị trên tem (VD: `Giảm 50.000₫`).
4. **Lời kêu gọi (CTA):** Nút bấm thu hút khách (VD: `Chia sẻ nhận quà ngay`).
5. **Nội dung mẫu (Share Text):** Soạn sẵn lời giới thiệu sản phẩm để khách chia sẻ (Copywriting mồi nhử).

---

## 4. Kiểm Tra & Vận Hành (Testing Checklist)

- [ ] Kiểm tra xem thanh Viral Bar có hiện số Likes không?
- [ ] Thử nhấn Chia sẻ: Cửa sổ chia sẻ có hiện đúng nội dung mẫu không?
- [ ] Sau khi chia sẻ, Voucher có hiện ra đúng giá trị không?
- [ ] Thử dùng lại Token cũ để verify (Hệ thống phải báo lỗi 401).
- [ ] Kiểm tra hiển thị trên Mobile (TikTok-style layout) xem có bị che khuất không?

---
> **Lưu ý:** Mọi thông tin về khóa bảo mật được quản lý qua biến môi trường `VIRAL_SECRET_KEY` trên Server. Không chia sẻ khóa này dưới bất kỳ hình thức nào.
