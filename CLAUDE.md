# HIẾN PHÁP FAST-PLATFORM ÁP DỤNG CHO MỌI VERSION

> **CHỈ THỊ CHO AI IDE:** Dự án Agentic AI 2026. Stack cố định: **SvelteKit 5 (Runes) + Litestar (Python 3.14-slim) + SQLAlchemy 2.0 (AdvancedAlchemy) + PydanticAI + LiteLLM**. Tuyệt đối KHÔNG dùng React/Next.js/FastAPI/Prisma. Mọi file tạo ra phải tuân thủ nghiêm ngặt các nguyên lý "THIẾT QUÂN LUẬT" (Hardened Architecture) và ép kiểu tĩnh 100% (CẤM dùng 'any' dưới mọi hình thức). Chỉ cho phép chạy trên 3 domain: smartshop.test, api.smartshop.test, admin.smartshop.test, cấm tuyệt đối dùng localhost, 127.0.0.1

---

## R00 – ĐẠO LUẬT TRÌNH BÁO (PROPOSE-FIRST PROTOCOL)

- ❌ CẤM TUYỆT ĐỐI AI tự ý xuất code, tạo file, hoặc sửa logic khi chưa được Sếp phê duyệt phương án.
- ✅ BẮT BUỘC tuân thủ quy trình 3 bước cho MỌI yêu cầu:
  1. **PROPOSE:** Trình bày phương án giải quyết (file nào sẽ bị sửa, logic thay đổi ra sao).
  2. **CRITIQUE:** Tự phản biện rủi ro (Cách này có ngốn thêm RAM VPS 2GB không? Có phá vỡ kiến trúc Lean/Zero-Hydration không?).
  3. **HALT:** Dừng lại và hỏi: "Sếp có duyệt phương án và chấp nhận rủi ro này không?". CHỈ KHI Sếp gõ "Duyệt" hoặc "Ok", mới được phép in code ra màn hình.
  4. **Đảm bả**o các gói cài đặt luôn mới nhất(latest), cấm đưa về bản củ.

## R01 – ĐẠO LUẬT TRINH SÁT (SCOUT & REPORT PROTOCOL)

AI IDE là một người cộng sự, không phải cái máy gõ phím mù quáng. Trong quá trình quét Context và phân tích mã nguồn để thực hiện yêu cầu của Sếp:

- ❌ **CẤM ÂM THẦM SỬA LỖI:** Nếu phát hiện bugs, code thối (code smell), hoặc điểm nghẽn hiệu năng nằm ngoài phạm vi yêu cầu hiện tại, TUYỆT ĐỐI KHÔNG được tự ý sửa để tránh side-effects.
- ❌ **CẤM IM LẶNG:** Không được lờ đi các vấn đề nghiêm trọng đập vào mắt bạn trong lúc đọc file.
- ✅ **BẮT BUỘC BÁO CÁO (THE SCOUT REPORT):** Ở cuối mỗi luồng phân tích (trước bước HALT chờ duyệt), bạn BẮT BUỘC phải mở một mục có tên `[💡 PHÁT HIỆN DỊ THƯỜNG / TỐI ƯU]`.
- ✅ **Cấu trúc Báo cáo Ngắn gọn:** Liệt kê theo format: `[Tên File] -> [Dòng/Hàm] -> [Phát hiện vấn đề: Bug/Performance/Security] -> [Hậu quả nếu để nguyên]`.

## I. ĐIỀU KIỆN NỀN & MÔI TRƯỜNG

**Deployment: VPS 2 vCPU, 2GB RAM, có Swap.** Mọi quyết định kiến trúc phải soi chiếu qua giới hạn phần cứng này.
**Coding Standards:** Ép kiểu tĩnh 100%. Mọi biến, tham số, và giá trị trả về phải có kiểu tường minh. CẤM dùng `any`.

## II. KIẾN TRÚC & CẤU TRÚC THƯ MỤC (V76.3)

### 1. Backend (Litestar + PydanticAI)
- `/backend/services/` -> **C.O.R.E (Central Orchestrated Routing Engine)**
  - `routing/` -> Bộ định tuyến 3 tầng: Heuristic (T1) -> Semantic (T1.5) -> LLM Dispatcher (T2)
  - `xohi/creative_studio/` -> Content Factory (Viral Hook Loop Engine)
  - `ai_engine/core/` -> Trinity Bridge (LiteLLM) & Vector Memory (RAG)
- `/backend/database/` -> SQLAlchemy 2.0 Repositories & Models (AdvancedAlchemy)
- `/backend/routers/` -> API Endpoints (SSE, Voice Stream, REST)
- `/backend/controllers/` -> Logic xử lý Business (Chat, Article, Settings)

### 2. Frontend (SvelteKit 5 Runes)
- `/frontend/src/lib/` -> Common Logic & Shared State
  - `state/` -> Nanobot Store (Svelte Runes implementation)
  - `vui/` -> Voice User Interface components
  - `components/` -> UI Atomic Components
- `/frontend/src/routes/` -> Page Routing & API Fetching

### 3. Core Protocols
- **State Management:** Tuyệt đối dùng Svelte 5 Runes (`$state`, `$derived`, `$effect`).
- **Communication:** Ưu tiên SSE (Server-Sent Events) cho phản hồi từ AI.
- **Memory Aggregation:** Dùng Redis Pipeline để fetch context trong 1 RTT (Rule R82.25).

