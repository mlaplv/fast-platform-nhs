# Báo cáo sửa lỗi Highlight "thoắt ẩn thoắt hiện" trong Tiptap

## 1. Triệu chứng
Sếp phát hiện khi check xong Copyright, các đoạn văn vi phạm có highlight vàng/đỏ nhưng lại biến mất NGAY LẬP TỨC. Tuy nhiên, nếu lưu lại rồi F5 trang thì các highlight này lại hiển thị bình thường.

## 2. Truy vết nguyên nhân
1. Sau khi phân tích xong (Loading = false), trạng thái `isBulkFixing` chuyển từ `true` sang `false`.
2. Hàm `$effect` trong `TiptapEditor.svelte` bắt được sự thay đổi này và gọi hàm `applyContentToEditor()` để ép Tiptap đồng bộ phiên bản nội dung mới nhất.
3. Hàm `applyContentToEditor` gọi `editor.commands.setContent()`. Lệnh này của Tiptap có đặc tính **phá hủy hoàn toàn Document cũ và tạo Document mới**. Việc này vô tình quét sạch toàn bộ các "Highlight" (Decorations) đang được vẽ trên màn hình.
4. Mặc dù Svelte có hàm theo dõi biến `annotations` để vẽ lại highlight, nhưng vì mảng `annotations` lúc này **không thay đổi** (vẫn là mảng đó), nên biến lock `_lastAnnotationKey` đã chặn đứng lệnh vẽ lại (để tối ưu hiệu năng).
5. Khi sếp F5 lại trang, mảng `annotations` được nạp từ đầu nên bypass được vòng khóa, do đó highlight lại xuất hiện.

## 3. Phẫu thuật dứt điểm (The Fix)
Em đã chèn thêm đoạn logic chủ động nạp lại (re-apply) các Annotations hiện có **ngay sau** lệnh `setContent` bên trong hàm `applyContentToEditor` (file `TiptapEditor.svelte`). 
Nhờ vậy, ngay khi Tiptap tạo xong Document mới, các thẻ highlight sẽ lập tức được vẽ lại vào đúng vị trí mà không bị Svelte chặn, loại bỏ hoàn toàn hiện tượng chớp tắt.
