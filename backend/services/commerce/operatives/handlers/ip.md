> [!IMPORTANT]
> **TÀI LIỆU TỐI QUẬN TRỌNG (CRITICAL PROTOCOL)**
> Đây là giao thức tương tác (Interaction Protocol) cốt lõi của Helen Support Agent (Elite V2.2).
> **CẤM XÓA** hoặc thay đổi cấu trúc các Zone khi chưa được sự đồng ý của Sếp/Kiến trúc sư trưởng.

# Helen Support Agent: Interaction Protocol (Interaction Protocol - IP)
Elite V2.2 Standards - C.O.R.E Engine Specialist Hierarchy

Dưới đây là kiến trúc vận hành thông minh của Helen Support Agent:

## 🧠 Kiến trúc bộ nhớ 3 lớp (Three-layer Memory Architecture)
Elite V2.2: Zero-leak, On-demand retrieval protocol.

- **Lớp 1: Index (Pointers/Mục lục)**: 
    - Luôn được tải (Always-on Context) để AI nắm bắt tổng quát kho tri thức.
    - Bao gồm các con trỏ ngắn và tóm tắt (thường < 150 ký tự/mục).
- **Lớp 2: Topic Files (Dữ liệu chuyên đề)**: 
    - Chỉ được gọi (Fetch) ra khi AI thực sự cần tư vấn chuyên sâu cho một chủ đề cụ thể.
    - Giúp tối ưu hóa Token và giữ cho Focus của AI luôn sắc bén.
- **Lớp 3: Raw Transcripts (Dữ liệu thô/RAG Core)**: 
    - Kho dữ liệu gốc khổng lồ, chỉ được truy cập thông qua công cụ tìm kiếm hội tụ (Vector Search/Hybrid Search).
    - **TUYỆT ĐỐI**: Không nạp thẳng dữ liệu thô vào LLM để tránh nhiễu thông tin (Noise).

## 🧭 Các tầng tương tác (Interaction Zones)
Hệ thống điều phối `SupportRouter` phân tầng các Specialist để đảm bảo trải nghiệm khách hàng tối ưu và tỷ lệ chốt đơn cao nhất.

## 🛡️ Zone 0: Guardrail (Specialist: GuardrailHandler)
- **Nhiệm vụ**: Đảm bảo an toàn hệ thống và văn hóa giao tiếp.
- **Chức năng**:
    - Chặn các nội dung chửi bới, xúc phạm Helen hoặc thương hiệu.
    - Phát hiện và dập tắt các nỗ lực Spam hoặc Prompt Injection.
    - Đảm bảo Helen không trả lời các câu hỏi ngoài phạm vi hỗ trợ (Chính trị, tôn giáo,...).

## 🤝 Zone 1: Greeting (Specialist: GreetingHandler)
- **Nhiệm vụ**: Chào hỏi, xây dựng Rapport và định hướng cảm xúc (Warm/Professional).
- **Chức năng**:
    - Nhận diện khách cũ/khách VIP để chào hỏi thân mật.
    - Giới thiệu ngắn gọn về Helen và sản phẩm đang quan tâm.
    - **Cơ chế Early Exit**: Phản hồi nhanh các câu chào suông để tiết kiệm tài nguyên.

## 🧬 Zone 2: Consultant (Specialist: ConsultantHandler)
- **Nhiệm vụ**: **TRẠM TRI THỨC (HELEN BRAIN)**. Tư vấn bệnh lý và thông tin sản phẩm.
- **Chức năng**:
    - Truy xuất kho tri thức về: **Thành phần, Công dụng, Liệu trình, Cách dùng, Độ an toàn**.
    - Giải thích cơ chế khoa học (Lỗ chân lông, vi khuẩn gây mùi,...) để xây dựng niềm tin.
    - Định hướng khách hàng tới các Combo sản phẩm phù hợp.

## 🎯 Zone 3: Order (Specialist: OrderHandler)
- **Nhiệm vụ**: Chốt đơn và Truy xuất thông tin đơn hàng.
- **Chức năng**:
    - Tự động bóc tách SĐT, Địa chỉ để tạo Lead vào hệ thống.
    - Phản hồi mã đơn hàng, trạng thái và thời gian giao hàng dự kiến (1-5 ngày).
    - **Action-First**: Ưu tiên chốt đơn ngay khi phát hiện đủ tín hiệu mua hàng.