# Kế hoạch sửa lỗi mất Highlight ngay sau khi check Copyright

- [x] Phân tích hiện tượng: Highlight hiện lên rồi biến mất ngay. Lưu lại và reload thì lại hiện.
- [x] Xác định nguyên nhân: Tính năng đồng bộ `content` của editor (cụ thể là hàm `applyContentToEditor` khi kết thúc `isBulkFixing` state) gọi lệnh `setContent` của Tiptap. Lệnh này tái tạo (recreate) lại toàn bộ nodes của DOM và xóa sạch các thẻ Highlight (Annotations). Trong khi đó, do mảng annotations không thay đổi (cùng tham chiếu/giá trị so với trước khi setContent) nên biến guard `_lastAnnotationKey` đã block không cho hàm `$effect` render lại highlight.
- [x] Sửa lỗi: Thêm đoạn code chủ động re-dispatch `SET_ANNOTATIONS` ngay bên trong hàm `applyContentToEditor` sau khi gọi `setContent(newHtml)` để buộc Tiptap vẽ lại highlight trên Document mới mà không bị dính guard.
