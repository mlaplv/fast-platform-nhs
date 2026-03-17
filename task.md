# QUY HOẠCH KIẾN TRÚC ELITE V2.2 (CONTROLLER -> SERVICE)

## 🎯 MỤC TIÊU
Nắn toàn bộ Backend về trục kiến trúc tinh gọn: Controller (Giao tiếp) -> Service (Logic & DB). Loại bỏ mọi lớp trung gian (Repository) vi phạm luật KISS/YAGNI.

## 📝 LỘ TRÌNH THỰC THI (CHECK-LIST)

### GIAI ĐOẠN 1: QUY HOẠCH CONTENT ENGINE (ARTICLE/NEWS)
- [x] Khởi tạo `backend/services/content_service.py` chứa logic Article CRUD + Embedding + Slug. <!-- id: 200 -->
- [x] Refactor `ArticleController`: Loại bỏ dependency `ArticleRepository`, gọi thẳng `ContentService`. <!-- id: 201 -->
- [x] Thanh lý `backend/database/repositories/article_repository.py`. <!-- id: 202 -->

### GIAI ĐOẠN 2: CHUẨN HÓA VOICE & STT PIPELINE
- [x] Khởi tạo `backend/services/voice_service.py`: Gộp logic từ `voice_stream.py` và `STTCorrector`. <!-- id: 203 -->
- [x] Refactor `stt_websocket`: Chỉ giữ lại logic nhận/gửi message, xử lý audio đẩy xuống `VoiceService`. <!-- id: 204 -->

### GIAI ĐOẠN 3: NẮN DÒNG USER & ORDER (TRỤC XƯƠNG SỐNG)
- [x] Hoàn thiện `backend/services/user_service.py`: Gộp logic User, Role, Permission. <!-- id: 207 -->
- [x] Refactor `UserController`: Gọi thẳng `UserService`, xóa bỏ dependencies Repository. <!-- id: 208 -->
- [x] Khởi tạo `backend/services/order_service.py`: Chứa logic Order + Anti-Spam Trigger. <!-- id: 209 -->
- [x] Refactor `OrderController`: Chuyển logic State Machine và Event Emit vào `OrderService`. <!-- id: 210 -->

### GIAI ĐOẠN 4: THANH LÝ & ĐÓNG GÓI (FINAL CLEANUP)
- [x] Khởi tạo `backend/services/notification_service.py`. <!-- id: 211 -->
- [x] Refactor `NotificationController` & `AIController`. <!-- id: 212 -->
- [x] **XÓA BỎ VĨNH VIỄN** `backend/database/repositories.py` và các provider liên quan. <!-- id: 213 -->
- [x] Kiểm tra ép kiểu tĩnh 100% (No `Any`) và hiệu năng (RAM < 2GB). <!-- id: 214 -->

## ✅ TRẠNG THÁI: HOÀN TẤT
- Đã hoàn tất chuyển đổi Controller -> Service cho toàn bộ hệ thống.
- Đã xóa bỏ vĩnh viễn lớp Repository và các provider liên quan.
- Đã đạt 100% Type Safety (No Any).
- Tối ưu hiệu năng qua Zero-Hydration.
