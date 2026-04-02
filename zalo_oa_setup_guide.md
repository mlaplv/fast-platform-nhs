# Hướng dẫn thiết lập Zalo OA Support Bridge (Elite V2.2)

Dành cho Sếp: Sau khi đã cấu hình `OAUTH_ZALO_CLIENT_ID` và `OAUTH_ZALO_CLIENT_SECRET` cơ bản, Sếp cần thực hiện 2 bước sau để kích hoạt cầu nối.

---

## 1. Lấy ZALO_OA_REFRESH_TOKEN (Dùng vĩnh viễn)

Zalo OA sử dụng cơ chế Token xoay vòng. Để lấy mã khởi tạo một cách nhanh nhất mà không cần viết code:

1.  **Truy cập Tool Debug**: Vào [Zalo API Explorer](https://developers.zalo.me/tools/explorer).
2.  **Chọn App**: Chọn đúng App SmartShop đã tạo.
3.  **Chọn OA**: Trong mục "Loại Token", chọn **Official Account Tablet**.
4.  **Cấp quyền**:
    *   Tích chọn các quyền: `oa.message.transaction`, `oa.message.content`.
    *   Nhấn **Cho phép**.
5.  **Copy Refresh Token**: 
    *   Sau khi cấp quyền, Tool sẽ hiển thị `Access Token` and `Refresh Token`.
    *   Hãy copy giá trị **Refresh Token** và dán vào file [.env](file:///home/lv/Desktop/fast-platform-core/.env).
    *   *Lưu ý*: Hệ thống sẽ tự động dùng mã này để lấy Access Token mới mỗi khi hết hạn (cơ chế tự động hóa trong [ZaloService](file:///home/lv/Desktop/fast-platform-core/backend/services/core/zalo_service.py#9-163)).

---

## 2. Lấy ZALO_ADMIN_ID (UID của người nhận tin)

Mỗi tài khoản Zalo khi quan tâm một OA sẽ có một **User ID (UID)** riêng biệt cho OA đó. Sếp cần UID này để hệ thống biết phải gửi thông báo về máy nào.

**Cách lấy UID nhanh nhất:**

1.  **Gửi tin nhắn**: Sếp lấy điện thoại, mở App Zalo và gửi bất kỳ tin nhắn nào vào OA SmartShop của mình.
2.  **Truy cập OA Manager**: Vào [Quản lý Zalo OA](https://oa.zalo.me/manage/oa).
3.  **Vào mục Chat**:
    *   Tìm đúng cuộc hội thoại Sếp vừa nhắn.
    *   Nhìn lên thanh địa chỉ (URL) của trình duyệt. 
    *   UID sẽ là chuỗi số cuối cùng sau dấu `/`. 
    *   *Ví dụ URL: `https://oa.zalo.me/manage/chat?uid=1234567890123...` -> ID là `1234567890123...`*
4.  **Cấu hình**: Dán ID này vào `ZALO_ADMIN_ID` trong file [.env](file:///home/lv/Desktop/fast-platform-core/.env).

---

## 3. Kiểm tra kết nối

1.  Trong Admin Panel, hãy đặt trạng thái Helen AI là **TẮT**.
2.  Mở trang chủ, chat một câu bất kỳ (ví dụ: "Tôi cần tư vấn gấp").
3.  Kiểm tra điện thoại: Sếp sẽ nhận được thông báo từ Zalo OA kèm nội dung chat và thông tin định danh khách hàng.

> [!IMPORTANT]
> Zalo OA Token có thời hạn. Cơ chế [ZaloService](file:///home/lv/Desktop/fast-platform-core/backend/services/core/zalo_service.py#9-163) đã được em thiết kế để tự động làm mới (Refresh). Sếp chỉ cần nạp lần đầu, trừ khi Sếp reset App Secret thì mới cần lấy lại Refresh Token mới.

*Hoàn thành bởi Antigravity (Elite V2.2 Protocol).*
