# SƠ ĐỒ VÀ PHÂN TÍCH KIẾN TRÚC DỰ ÁN (ELITE V2.2)

Tài liệu này cung cấp sơ đồ cây thư mục kiến trúc của dự án Fast-Platform (Elite V2.2) cùng với phân tích chi tiết về điểm mấu chốt, điểm ưu và điểm nhược trong thiết kế hệ thống.

---

## I. SƠ ĐỒ CÂY THƯ MỤC KIẾN TRÚC

```text
fast-platform-core/
├── backend/                                  # 🐍 HỆ THỐNG BACKEND (Litestar + Python 3.14)
│   ├── main.py                               # File chạy chính của ứng dụng Litestar
│   ├── lifespan.py                           # Quản lý vòng đời khởi chạy/đóng kết nối (Startup/Shutdown)
│   │
│   ├── controllers/                          # 🎮 TẦNG ĐIỀU HƯỚNG REQUESTS (Controllers)
│   │   ├── client/                           # Nhóm điều hướng Client/Storefront công khai (CRO)
│   │   │   ├── home.py, product.py           # Hiển thị trang chủ, thông tin sản phẩm
│   │   │   ├── checkout.py, order.py         # Quy trình giỏ hàng, đặt hàng và thanh toán
│   │   │   └── support.py, tts.py            # AI tư vấn (Helen) và chuyển đổi giọng nói (Text-to-Speech)
│   │   ├── admin_*.py                        # Nhóm điều hướng quản trị (admin_ctv, admin_support,...)
│   │   └── auth.py, seo.py, category.py      # Các controller dùng chung cho phân quyền và SEO
│   │
│   ├── services/                             # 🧠 TẦNG BUSINESS LOGIC & AI SERVICES
│   │   ├── ai_engine/                        # Engine xử lý AI Core (PydanticAI V2 + LiteLLM)
│   │   │   ├── core/                         # Trọng tâm điều phối: Trinity Bridge, Brain Manager
│   │   │   └── tools/                        # Công cụ hỗ trợ AI truy vấn (Knowledge base, RAG)
│   │   ├── commerce/                         # Nghiệp vụ Thương mại (Bán hàng, Khuyến mãi, Loyalty)
│   │   │   ├── loyalty.py, price_agent.py    # Xử lý tính điểm thành viên và báo giá
│   │   │   ├── seo_service.py                # Xử lý tối ưu hóa SEO tự động
│   │   │   └── operatives/                   # Chat Agent Operatives (Hệ thống Helen tư vấn)
│   │   │       ├── support_agent.py          # Khởi tạo và quản lý ngữ cảnh hội thoại
│   │   │       └── handlers/                 # Phân luồng xử lý: consultant (tư vấn), order (đặt hàng)...
│   │   ├── ads_protection/                   # Dịch vụ chống click tặc, phân tích Ads Forensic (Xohi)
│   │   ├── xohi/                             # Studio tự động hóa và sinh bài viết chuẩn SGE
│   │   ├── auth_service.py                   # Xử lý xác thực người dùng
│   │   └── event_bus.py                      # Hệ thống Bus sự kiện đồng bộ/bất đồng bộ
│   │
│   ├── database/                             # 💾 TẦNG DỮ LIỆU (SQLAlchemy 2.0 ORM)
│   │   ├── alchemy_config.py                 # Khởi tạo kết nối DB & Session Management
│   │   ├── repositories.py                   # Pattern Repository truy vấn Database an toàn
│   │   └── models/                           # Các thực thể dữ liệu (commerce, content, seo, auth, ads...)
│   │
│   ├── routers/                              # 🌐 TẦNG STREAMING & REAL-TIME
│   │   ├── intent.py, intent_core.py         # Nhận diện ý định giọng nói và điều phối luồng
│   │   └── content_stream.py, voice_stream.py# Stream kết quả âm thanh và văn bản real-time
│   │
│   ├── schemas/                              # 🛡️ Pydantic V2 Schemas để Validation/Serialization
│   ├── infra/                                # ⚙️ Cấu hình hạ tầng (arq_config cho Background Worker)
│   └── constants/                            # 📌 Quản lý các biến hằng số (commerce, permissions, voice...)
│
├── frontend/                                 # ⚡ HỆ THỐNG FRONTEND (SvelteKit 5 + TypeScript + Runes)
│   ├── svelte.config.js, vite.config.js      # File cấu hình build và môi trường SvelteKit/Vite
│   ├── src/
│   │   ├── app.html                          # HTML template gốc
│   │   ├── hooks.server.ts                   # Hooks xử lý Auth Session và Security Headers ở Server
│   │   │
│   │   ├── routes/                           # 🚦 ĐỊNH TUYẾN TRANG (SvelteKit Directory Routing)
│   │   │   ├── (client)/                     # 🛒 Nhóm giao diện Storefront cho Khách hàng công khai
│   │   │   │   └── (store)/                  # Chi tiết giỏ hàng, khuyến mại, search, và [slug] (sản phẩm)
│   │   │   ├── (admin)/                      # 🔑 Nhóm quản trị hệ thống
│   │   │   │   └── dashboard/                # Trang tổng quan điều phối kinh doanh & kỹ thuật
│   │   │   └── auth/                         # Giao diện đăng nhập, đăng ký
│   │   │
│   │   └── lib/                              # 📦 THƯ VIỆN GIAO DIỆN & TRẠNG THÁI CHUNG
│   │       ├── components/                   # UI Components phân tách theo phân hệ
│   │       │   ├── storefront/               # Components bán hàng (Cart, Product Card...)
│   │       │   ├── admin/                    # Components quản trị (User table, Bento cards...)
│   │       │   └── widgets/                  # Tiện ích tương tác giọng nói, Ads Protection widget...
│   │       ├── state/                        # Quản lý Client State sử dụng Svelte 5 Runes ($state, $derived)
│   │       ├── constants/                    # Hằng số toàn cục (zIndex.ts, route paths...)
│   │       ├── api/                          # SDK giao tiếp với Backend Litestar
│   │       └── styles/                       # CSS Vanilla
│
├── scripts/                                  # 🛠️ CÁC TOOL SCRIPTS (Sync, setup SSL, database seed)
├── docker-compose.yml                        # 🐳 Điều phối môi trường Container (Backend, Frontend, Redis, DB)
└── CLAUDE.md                                 # 📜 Hiến pháp & Quy tắc lập trình tối cao của dự án
```

---

## II. ĐIỂM MẤU CHỐT TRONG KIẾN TRÚC (KEY ARCHITECTURAL POINTS)

1. **Kiến trúc hướng Agent (Agent-Centric Architecture):**
   - Không chỉ là một ứng dụng CRUD thông thường, hệ thống tích hợp sâu các tác nhân AI thông minh (Helen Agent, Ads Forensic Agent, Viral Share Agent) làm lõi cốt lõi để xử lý nghiệp vụ tự động hóa từ phân tích click ảo đến đặt hàng và tư vấn khách hàng.
   - Giao tiếp giữa các Agent thông qua cầu nối trung gian `TrinityBridge` và hệ thống định tuyến ngữ nghĩa `SemanticRouter`.

2. **Ứng dụng Svelte 5 Runes:**
   - Việc chuyển dịch sang Svelte 5 (sử dụng `$state`, `$derived`, `$effect`, `$props`) giúp quản lý trạng thái động của các Widget điều hướng giọng nói và giỏ hàng cực kỳ hiệu quả mà không bị overhead (bloat) như các cơ chế Virtual DOM khác.
   - Phân cấp rõ ràng giữa hai Route Group chính là `(client)` và `(admin)`, trong đó client tối ưu tối đa về thời gian tải trang (CRO) và không yêu cầu đăng nhập bắt buộc.

3. **Luồng dữ liệu chặt chẽ (Strict Data Flow Protocol):**
   - Client hoàn toàn không được truy vấn trực tiếp cơ sở dữ liệu. Mọi tương tác bắt buộc phải đi qua API Endpoint (Litestar Controllers) -> Services (Business Logic) -> Repositories (Database Access) -> SQLAlchemy 2.0 ORM.
   - Ép kiểu tĩnh 100% bằng TypeScript ở Frontend và sử dụng Pydantic V2 để validate đầu vào/đầu ra ở Backend.

---

## III. ĐIỂM ƯU (STRENGTHS)

* **Hiệu năng vượt trội (High Performance):**
  - Litestar là một ASGI framework cực kỳ gọn nhẹ và tối ưu, cho tốc độ xử lý nhanh hơn nhiều so với các framework truyền thống. Kết hợp với Svelte 5 (Zero-Hydration client state), giúp giữ thời gian phản hồi API luôn ở mức cực thấp (<200ms).
* **Tối ưu hóa SEO tối đa:**
  - Cấu trúc thư mục được thiết kế để tích hợp chặt chẽ với các dịch vụ SEO tự động (`seo_service.py`, `seo_graph_service.py`), hỗ trợ kết xuất SSR động cho các trang sản phẩm và tin tức nhằm đạt điểm số Lighthouse tối đa.
* **Cơ chế AI modular, dễ mở rộng:**
  - AI Engine được tách biệt độc lập trong `backend/services/ai_engine/`. Điều này cho phép dễ dàng thay thế các mô hình ngôn ngữ lớn (LLM) thông qua cấu hình `LiteLLM` hoặc thay đổi prompt system mà không ảnh hưởng đến logic nghiệp vụ thương mại cốt lõi.
* **Hệ thống bảo vệ chủ động (Ads Protection & Security):**
  - Kiến trúc có sẵn module giám sát `ads_protection` chuyên biệt chống click tặc, đồng thời áp dụng chính sách "Four Eyes Policy" (`four_eyes.py`) đối với các thao tác cấu hình hệ thống nhạy cảm.

---

## IV. ĐIỂM NHƯỢC (WEAKNESSS)

* **Rủi ro rò rỉ tài nguyên & Bộ nhớ hạn chế:**
  - Hệ thống chạy real-time stream (SSE/WebSockets cho giọng nói và phản hồi chat) trên máy chủ có tài nguyên giới hạn (4GB RAM). Việc quản lý giải phóng kết nối (`dispose`) nếu không được thực hiện nghiêm ngặt rất dễ gây tràn bộ nhớ (Memory Leak) hoặc nghẽn Event Loop.
* **Độ phức tạp cao trong việc debug luồng AI:**
  - Với sự tham gia của nhiều agent, semantic routers, và prompt entropy, việc tái dựng và debug một lỗi cụ thể trong quá trình chat/đặt hàng đòi hỏi phải phân tích log rất sâu qua nhiều tầng (Trinity Bridge -> Support Agent -> Handlers).
* **Nguy cơ lỗi giao diện khi binding Svelte 5:**
  - Việc cấm sử dụng fallback values trực tiếp cho `$bindable` props (bẫy binding của Svelte 5) yêu cầu lập trình viên phải luôn khởi tạo trạng thái an toàn ở mức Store hoặc `onMount`. Nếu quên, ứng dụng có thể gặp lỗi crash `props_invalid_value` trên client.
* **Phụ thuộc lớn vào API bên thứ ba:**
  - Các tính năng chính phụ thuộc chặt chẽ vào độ ổn định của API bên thứ ba (Google Ads API, Zalo OA API, các nhà cung cấp mô hình AI qua LiteLLM). Bất kỳ sự cố kết nối hoặc thay đổi chính sách nào từ đối tác cũng có thể gây ảnh hưởng trực tiếp đến hệ thống.
