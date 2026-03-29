# HIẾN PHÁP FAST-PLATFORM (ELITE V2.2)

> **CHỈ THỊ TỐI CAO:** Dự án Agentic AI 2026. Stack: **SvelteKit 5 (Runes: $state, $derived, $effect, $props) + Litestar (Python 3.14) + SQLAlchemy 2.0 + PydanticAI + LiteLLM**. Ép kiểu tĩnh 100% (CẤM 'any'). Hoạt động trên domain `*.smartshop.test`.
>
> > ** CẤM GIẢI THÍCH, LÀM XONG BÁO KẾT QUẢ.**

---

## 🛑 R00 – KỶ LUẬT TÁC CHIẾN (WAR ROOM PROTOCOL)

- ❌ **CẤM:** Sửa code/tạo file khi chưa được duyệt.
- ❌ **CẤM Tuyệt đối:** Hardcode giá trị logic, dùng dữ liệu giả (Mock Data/Placeholders) hoặc code `// TODO`. Mọi dữ liệu phải flow từ DB/API hoặc Config chính thống.
- ✅ **PROPOSE-FIRST:** Mọi thay đổi phải qua 2 giai đoạn: PROPOSE (Kế hoạch + Phản biện rủi ro RAM/Latency) -> HALT (Đợi duyệt).
- ✅ **QUY TRÌNH QUẢN TRỊ:** Bắt buộc duy trì `task.md` (check-list) và `walkthrough.md` (bằng chứng) cho mọi task.
- ✅ **QUANTUM SYNC:** Luôn nhắc Sếp hoặc chủ động `git pull --rebase` trước khi làm để tránh xung đột đa máy/đa bot.
- ✅ **FILE SIZE:** mỗi file không quá 500 dòng.

## 🔍 R01 – TRINH SÁT (SCOUT PROTOCOL)

- ❌ **CẤM:** Âm thầm sửa lỗi nằm ngoài yêu cầu (side-effects).
- ✅ **PHÁT HIỆN DỊ THƯỜNG:** Mọi bug, code thối hoặc điểm tối ưu phát hiện được trong lúc đọc file phải được báo cáo ở cuối luồng phân tích.

## 🛡️ R02 – BẢO MẬT & PHONG THÁI (HYGIENE & ETIQUETTE)

- ❌ **CẤM:** Hardcode API Key/Mật khẩu. CẤM log dữ liệu nhạy cảm.
- ✅ **TỰ KIỂM THỨC:** AI phải tự check log/lỗi UI sau khi code. Luôn bắt đầu bằng "Dạ vâng Sếp" hoặc "Thưa Sếp".
- ✅ **LATEST ONLY:** Luôn ưu tiên cài đặt/cập nhật thư viện bản mới nhất.

## 🚀 R03 – GIAO THỨC TIẾN HÓA (EVOLUTION PROTOCOL)

- 🧪 **TRINH SÁT CÔNG NGHỆ:** AI không được dậm chân tại chỗ. Phải luôn chủ động tìm kiếm các kỹ thuật lập trình, thuật toán và giải pháp kiến trúc mới nhất/tầng cao nhất để áp dụng cho Sếp.
- 💡 **ĐỀ XUẤT CẢI TIẾN:** Nếu thấy một giải pháp cũ (legacy) có thể thay thế bằng công nghệ mới hiệu quả hơn, BẮT BUỘC phải đề xuất trong bước PROPOSE.

## 🏗️ I. ĐỊA BÀN & HIỆU NĂNG (ULTRA-LEAN ARCHITECTURE)

- **Architecture Domain (Elite V2.2 Standard):**
  - 🧠 `backend/services/core/`: Các dịch vụ hệ thống (AI, Auth, Memory, EventBus).
  - 🛒 `backend/services/commerce/`: Nghiệp vụ bán hàng (Product, Checkout, Order, Category).
  - 🌐 `frontend/src/lib/state/commerce/`: Trạng thái Thương mại (Shop, Cart).
- **Naming Context:**
    - `commerce`: Dùng cho tầng **Domain/Logic** nghiệp vụ.
    - `client`: Dùng cho tầng **Access/Route** công khai (Storefront).
- **Zero-Barrier Protocol:** Các trang thuộc route `(client)` (Storefront) **BẮT BUỘC** phải duy trì khả năng truy cập công khai không cần Login để tối ưu chuyển đổi (CRO), trừ khi có chỉ thị đặc biệt.
- **Resource Discipline:** Phải "Dispose" ngay tài nguyên (WebSocket/SSE) khi xong để bảo vệ 2GB RAM.
- **Ultra-Fast UX:** Phản hồi <200ms. Luôn có Loading cho tác vụ dài. Cấm Request trùng lặp (Double-call).

## 🚫 III. DANH MỤC LỖI CẤM (ANTI-PATTERNS)

### 1. Lỗi Kỹ thuật (Technical Sins)

- ❌ **Blocking Async:** Cấm dùng hàm đồng bộ (sync) trong luồng async gây treo event loop.
- ❌ **Memory Leak:** Cấm quên `revokeObjectURL` hoặc không dọn dẹp `Event Listener` khi hủy component.
- ❌ **Svelte 5 Binding Trap:** CẤM dùng giá trị mặc định (fallback) cho `$bindable` props (ví dụ: `prop = $bindable("")`). Nếu cha truyền `undefined`, ứng dụng sẽ crash (`props_invalid_value`). Bắt buộc khởi tạo giá trị an toàn tại Store hoặc `onMount`.
- ❌ **Rune Abuse:** Cấm lạm dụng `$effect` trong Svelte 5 khi có thể dùng `$derived`.
- ❌ **Silent Fail:** Cấm dùng `try-catch` rỗng mà không có log hoặc báo cáo cho Sếp.

### 2. Lỗi Kiến Trúc & Bảo Tồn (Architecture & Preservation Sins)

- ❌ **Cấm đổi kiến trúc:** Giữ nguyên cấu trúc thư mục, file. Muốn đổi PHẢI hỏi.
- ❌ **Cấm sửa tính năng cũ:** Không xóa/sửa logic đang chạy. Chỉ fix và thêm.
- ❌ **Cấm dùng tech cũ:** Luôn dùng syntax mới nhất, không hạ cấp thư viện.
- ❌ **KISS (Đơn giản):** Code trực diện, dễ hiểu. Cấm bày vẽ phức tạp (Over-engineering).
- ❌ **YAGNI (Vừa đủ):** Chỉ làm đúng yêu cầu. Không thêm code thừa, không "lo xa" tính năng tương lai.
- ❌ **Xác nhận:** Luôn hỏi trước khi xóa code cũ hoặc refactor lớn.
- ✅ **PYDANTIC V2 ONLY:** CẤM dùng Pydantic V1 hoặc `pydantic.v1`. Mọi schema phải dùng Pydantic V2 (`model_config`, `field_validator`).
  - *Lưu ý (Python 3.14):* Tạm thời suppress `UserWarning` về "Pydantic V1 compatibility bridge" trong `docker-compose.yml` và `backend/__init__.py` do giới hạn của thư viện Litestar hiện tại. Sẽ gỡ bỏ khi thư viện cập nhật bản fix triệt để.

## 💎 IV. QUY TẮC Z-INDEX TẬP TRUNG (ELITE V2.2)

- ❌ **CẤM Tuyệt đối:** Hardcode giá trị `z-index` trong file `.svelte` hoặc dùng class Tailwind `z-[...]`.
- ✅ **SINGLE SOURCE OF TRUTH:** Toàn bộ `z-index` phải được khai báo tại `src/lib/core/constants/zIndex.ts`.
- ✅ **PORTAL ACTION:** Ưu tiên dùng `use:portal` cho các phần tử nổi (Modal, Overlay, Toast) để tách biệt Stacking Context.
- ✅ **GLOBAL SYNC:** Sử dụng CSS Variables được tiêm từ `+layout.svelte` cho các file `.css` thuần thông qua `--z-*`.
