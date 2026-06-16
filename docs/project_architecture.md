# SƠ ĐỒ VÀ PHÂN TÍCH KIẾN TRÚC DỰ ÁN (ELITE V2.3 - SOC ACTIVATED)

Tài liệu này cung cấp sơ đồ cây thư mục kiến trúc của dự án Fast-Platform (Elite V2.3) cùng với phân tích chi tiết về điểm mấu chốt, điểm ưu và điểm nhược trong thiết kế hệ thống, đặc biệt tích hợp hạ tầng **Security Operations Center (SOC)**.

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
│   │   ├── health.py                         # [SOC V2.3] Giám sát cơ sở dữ liệu, snapshot hệ thống & live SSE telemetry
│   │   ├── security.py                       # [SOC V2.3] Điều khiển registry kết nối, kill switch & Redis ops panel
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
│   │   ├── connection_registry.py            # [SOC V2.3] Registry giám sát và ngắt kết nối live stream (zombie switch)
│   │   ├── db_health_service.py              # [SOC V2.3] Chẩn đoán DB pool status, leaks, slow queries, locks & vacuum
│   │   ├── health_service.py                 # [SOC V2.3] Trích xuất snapshot phần cứng VPS (CPU/RAM/Redis)
│   │   ├── auth_service.py                   # Xử lý xác thực người dùng
│   │   └── event_bus.py                      # Hệ thống Bus sự kiện đồng bộ/bất đồng bộ
│   │
│   ├── database/                             # 💾 TẦNG DỮ LIỆU (SQLAlchemy 2.0 ORM)
│   │   ├── alchemy_config.py                 # [SOC V2.3] SQLAlchemy event listeners đếm leaks & slow queries
│   │   ├── repositories.py                   # Pattern Repository truy vấn Database an toàn
│   │   └── models/                           # Các thực thể dữ liệu (commerce, content, seo, auth, ads...)
│   │
│   ├── routers/                              # 🌐 TẦNG STREAMING & REAL-TIME
│   │   ├── intent.py, intent_core.py         # Nhận diện ý định giọng nói và điều phối luồng
│   │   └── content_stream.py, voice_stream.py# [SOC V2.3] Hook đăng ký vòng đời kết nối với registry
│   │
│   ├── schemas/                              # 🛡️ Pydantic V2 Schemas để Validation/Serialization
│   ├── infra/                                # ⚙️ Cấu hình hạ tầng (arq_config cho Background Worker)
│   └── constants/                            # 📌 Quản lý các biến hằng số (commerce, permissions, voice...)
│
│
├── frontend/                                 # ⚡ HỆ THỐNG FRONTEND (SvelteKit 5 + TypeScript + Runes)
│   ├── src/
│   │   ├── routes/                           # 🚦 ĐỊNH TUYẾN TRANG (SvelteKit Directory Routing)
│   │   │   ├── (client)/                     # 🛒 Nhóm storefront công khai cho khách hàng
│   │   │   └── (admin)/                      # 🔑 Nhóm quản trị hệ thống
│   │   │
│   │   └── lib/                              # 📦 THƯ VIỆN GIAO DIỆN & TRẠNG THÁI CHUNG
│   │       ├── components/                   # UI Components
│   │       │   ├── admin/
│   │       │   │   └── management/
│   │       │   │       └── SecuritySOC.svelte# [SOC V2.3] Dashboard Svelte 5 tabbed tích hợp Connections/DB/Redis
│   │       │   └── storefront/, widgets/
│   │       └── state/                        # Quản lý Client State sử dụng Svelte 5 Runes ($state)
│
├── scripts/                                  # 🛠️ CÁC TOOL SCRIPTS (Sync, setup SSL, database seed)
├── docker-compose.yml                        # 🐳 Điều phối môi trường Container (Backend, Frontend, Redis, DB)
└── CLAUDE.md                                 # 📜 Hiến pháp & Quy tắc lập trình tối cao của dự án
```

---

## II. ĐIỂM MẤU CHỐT TRONG KIẾN TRÚC (KEY ARCHITECTURAL POINTS)

1. **Kiến trúc hướng Agent (Agent-Centric Architecture):**
   - Hệ thống tích hợp sâu các tác nhân AI thông minh (Helen Agent, Ads Forensic Agent, Viral Share Agent) làm lõi xử lý nghiệp vụ tự động hóa từ phân tích click ảo đến đặt hàng và tư vấn khách hàng.
   - Giao tiếp giữa các Agent thông qua cầu nối trung gian `TrinityBridge` và hệ thống định tuyến ngữ nghĩa `SemanticRouter`.

2. **Hạ tầng SOC - Thiết kế Zero-Overhead & On-Demand Activation (Bảo vệ VPS 4GB):**
   - **Tắt mặc định (Default Off)**: Các module nặng như Connection Registry hay SSE Live Stream Monitor được vô hiệu hóa mặc định để bảo toàn tài nguyên RAM/CPU.
   - **Watchdog Tự động ngắt**: Khi Admin kích hoạt giám sát, hệ thống sẽ tự khởi động một luồng đếm ngược (watchdog). Nếu không phát hiện thao tác hoặc sau thời gian cấu hình (ví dụ 60 phút), registry sẽ tự chuyển sang trạng thái ngắt kết nối để giải phóng RAM tối đa.
   - **In-Memory SQLAlchemy Listener**: Việc đếm connection leaks và slow queries được thực hiện trực tiếp trên in-memory dict thông qua SQLAlchemy event listeners, đảm bảo không sinh thêm câu lệnh SQL dư thừa làm chậm luồng xử lý chính.

3. **Ứng dụng Svelte 5 Runes & HUD Giao diện Phân tách (Bento Grid / Tabbed Panel):**
   - Việc quản lý trạng thái động của các Widget điều hướng giọng nói và tab SOC sử dụng `$state`, `$derived`, `$effect` của Svelte 5 giúp giảm thiểu tối đa overhead.
   - Giao diện `SecuritySOC.svelte` phân chia khoa học thành 4 tab chức năng chuyên sâu, tương tác thời gian thực với backend qua hệ thống kiểm soát quyền `SYS_ADMIN`.

4. **Luồng dữ liệu chặt chẽ (Strict Data Flow Protocol):**
   - Client hoàn toàn không được truy vấn trực tiếp cơ sở dữ liệu. Mọi tương tác bắt buộc phải đi qua API Endpoint (Litestar Controllers) -> Services (Business Logic) -> Repositories (Database Access) -> SQLAlchemy 2.0 ORM.
   - Ép kiểu tĩnh 100% bằng TypeScript ở Frontend và sử dụng Pydantic V2 để validate đầu vào/đầu ra ở Backend.

---

## III. ĐIỂM ƯU (STRENGTHS)

* **Hiệu năng vượt trội & Chống rò rỉ (High Performance & Anti-Leak):**
  - Kết hợp Litestar ASGI gọn nhẹ và Svelte 5 giúp thời gian phản hồi API luôn ở mức cực thấp (<200ms).
  - Tích hợp **Connection Registry & Kill Switch** cho phép dọn dẹp cưỡng bức các kết nối SSE/WS rác hoặc IP spam (zombie connections) giúp bảo vệ RAM tối đa.
* **Database Telehealth Chuyên sâu:**
  - Hệ thống giám sát được chi tiết Pool status, Active locks, các cặp blocking queries gây treo db và độ phân mảnh (Bloat %) của từng bảng.
  - Cho phép quản trị viên thực thi **VACUUM ANALYZE** an toàn chạy nền (non-blocking) đối với các bảng whitelisted nhằm thu hồi không gian lưu trữ vật lý tức thời.
* **Redis Ops Panel An toàn:**
  - Thay vì sử dụng lệnh `KEYS` nguy hiểm gây nghẽn Redis đơn luồng, hệ thống sử dụng cơ chế `SCAN` tuần tự an toàn.
  - Cung cấp tính năng Flush theo từng Namespace whitelisted (`pulse:`, `spam:`, `helen:`) giải quyết triệt để vấn đề đầy bộ nhớ Redis.
* **Tối ưu hóa SEO tối đa:**
  - Cấu trúc thư mục được thiết kế để tích hợp chặt chẽ với các dịch vụ SEO tự động (`seo_service.py`), hỗ trợ kết xuất SSR động cho các trang sản phẩm và tin tức nhằm đạt điểm số Lighthouse tối đa.

---

## IV. ĐIỂM NHƯỢC (WEAKNESSES)

* **Độ phức tạp khi giám sát thời gian thực:**
  - Việc quản lý registry kết nối hoạt động bất đồng bộ (`asyncio`) đòi hỏi kiểm tra kỹ trạng thái kết nối ở các generator loop để tránh exception `RuntimeError` khi đóng kết nối đột ngột từ phía client.
* **Giới hạn an toàn của VACUUM & Redis Flush:**
  - Việc giới hạn danh sách bảng whitelisted có quyền chạy `VACUUM` hoặc các key được phép `FLUSH` là bắt buộc để tránh phá hủy cấu trúc dữ liệu hệ thống từ tài khoản admin bị lộ. Lập trình viên cần bổ sung thủ công cấu hình khi thêm bảng nghiệp vụ mới.
* **Độ phức tạp cao trong việc debug luồng AI:**
  - Với sự tham gia của nhiều agent, semantic routers, và prompt entropy, việc tái dựng và debug một lỗi cụ thể trong quá trình chat/đặt hàng đòi hỏi phải phân tích log rất sâu qua nhiều tầng (Trinity Bridge -> Support Agent -> Handlers).
* **Nguy cơ lỗi giao diện khi binding Svelte 5:**
  - Việc cấm sử dụng fallback values trực tiếp cho `$bindable` props yêu cầu lập trình viên phải luôn khởi tạo trạng thái an toàn ở mức Store hoặc `onMount` để tránh lỗi crash `props_invalid_value` trên client.
