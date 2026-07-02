# Kế Hoạch Triển Khai Chi Tiết: Schema `HowTo` & Đối Phó Google Spam Update (Tháng 6/2026)

Kế hoạch này phân tách lộ trình thực hiện thành 7 giai đoạn rõ ràng bao gồm: Thiết kế Database, Cơ chế Thu thập và Nhập dữ liệu (Thủ công + Tự động), Logic xử lý Backend, Đồng bộ Frontend, Tối ưu hóa AI Agent và Kiểm thử.

---

## BẢN ĐỒ PHÂN CHIA GIAI ĐOẠN (ROADMAP)

```mermaid
grid
    GiaiDoan1["Phase 1: Database & Model"]
    GiaiDoan2["Phase 2: Operational Data Input & AI Extraction"]
    GiaiDoan3["Phase 3: Intent-based Schema Builder"]
    GiaiDoan4["Phase 4: Spam Protection Hardening"]
    GiaiDoan5["Phase 5: Frontend Ingestion & Client Config"]
    GiaiDoan6["Phase 6: AI Creative Studio & E-E-A-T Agent"]
    GiaiDoan7["Phase 7: QA, Verification & Performance"]
```

---

## HƯỚNG DẪN CHI TIẾT TỪNG GIAI ĐOẠN

### GIAI ĐOẠN 1: Database & Mô hình Dữ liệu (Backend/DB)
*   **Mục tiêu:** Tạo cấu trúc lưu trữ dữ liệu `HowTo` và cấu hình Spam Protection trong Database.
*   **Chi tiết thực hiện:**
    1.  **DB Migration (`PostgreSQL`):**
        *   Cấu trúc cột `article_metadata` (JSONB) của bảng `articles` để lưu trữ dữ liệu HowTo. Cấu trúc JSON chuẩn như sau:
            ```json
            {
              "how_to": {
                "total_time": "PT10M", 
                "tools": [{"name": "Dụng cụ A"}],
                "supplies": [{"name": "Nguyên liệu B"}],
                "steps": [
                  {"name": "Bước 1", "text": "Mô tả bước 1", "image": "URL_ảnh"}
                ]
              }
            }
            ```
    2.  **Di chuyển Cấu hình (System Settings):**
        *   Di chuyển `authority_map` (danh sách keyword trỏ đến các site uy tín như PubMed, Harvard) từ code cứng trong `seo_service.py` vào cấu hình JSONB trong bảng `system_settings` trong DB.

---

### GIAI ĐOẠN 2: Cơ chế Thu thập & Nhập Dữ liệu (Operational Input)
*   **Mục tiêu:** Xác định rõ dữ liệu `HowTo` được nhập và xử lý từ nguồn nào trước khi xuất bản.
*   **Chi tiết thực hiện:**
    1.  **Luồng 1: AI Auto-Extraction (Tự động):**
        *   Khi AI viết bài trong Creative Studio, nếu bài viết được phân loại intent là `informational_how`, một tiến trình AI nền sẽ tự động bóc tách bài viết thành các trường: `steps`, `tools`, `supplies` và `total_time` dưới dạng JSON và lưu nháp vào `article_metadata["how_to"]`.
    2.  **Luồng 2: Admin Manual Input (Thủ công):**
        *   Tại trang quản trị (`DraftGenerativeForm.svelte` hoặc `NewsManagement.svelte`), bổ sung tab **"Cấu hình HowTo"** cho phép Admin chỉnh sửa trực quan danh sách dụng cụ, nguyên liệu, và các bước thực hiện (tiêu đề, mô tả, ảnh minh họa từng bước).
        *   Khi lưu bài viết, dữ liệu này sẽ được đồng bộ gửi lên API để ghi đè vào DB.
    3.  **Luồng 3: HTML Parser Fallback (Cứu cánh):**
        *   Nếu không có dữ liệu nhập tay hoặc AI bóc tách trước đó, khi render SEO, backend sẽ chạy một bộ lọc HTML để trích xuất danh sách bước tự động từ các thẻ `<ol>` hoặc các thẻ tiêu đề dạng `<h3>Bước X: ...</h3>` trong nội dung bài viết.

---

### GIAI ĐOẠN 3: Intent-based Schema Builder (Backend)
*   **Mục tiêu:** Sinh mã JSON-LD của `HowTo` từ dữ liệu đã lưu trữ.
*   **Chi tiết thực hiện:**
    1.  **Ánh xạ Intent:**
        *   Kích hoạt logic trong `seo_entity_extractor.py` để map intent `"informational_how"` sang schema type `"HowTo"`.
    2.  **Xây dựng `HowTo` Generator (`seo_service.py`):**
        *   Tạo hàm `_build_how_to_ld(title, url, desc, how_to_data)` chuyển đổi object JSON sang schema `@type: "HowTo"` với các nút con `@type: "HowToStep"`, `HowToTool`, `HowToSupply`.
    3.  **Cơ chế Fallback bảo vệ:**
        *   Nếu bài viết là `informational_how` nhưng không có dữ liệu bước thực hiện (`steps`), hệ thống tự động fallback về `Article` để tránh lỗi cảnh báo của Google Search Console.

---

### GIAI ĐOẠN 4: Spam Protection Hardening (Backend)
*   **Mục tiêu:** Khắc phục các vấn đề liên quan đến Google Spam Update (Tháng 6/2026).
*   **Chi tiết thực hiện:**
    1.  **Sửa lỗi `@id` Entropy (`schema_mutator.py`):**
        *   **Xóa bỏ** thuật toán MD5 suffix trên `@id` của thực thể. Giữ nguyên `@id` dạng IRI tĩnh vĩnh viễn (ví dụ: `{canonical_url}#howto`) để Google và AI Searchresolve thực thể chính xác.
    2.  **Harden Outbound Links (`seo_service.py`):**
        *   Cập nhật `harden_external_links` để chèn thuộc tính `rel="nofollow noopener noreferrer"` vào tất cả liên kết trỏ ra ngoài hệ thống nhằm tuân thủ chính sách chống Link Spam của Google.
    3.  **Anchor Text Diversification (`seo_contextual_linker.py`):**
        *   Cài đặt bộ đa dạng hóa anchor text, cấm dùng cùng một anchor text cho cùng một link đích quá 15% tổng số liên kết nội bộ.

---

### GIAI ĐOẠN 5: Frontend Ingestion & Client Config (Frontend)
*   **Mục tiêu:** Xuất bản Schema động ra mã nguồn HTML và quản lý các file cấu hình crawler.
*   **Chi tiết thực hiện:**
    1.  **Hợp nhất `@graph` (`SeoHead.svelte` & `schemaFactory.svelte.ts`):**
        *   Đảm bảo chuỗi JSON-LD `HowTo` sinh từ backend đi qua cổng lọc frontend và được hợp nhất trực tiếp vào khối `<script type="application/ld+json" id="seo-schema-graph">` duy nhất.
    2.  **Tạo Robots.txt động (`robots.txt/+server.ts`):**
        *   Mở quyền crawl cho các AI Search Bot hữu ích (`GPTBot`, `PerplexityBot`).
        *   Chặn các AI Training Bot (`Google-Extended`, `CCBot`).
    3.  **Sitemap động (`sitemap.xml/+server.ts`):**
        *   Sinh sitemap tự động lấy trực tiếp từ DB kèm trường `lastmod` lấy từ `updated_at` của bài viết và sản phẩm để cung cấp Freshness signal cho AI Search.

---

### GIAI ĐOẠN 6: AI Creative Studio & E-E-A-T Agent
*   **Mục tiêu:** Cải tiến chất lượng sinh bài viết AI để vượt qua cơ chế SpamBrain 2026.
*   **Chi tiết thực hiện:**
    1.  **Multi-Agent Research Pipeline:**
        *   Tích hợp tác vụ: Agent 1 quét dữ liệu nghiên cứu khoa học thực tế từ internet → Đẩy ngữ cảnh vào Agent 2 viết bài để tăng tính nguyên bản, tránh sinh bài viết AI sáo rỗng.
    2.  **E-E-A-T Credentials:**
        *   Điều chỉnh Prompt của AI Writer để chèn các cấu trúc y khoa có kiểm chứng (bảng biểu `<figure class="xohi-clinical-table">`) và gán thông tin tác giả thực tế có uy tín (schema `Person` trỏ đến LinkedIn/Profile y khoa).

---

### GIAI ĐOẠN 7: QA, Xác minh & Tối ưu hóa Hiệu năng
*   **Mục tiêu:** Đánh giá tính chính xác của dữ liệu cấu trúc và dọn dẹp code dư thừa.
*   **Chi tiết thực hiện:**
    1.  **Google Rich Results Test:**
        *   Sử dụng công cụ kiểm tra của Google để xác nhận schema `HowTo` hiển thị tick xanh không có cảnh báo.
    2.  **Dọn dẹp code dư thừa (KISS):**
        *   Giảm số lớp lọc trùng lặp schema (Deduplication) ở Frontend từ 4 lớp xuống 2 lớp (giữ lại Layer 1: `containsSchemaType` và Layer 2: `buildGraphLd` trong Map. Loại bỏ Layer 3 và Layer 4 DOM setTimeout vì gây lãng phí CPU client và không có tác dụng với SEO SSR).
