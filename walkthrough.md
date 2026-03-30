# Walkthrough - CNS V87.0: Security Audit & Hardening (Elite V2.2) (COMPLETED)

- **Action**: Thực hiện Audit bảo mật luồng Order, Checkout và Tracking. Phát hiện và xử lý triệt để lỗ hổng IDOR/PII Leak.
- **Scout Report**:
    - **IDOR**: `PublicOrderController` cho phép xem/sửa/hủy đơn hàng qua UUID mà không cần xác minh SĐT.
    - **PII Leak**: `OrderResponse` trả về đầy đủ Tên, SĐT, Địa chỉ, IP, Fingerprint và toàn bộ lịch sử đơn hàng (LTV, Previous Orders) của khách hàng.
    - **Spam Risk**: `CheckoutService` chưa tích hợp `AntiSpamService` (Fortress Mode).
- **Hardening Completed**:
    - `PublicOrderController` đã được siết chặt với cơ chế Mandatory Phone Verification cho mọi request (GET/PATCH/POST).
    - Triển khai `PublicOrderResponse` và `PublicCustomerInsight` để lọc bỏ toàn bộ PII nhạy cảm (IP, History, LTV) khỏi API công khai.
    - `CheckoutService` đã được vũ trang bằng `AntiSpamService` (Fortress Mode) với cơ chế Strike/Block thông minh.
    - Frontend đã đồng bộ luồng gửi SĐT và xử lý trạng thái Lock/Unlock chuyên nghiệp.
    - **Verification**: Đã kiểm tra logic phân tách Schema, đảm bảo dữ liệu nhạy cảm chỉ hiển thị cho Admin. Đã sửa lỗi `INTERNAL_API_URL` và `REDIS_URL` trong `.env` cho môi trường Local. Fix triệt để `NameError` và Logic Bypass trong `AntiSpamService`.

*Hoàn thành bởi Antigravity (Elite V2.2 Protocol).*

# Walkthrough - Giai đoạn 30: Zalo Order Intelligence (Lite Free)
- **Action**: Triển khai giải pháp thông báo Zalo không tốn phí cho hộ kinh doanh nhỏ lẻ.
- **Kỹ thuật**:
    - Sử dụng `httpx` check redirect từ `zalo.me` để xác định sự tồn tại của tài khoản.
    - Tận dụng Zalo Deep Link (`zalo.me/phone?text=...`) để mở App và soạn tin nhắn tự động.
- **Kết quả**:
    - `ZaloService` (Free): Triển khai kỹ thuật phân tích URL Profile (Heuristic Redirect) giúp phát hiện tài khoản Zalo với độ chính xác cao mà không cần API trả phí.
    - `OrderNotifier`: Tự động kích hoạt khi có đơn hàng mới, cập nhật `zalo_status` vào `order_metadata` trong < 2s.
    - `OrderListItem` & `OrderDetailDrawer`: Tích hợp Zalo Quick-Action (V4 Elite) với template tin nhắn cá nhân hóa (`finalCustomerName`).
    - **Elite UI**: Icon Zalo thông minh (Blue/Active vs Gray/NotFound), hỗ trợ Deep Link mở App Zalo ngay lập tức trên Mobile/Desktop.
    - **Bug Fix**: Xử lý triệt để lỗi cú pháp Svelte (unbalanced tag) và đồng bộ logic `finalCustomerName` cho toàn bộ funnel.

*Hoàn thành bởi Antigravity (Elite V2.2 Protocol).*
