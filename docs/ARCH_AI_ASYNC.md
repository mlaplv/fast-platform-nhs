# Elite V2.2: Agentic AI Asynchronous Architecture

Tài liệu này thuyết minh về kiến trúc thực thi AI bất đồng bộ (Asynchronous Execution) được triển khai cho Helen AI và hệ thống Agentic Core (XoHi), tuân thủ tiêu chuẩn CTO quốc tế.

---

## 1. Tổng quan Kiến trúc (High-Level Design)

Hệ thống chuyển dịch từ mô hình "Request-Response Blocking" sang mô hình **"Dual-Tier Event-Driven"**:

### Tầng 1: Triage Butler (Synchronous - <100ms)
- **Nhiệm vụ**: Phân loại ý định (Intent), xử lý câu chào, FAQ tĩnh hoặc từ chối spam.
- **Phản hồi**: `200 OK` nếu xử lý được ngay.
- **Mục tiêu**: Tuyệt đối không gọi LLM cho các tác vụ đơn giản để tiết kiệm token và giảm Latency.

### Tầng 2: Neural Brain (Asynchronous - Background Task)
- **Nhiệm vụ**: Xử lý logic nặng (RAG, Phân tích chuyên sâu, Generative AI).
- **Phản hồi**: `202 Accepted` kèm `task_id` ngay lập tức để giải phóng Main Thread của Litestar.
- **Công cụ**: `arq` (Redis-based Queue) + `TrinityBridge`.

---

## 2. Di sản Kế thừa & "Cửa hậu" (The Heritage Backdoor)

Kiến trúc được cấy trực tiếp vào lớp cha cao nhất để đảm bảo tính sẵn sàng cho toàn hệ thống mà không cần sửa code cũ của XoHi.

### Cấu trúc Registry (`agent_base.py`)
Mọi Agent kế thừa từ `BaseAgentOperative` đều tự động đăng ký vào một Registry toàn cục thông qua `__init_subclass__`:

```python
# AGENT_REGISTRY: Maps agent_id_class -> Class Definition
AGENT_REGISTRY = {
    "support_agent": <class SupportAgentOperative>,
    "plagiarism_cop": <class PlagiarismCop>,
    "content_enricher": <class ContentEnricher>,
}
```

### Cách thức hoạt động của "Cửa hậu":
1.  **Tự động nhận diện**: Ngay khi một class được định nghĩa với `agent_id_class`, nó được nạp vào Registry.
2.  **Phương thức `enqueue_chat`**: Đây là phương thức "cửa hậu" nằm ở lớp Base. Bất kỳ Agent nào cũng có thể gọi `self.enqueue_chat(payload)` để đẩy việc xuống Worker.
3.  **Dynamic Instantiation**: Background Worker chỉ cần nhận `agent_id` từ Redis, tra cứu Registry và khởi tạo Agent đó để chạy logic `chat`.

---

## 3. Quy trình kết nối (Connection Flow)

### Client Flow (Helen AI)
1.  **Frontend (Svelte 5)**: `SupportWidget` gọi `ChatProvider.sendMessage()`.
2.  **API (Litestar)**: `SupportController` nhận request, gọi `SupportAgent.chat()`.
3.  **Triage**: `SupportAgent` quyết định đây là câu hỏi khó -> gọi `self.enqueue_chat()`.
4.  **Enqueue**: `arq` lưu Job vào Redis, API trả về `202 Accepted`.
5.  **SSE Sync**: Frontend nhận `task_id` và hiển thị "Helen đang xử lý...". Kết quả thật sẽ được đẩy qua `Pulse SSE` khi Worker xong việc.

### Admin Flow (XoHi Backdoor Integration)
Đối với các Agent của XoHi (như PlagiarismCop), cách móc nối cực kỳ đơn giản:
1.  **Cánh cửa đã mở**: Class `PlagiarismCop` đã có `agent_id_class`. Nó đã nằm trong Registry.
2.  **Móc nối**: Ở `PlagiarismController`, thay vì `await plagiarism_cop.chat(...)`, sếp chỉ cần đổi thành `await plagiarism_cop.enqueue_chat(...)`.
3.  **Thực thi**: Hệ thống sẽ tự động điều hướng việc phân tích đạo văn xuống `arq_worker.py` mà không làm treo UI của Admin.

---

## 4. Quản lý tài nguyên (Resource & Session Lifecycle)

Để bảo đảm VPS 2GB RAM không bị crash:
-   **Isolation**: Worker tạo `AsyncSession` mới cho mỗi task, `commit()` và `close()` ngay lập tức sau khi xong.
-   **Concurrency**: Giới hạn `max_jobs=10` tại `WorkerSettings` để tránh bùng nổ tiến trình khi AI xử lý chậm.
-   **Lifecycle Monitoring**: Toàn bộ quá trình được log rõ ràng qua `./xohi.sh logs`.

---

## 5. Cấu trúc File minh bạch

-   `backend/services/ai_engine/core/agent_base.py`: Trái tim kế thừa & Registry Backdoor.
-   `backend/infra/arq_config.py`: Cấu hình kết nối Redis/Queue.
-   `backend/arq_worker.py`: Hệ điều hành thực thi các Task AI ngầm.
-   `backend/services/commerce/operatives/support_agent.py`: Implement mẫu cho luồng Sync/Async 2 tầng.
-   `frontend/src/lib/state/chat_provider.svelte.ts`: Quản lý state cô lập và lắng nghe tín hiệu thực thi xong.

---
**Đây là kiến trúc chuẩn Elite V2.2, đảm bảo Helen AI chạy mượt mà như Shopee và XoHi sẵn sàng lên Async bất cứ lúc nào sếp muốn.**

[ARCH_AI_ASYNC.md](file:///home/lv/Desktop/fast-platform-core/docs/ARCH_AI_ASYNC.md)


