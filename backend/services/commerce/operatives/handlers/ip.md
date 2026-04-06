# HELEN INTERACTION PROTOCOL (ELITE V2.2)

> **CHỈ THỊ GỐC RỄ:** Helen là Hệ thống Đại lý Agentic AI cho SmartShop 2026. Mọi tương tác phải tuân thủ cấu trúc 4 tầng trí nhớ để tối ưu Latency và Quota Gemini.

---

## 🏗️ 4-LAYER MEMORY ARCHITECTURE

Hệ thống điều phối dữ liệu dựa trên độ phức tạp của câu hỏi để quyết định lúc nào dùng AI, lúc nào không.

### 🔹 Layer 0: Neural Reflex (Ngắt mạch sớm)
- **Cơ chế:** Database Semantic/Exact Match (Hỗ trợ bởi `pgvector`).
- **Lúc nào dùng:** Các câu hỏi FAQ tĩnh (Địa chỉ, Hotline, Giá, Giờ làm việc, Chính sách).
- **Hành động:** Trả lời NGAY từ Database. Quota AI = 0. Latency < 100ms.
- **Tiêu chuẩn:** `match_score > 0.92`.

### 🔹 Layer 1: Topic Indexing (Định hướng)
- **Cơ chế:** Nạp danh sách ID/Câu hỏi (`knowledge_index`) vào Context AI.
- **Lúc nào dùng:** Khách hỏi chung chung hoặc hỏi nhiều vấn đề cùng lúc.
- **Hành động:** AI đóng vai trò "Lễ tân", chỉ dẫn khách hàng vào các chủ đề chi tiết.

### 🔹 Layer 2: Deep Brain (Tổng hợp & Tư vấn)
- **Cơ chế:** Trinity Bridge (Gemini 1.5 Stable).
- **Lúc nào dùng:** Tư vấn bệnh lý (ôi nách/chân), so sánh sản phẩm, giải quyết khiếu nại phức tạp.
- **Hành động:** AI thực hiện RAG (Retrieval-Augmented Generation) để tổng hợp câu trả lời chuyên nghiệp.

### 🔹 Layer 3: Conversion Specialist (Chốt đơn)
- **Cơ chế:** Order Handler (Lead Extraction).
- **Lúc nào dùng:** Khi phát hiện SĐT, Địa chỉ hoặc ý định mua hàng rõ rệt.
- **Hành động:** Trích xuất Lead, đẩy vào CRM và xác nhận đơn hàng với phong thái Elite.

---

## 🎖️ SPECIALIST ZONES (Tactical Roles)

Hệ thống Specialist Pipeline được chia thành các vùng nhiệm vụ đặc thù để tối ưu hóa logic xử lý:

### 🛡️ Zone 0: Guardrail (Vòng bảo vệ)
- **Nhiệm vụ:** Chặn Prompt Injection, lọc ngôn từ thô tục, từ chối các vấn đề ngoài phạm vi (Politics, Competitors).
- **Handler:** `GuardrailHandler`.
- **Đặc điểm:** Tốc độ phản ứng cực nhanh (Heuristics).

### 🌸 Zone 1: Greeting (Lễ tân)
- **Nhiệm vụ:** Chào hỏi, xây dựng Persona "Helen" thân thiện, sử dụng Social Proof (Active visitors) để tạo thiện cảm ban đầu.
- **Handler:** `GreetingHandler`.

### 🧬 Zone 2: Consultant (Chuyên gia)
- **Nhiệm vụ:** Tư vấn chuyên sâu về bệnh lý (hôi nách/chân), giải thích cơ chế sản phẩm dựa trên Knowledge Base.
- **Handler:** `ConsultantHandler`.
- **Công cụ:** Layer 0-2 Memory.

### 💰 Zone 3: Order (Sát thủ chốt đơn)
- **Nhiệm vụ:** Phát hiện ý định mua hàng, trích xuất SĐT/Địa chỉ (Lead), tự động tạo đơn hàng nháp hoặc chốt đơn chính thức.
- **Handler:** `OrderHandler`.
- **Công cụ:** `LeadExtractor`.

### ⚙️ Zone 4: Management (Quản lý)
- **Nhiệm vụ:** Xử lý các yêu cầu hệ thống, dọn dẹp dữ liệu hoặc các tác vụ background khác.
- **Handler:** `ManagementHandler`.

---

## 🚫 NGUYÊN TẮC THIẾT QUÂN LUẬT (Coding Standards)

1. **CẤM Hardcode Model:** Luôn lấy từ `voice_profiles` trong DB.
2. **Key Rotation:** Bắt buộc dùng `TrinityBridge` để xoay vòng 8 key, không được dùng Key đơn lẻ.
3. **Data Extraction:** Tuyệt đối không dùng `hasattr` vá víu. Dùng middleware `TrinityBridge.run` để nhận Schema sạch 100%.
4. **RAM Guard:** Duy trì giới hạn 2GB RAM cho VPS bằng cách dùng Lazy Import cho các thư viện AI nặng.

---

## 🏆 KẾT QUẢ MONG ĐỢI
- **Tốc độ:** Câu hỏi đơn giản phản hồi tức thì.
- **Bền bỉ:** Không bao giờ gục ngã vì lỗi 429 Quota.
- **Chuyên nghiệp:** Phong thái Admin-style, lì lợm và chuẩn xác.