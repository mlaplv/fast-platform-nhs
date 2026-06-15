# Kế hoạch gộp Giỏ hàng UI và Bản nháp đơn hàng AI (Single Source of Truth)

## 1. Mô tả mục tiêu
Gộp giỏ hàng giao diện (Frontend Cart) và bản nháp đơn hàng của AI (Redis Order Draft) thành một nguồn dữ liệu duy nhất. Khi khách hàng bấm "Tính tiền" hoặc nhắn "tính tiền", Helen sẽ lấy trực tiếp sản phẩm trong giỏ hàng thực tế để chốt đơn, loại bỏ hoàn toàn sự bất đồng bộ giữa giao diện web và khung chat.

---

## 2. Phân tích giải pháp & Phản biện rủi ro (Risk Analysis & Critique)

### Rủi ro 1: Bất đồng bộ khi khách hàng thay đổi sản phẩm bằng lời nói qua Chat
- **Mô tả**: Nếu khách hàng đang mở giỏ hàng nhưng lại nhắn chat: *"Cho chị thêm 1 serum nhé"*, AI sẽ ghi nhận thêm serum vào đơn hàng nháp. Tuy nhiên, ở lượt chat tiếp theo, do giỏ hàng Frontend truyền lên không thay đổi, sản phẩm serum vừa thêm bằng miệng sẽ bị ghi đè/mất đi.
- **Phương án giải quyết (Bidirectional Sync)**: 
  - Khi AI xử lý thêm/bớt hàng qua chat, Backend sẽ trả về danh sách sản phẩm mới trong thuộc tính `ui_metadata.update_cart`.
  - Frontend Svelte Store sẽ lắng nghe sự kiện này và tự động gọi hàm `getGlobalCart().updateItem(...)` để đồng bộ giỏ hàng thực tế trên giao diện khớp với lời nói của AI.

### Rủi ro 2: Khách hàng đa kênh (Zalo, Facebook Messenger) không có giỏ hàng Frontend
- **Mô tả**: Khách chat từ Zalo OA hoặc Messenger không có trình duyệt/giỏ hàng UI truyền lên (`cart_items` rỗng).
- **Phương án giải quyết (Hybrid Fallback)**:
  - Hệ thống chỉ đồng bộ theo giỏ hàng UI khi `cart_items` được truyền lên (Web Chat).
  - Nếu `cart_items` trống hoặc rỗng (Zalo/Messenger), hệ thống tự động sử dụng luồng trích xuất sản phẩm bằng AI (LLM-based extraction) và lưu trữ nháp trên Redis như cũ.

---

## 3. Các thay đổi đề xuất

### A. Backend Layer (Đồng bộ và xử lý logic chốt đơn)

#### [MODIFY] [lead_extractor.py](file:///media/lv/data/fast-platform-core/backend/services/commerce/logic/lead_extractor.py)
- Trong hàm `extract_and_convert`, kiểm tra tham số `cart_items`.
- Nếu có `cart_items` (Web Chat), bỏ qua bước AI trích xuất sản phẩm từ văn bản chat. Gán trực tiếp danh sách sản phẩm từ `cart_items` vào `lead.items`.
- Nếu `cart_items` rỗng, thực hiện trích xuất sản phẩm qua AI từ tin nhắn như bình thường (Zalo/Messenger fallback).

#### [MODIFY] [order.py](file:///media/lv/data/fast-platform-core/backend/services/commerce/operatives/handlers/order.py)
- Cập nhật luồng xử lý `OrderHandler`: Khi nhận thấy khách nhắn từ khóa thanh toán (`tính tiền`, `thanh toán`) và giỏ hàng client gửi lên có hàng, thực hiện đồng bộ ngay lập tức các sản phẩm này vào Redis `order_draft` để đảm bảo dữ liệu đơn hàng luôn chính xác tuyệt đối theo giỏ hàng hiện tại.

### B. Frontend Layer (Đồng bộ 2 chiều về giao diện)

#### [MODIFY] [supportAgent.svelte.ts](file:///media/lv/data/fast-platform-core/frontend/src/lib/state/commerce/supportAgent.svelte.ts)
- Bổ sung hàm lắng nghe kết quả trả về từ Helen: Nếu phản hồi từ server có chứa chỉ thị cập nhật giỏ hàng (`ui_metadata.update_cart`), tự động gọi store `getGlobalCart()` để cập nhật số lượng và sản phẩm thực tế của giỏ hàng trên giao diện của khách.

---

## 4. Kế hoạch xác minh (Verification Plan)

### Kiểm thử tự động (Automated Tests)
- Bổ sung test case trong `backend/tests/test_helen_support_specialists.py` giả lập trường hợp client gửi request chat kèm `cart_items` và nội dung `"tính tiền"`, kiểm tra xem đơn hàng tạo ra có khớp 100% với danh sách sản phẩm trong giỏ hàng gửi lên hay không.

### Kiểm thử thủ công (Manual Verification)
- Mở Storefront, thêm sản phẩm vào giỏ hàng.
- Chat với Helen: nhắn `"tính tiền"`. Kiểm tra xem Helen có hiển thị đúng thông tin thanh toán của các sản phẩm trong giỏ hàng hay không.
- Thử nhắn *"cho chị thêm 1 sản phẩm X"* trong chat, kiểm tra xem sản phẩm X có tự động được thêm vào giỏ hàng trên giao diện web hay không.
