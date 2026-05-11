# Kế hoạch sửa lỗi cắt chữ (Truncation) ở phần SURGICAL PLAN (Bản quyền)

- [x] Phân tích log và báo cáo UI bị đứt ngang chữ "Cuộc chiến chống lại".
- [x] Xác định nguyên nhân: Không phải do timeout, không phải max_tokens, mà do **Gemini Safety Filter** bị kích hoạt bởi cụm từ nhạy cảm ("Cuộc chiến chống lại", "vũ khí", "phẫu thuật") -> Model dừng tạo text đột ngột và PydanticAI tự đóng JSON.
- [x] Áp dụng `safety_none=True` vào `trinity_bridge.run` trong `plagiarism_cop.py` để vô hiệu hóa Safety Filter.
- [x] Áp dụng phòng ngừa tương tự cho `ai_inspector.py` và `neural_rewriter.py` (vì cũng là các agent phẫu thuật/sáng tạo dễ dùng từ ngữ "mạnh").
