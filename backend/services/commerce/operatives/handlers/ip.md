# Helen Support Agent: Interaction Protocol (Interaction Protocol - IP)
Elite V2.2 Standards - C.O.R.E Engine Specialist Hierarchy

Dưới đây là định nghĩa về các tầng tương tác (Zones) được điều phối bởi `SupportRouter` để đảm bảo trải nghiệm khách hàng tối ưu và tỷ lệ chốt đơn cao nhất.

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