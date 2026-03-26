# Task: Giai đoạn 7 - Advanced Asset Optimization & Smart Download

## 🎯 Mục tiêu
Nâng cấp khả năng xử lý ảnh động và tải xuống hàng loạt thông minh.

## 📝 Check-list
- [x] Backend: Triển khai Dynamic Image Resizing API (Thumbnail Engine). <!-- id: 0 -->
- [x] Backend: Triển khai API `/api/v1/media/bulk-download` (ZIP Generation). <!-- id: 1 -->
- [x] Logic: Cập nhật `media.svelte.ts` hỗ trợ `bulkDownload`. <!-- id: 2 -->
- [x] UI: Tích hợp Thumbnail preview vào Grid để tối ưu tốc độ load. <!-- id: 3 -->
- [x] UI: Thêm nút "Tải xuống ZIP" vào Bulk Action Toolbar. <!-- id: 4 -->
- [x] UI: Thêm tính năng "Quick Edit" (Xoay/Lật ảnh) trong Detail Panel. <!-- id: 5 -->

## 🛠️ Trạng thái: Completed Phase 8
- AI Semantic Search (Vector Match) hoạt động cực nhạy với tiếng Việt.
- Surgical Update + Cache-busting đảm bảo UX siêu tốc.
- Cơ chế tự dọn dẹp (Cleanup Loop) bảo vệ tài nguyên server.
- Giao diện AI Processing mượt mà, hiện đại.

## 🎯 Giai đoạn 9: Cloud Ecosystem & CDN Integration
- [x] Backend: Triển khai S3/Cloudflare R2 Provider (Hỗ trợ Multi-storage). <!-- id: 11 -->
- [x] Backend: Tích hợp CDN Cache Invalidation khi edit ảnh trên Cloud. <!-- id: 12 -->
- [x] Logic: Hỗ trợ "Remote Fetch" (Tải ảnh từ URL trực tiếp vào Library). <!-- id: 13 -->
- [x] UI: Dashboard thống kê dung lượng và định dạng tài nguyên. <!-- id: 14 -->
- [x] UI: Tích hợp FileManager vào CKEditor/Article Editor làm Plugin. <!-- id: 15 -->

## 🎯 Giai đoạn 10: Elite Optimization & Safety (COMPLETED)
- [x] UI: Image Crop & Transformation Presets (Square, Banner, Story). <!-- id: 16 -->
- [x] Backend: Dynamic Watermarking Engine (Logo overlay + Text Fallback). <!-- id: 17 -->
- [x] UI/UX: Trash Bin & Soft-delete Recovery logic. <!-- id: 18 -->
- [x] Backend: RBAC for Media Assets (Private vs Public). <!-- id: 19 -->
- [x] Backend: Auto-purge Trash Bin logic (30 days lifecycle). <!-- id: 20 -->

## 🎯 Giai đoạn 13: Elite V2.2 Zero-Hydration & Service-Centric (COMPLETED)
- [x] Backend: Refactor `ArticleController` to use Scalar Projection (Rule 1.5). <!-- id: 31 -->
- [x] Backend: Standardize `ProductController` mutation responses to `SuccessResponse`. <!-- id: 32 -->
- [x] Backend: Refactor `SettingsController` for Zero-Hydration & Pydantic V2. <!-- id: 33 -->
- [x] Backend: Refactor `AIController` for Pydantic V2 strictness. <!-- id: 34 -->
- [x] Backend: Refactor `CategoryController` for Zero-Hydration & SuccessResponse. <!-- id: 36 -->
- [x] Backend: Refactor `OrderController` & `UserController` for Zero-Hydration & Pydantic V2. <!-- id: 37 -->
- [x] Backend: Consolidate Auth (Social/OTP) into unified Service/Controller. <!-- id: 38 -->
- [x] Frontend: Fix Notification filter crash (API format sync). <!-- id: 39 -->
- [x] Documentation: Update `walkthrough.md` with new architectural standards. <!-- id: 35 -->
- [x] Cleanup: Remove all `auth_extended` remnants and stale dependencies. <!-- id: 40 -->
- [x] Final Audit: Verify 100% Service-Centric compliance for all controllers. <!-- id: 41 -->

## 🎯 Giai đoạn 18: Order Management Optimization (Elite V2.2) (COMPLETED)
- [x] Logic: Centralize format utilities (currency, date, timeAgo) in `src/lib/utils/format.ts`. <!-- id: 80 -->
- [x] UI: Refactor `OrderDetailDrawer.svelte` (Z-index CSS variables, centralized format utils). <!-- id: 81 -->
- [x] UI: Refactor `OrderFilters.svelte` (Z-index CSS variables). <!-- id: 82 -->
- [x] UI: Refactor `OrderListItem.svelte` (Z-index, format utils, optimize `timeAgo` re-renders). <!-- id: 83 -->
- [x] UI: Refactor `OrderManagement.svelte` (Rune optimization, clean up effects). <!-- id: 84 -->
- [x] UI: Refactor `OrderPagination.svelte` (Z-index CSS variables). <!-- id: 85 -->

## 🎯 Giai đoạn 17: Scouting & Documentation (COMPLETED)
- [x] Scout: Vẽ cấu trúc cây thư mục dự án (project.md). <!-- id: 70 -->
- [x] Design: Đề xuất và tích hợp cấu trúc trang bán hàng (Client) vào project.md. <!-- id: 71 -->
- [x] Optimization: Cập nhật project.md theo Best Practice Elite V2.2 & Ghi chú trực tiếp. <!-- id: 72 -->
- [x] Security: Triển khai Domain Guard Middleware cô lập Admin/Client. <!-- id: 73 -->

## 🎯 Giai đoạn 19: Product Management Optimization (Elite V2.2) (COMPLETED)
- [x] Logic: Centralize format utilities (currency) in `ProductManagement.svelte`. <!-- id: 90 -->
- [x] UI: Refactor `ProductTable.svelte` (Z-index CSS variables, centralized format utils). <!-- id: 91 -->
- [x] UI: Refactor `ProductStats.svelte` (Remove prop drilling for format utils, Z-index CSS variables). <!-- id: 92 -->
- [x] Cleanup: Remove local scrollbar CSS in `ProductToolbar.svelte`. <!-- id: 93 -->
- [x] Logic: Replace `any[]` with proper interfaces in `ProductManagement.svelte`. <!-- id: 94 -->

## 🎯 Giai đoạn 20: Order Management Deep Reconnaissance (R01) (COMPLETED)
- [x] Scout: Kiểm tra toàn bộ components thuộc Order Management về Z-index (Protocol R04). <!-- id: 100 -->
- [x] Scout: Kiểm tra Type Safety (Protocol R03) trong Order-related components. <!-- id: 101 -->
- [x] Propose: Đề xuất phương án refactor nếu phát hiện sai lệch Protocol. <!-- id: 102 -->

## 🎯 Giai đoạn 21: Order Management Refactoring (Elite V2.2) (COMPLETED)
- [x] UI: Fix Z-index violation in `OrderListItem.svelte` (Replace `z-[100]` with `var(--z-popover)`). <!-- id: 110 -->
- [x] Logic: Ensure strict `unknown` type in all `catch` blocks in Order components. <!-- id: 111 -->
- [x] Logic: Standardize prop interfaces and rune usage across Order components. <!-- id: 112 -->



## 🎯 Giai đoạn 22: Advanced Structural Noise Cleaning (Elite V2.2) (COMPLETED)
- [x] Backend: Install `lxml` for high-performance DOM manipulation. <!-- id: 120 -->
- [x] Backend: Refactor `NoiseCleaner` to use tree-based structural pruning. <!-- id: 121 -->
- [x] Backend: Remove legacy Regex-based "patchwork" loops. <!-- id: 122 -->
- [x] Final: Verify logic with nested empty tags and reporting. <!-- id: 123 -->

## 🎯 Giai đoạn 23: Performance Optimization & Hybrid Cleaning (Elite V2.2) (COMPLETED)
- [x] Backend: Optimize `NoiseCleaner` performance using `asyncio.to_thread` for CPU-bound tasks. <!-- id: 130 -->
- [x] Backend: Implement Hybrid Cleaning (Flashtext O(N) + RapidFuzz O(N log M)). <!-- id: 131 -->
- [x] Backend: Fix Flashtext exact match bug (Space-replacement mapping). <!-- id: 132 -->
- [x] Final: Verify performance with 277k character stress test (< 200ms). <!-- id: 133 -->

## 🎯 Giai đoạn 24: Cross-Browser Sync & Deterministic Normalization (Elite V2.2) (COMPLETED)
- [x] Frontend: Implement recursive `prune` function in `TiptapEditor.svelte`. <!-- id: 140 -->
- [x] Frontend: Add `normalizeHTML` in `xohiAnalysis.svelte.ts` to sync with editor logic. <!-- id: 141 -->
- [x] Logic: Eliminate flicker and cursor jumping on Safari/Firefox via deterministic normalization. <!-- id: 142 -->
- [x] Final: Verify zero-diff between Frontend and Backend cleaning output. <!-- id: 143 -->

## 🎯 Giai đoạn 25: RAG Startup Optimization & AI Core Warmup (Elite V2.2) (COMPLETED)
- [x] Backend: Parallelize Event Bus, Trinity Bridge, and Vector Encoder warmup in `lifespan.py`. <!-- id: 150 -->
- [x] Backend: Resolve "Product Encoder not ready" warning by ensuring early initialization. <!-- id: 151 -->
- [x] Backend: Clean up redundant service subscriptions and initializations in lifespan logic. <!-- id: 152 -->

## 🎯 Giai đoạn 26: NoiseCleaner Toolbar Sync Fix (Elite V2.2) (COMPLETED)
- [x] Frontend: Import `tick` and implement robust locking in `TiptapEditor.svelte`. <!-- id: 160 -->
- [x] Frontend: Extend `isInternalUpdating` lock to prevent redundant `$effect` sync. <!-- id: 161 -->
- [x] Logic: Ensure `onChange` is called after DOM has stabilized. <!-- id: 162 -->
- [x] Final: Verify toolbar "NoiseCleaner" updates UI correctly. <!-- id: 163 -->
