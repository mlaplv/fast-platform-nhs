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
- [x] Đồng bộ hóa `walkthrough.md` và đóng gói commit. <!-- id: 215 -->
- [x] Refactor MediaService & Global Zero-Hydration Sweep (Rule 1.5). <!-- id: 216 -->

### GIAI ĐOẠN 5: KIỂM TOÁN TỔNG THỂ & DỌN RÁC (AUDIT PHASE)
- [x] Vẽ bản đồ kiến trúc hoàn công Elite V2.2. <!-- id: 217 -->
- [x] Trinh sát và lập danh sách file "mìn" (Orphan Files). <!-- id: 218 -->
- [x] Chờ duyệt và thực hiện lệnh "Thanh tẩy" (Purge). <!-- id: 219 -->
- [x] Di chuyển nốt các Schema từ `models/` nội bộ sang `schemas/`. <!-- id: 220 -->
- [x] Xóa bỏ hoàn toàn trạm Schema nội bộ tại Creative Studio. <!-- id: 221 -->

## ✅ TRẠNG THÁI: HOÀN TẤT TINH KHIẾT (ELITE V2.2)
- [x] Toàn bộ Backend đã chuyển sang mô hình Service-Centric.
- [x] Đã xóa bỏ Repository Layer (Rule KISS/YAGNI).
- [x] Đạt 100% Type Safety.
- [x] Zero-Hydration cho các luồng dữ liệu cao tần (R1.5).
- [x] Đã gỡ bỏ toàn bộ ORM Model imports khỏi Service layer.
- [x] Creative Studio & AI Engine đã được nắn dòng Zero-Hydration.
