Sơ đồ Quan hệ & Nhiệm vụ của các File:
File	Vai trò (Metaphor)	Nhiệm vụ chính
key_loader.py	Người Thủ kho	Chỉ lo việc lấy Key từ Biến môi trường (ENV) hoặc Giải mã từ Database (VoiceProfile).
key_metrics.py	Trinh sát Log	Chuyên theo dõi sức khỏe của Key (Fail-count), đo đếm Token và đánh dấu Model bị cạn Quota vào Redis.
key_rotator.py	Tổng Chỉ huy	File này kế thừa 2 Mixin trên (KeyLoader & KeyMetrics) để vận hành việc xoay vòng Key thông minh, lựa chọn Key khỏe nhất cho Sếp.
trinity_models.py	Bản đồ Chiến lược	Quản lý danh sách Model từ Google, phân tầng Model (Pro, Flash, Lite) và xây dựng chuỗi fallback (Waterfall).
trinity_bridge.py	Cầu nối Thần kinh	Lớp cao nhất. Nó gọi KeyRotator để lấy Key và gọi TrinityModels để biết cần dùng model nào, sau đó mới thực thi AI.
🛠️ Tại sao lại cần tách nhỏ như vậy?
Dễ bảo trì (Martial Law): Nếu logic nạp Key bị lỗi, con chỉ cần sửa key_loader.py mà không làm hỏng logic xoay vòng Key.
Tránh xung đột (Race Conditions): Việc tách key_metrics giúp tách biệt logic ghi dữ liệu vào Redis, tránh việc file key_rotator trở nên quá cồng kềnh và khó kiểm soát khi hệ thống chạy song song nhiều task.
Tái sử dụng: Ví dụ, key_metrics có thể được tái sử dụng cho các loại AI khác (như OpenAI hay Claude) mà không cần viết lại logic đo đếm token.