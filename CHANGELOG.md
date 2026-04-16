# Changelog

All notable changes to the **Fast Platform Core** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [22.4.16.01] - 2026-04-16
### Added
- **Dynamic Voucher Integration (Elite V2.2):** Replaced legacy hardcoded lists with a database-driven architecture using `PromotionAdminService`. Added `title` and `subtitle` to the `Voucher` model for premium UI labeling.
- **Global Data Hub (Sync V2):** Implemented `GET /api/v1/client/home/vouchers` for lightweight global synchronization. Updated store layout to fetch and hydrate vouchers across all landing pages (Home, Product Detail, Checkout).
- **Strict Typing Protocol (Compliance R03):** Created `HomeDataResponse` and `VoucherListResponse` Pydantic schemas to eliminate `Dict[str, Any]` in public controllers.

### Changed
- **Zero-Hydration Optimization:** Re-architected `+layout.server.ts` to use parallel `Promise.all` fetches for a consistent <200ms TTFB.
- **Refined Product Metadata:** Expanded `ProductMetadata` TS interface to include strict types for rating, brand metrics, and video trimming (R00).

### Fixed
- **The "Missing 4" Bug:** Resolved critical layout data-flow issue where only hardcoded fallback vouchers were visible on direct product page entries.
- **Master Cleanup:** Removed 100% of `(metadata as any)` casts from the storefront rendering engine ensuring strict Elite V2.2 compliance.

## [22.3.12.13] - 2026-03-22
### Added
- **Discovery-First Intelligence (Phase 15):** Integrated `DiscoveryHunter` to perform real-time Google Search trinh sát for topic context (snippets) before analysis.
- **Neural Intent Guard (Phase 15.2):** Implemented a 3-stage reasoning process in `VisionInsight` (Disambiguation, Semantic Matching, Intent Lock) to eliminate entity hallucinations.
- **Strategic Image Filtering (Phase 15.3):** Implemented "Subject-Locking" and automated negative keyword injection in `AssetHunter` to eliminate naming noise (e.g., product brands vs persons).
- **Ultra-Premium Loading UI (Phase 16):** Created `UltraPremiumLoading.svelte` with mesh gradients, a glassmorphic "Neural Core", and dynamic "Data Crystals" for a world-class iPhone 18 aesthetic.
- **Zero-Latency Trigger (Phase 16.1):** Re-architected Step 1 to use background analysis (Nói là làm liền), allowing the Content Factory modal to open instantly with the premium loading UI.
- **Enhanced Live Intelligence (Phase 15.4):** Upgraded real-time progress reporting in `VisionInsight` and `AssetHunter` to show detailed Ground Truth snippets and exact search queries.

### Changed
- **Context Propagation (Phase 15.1):** Added `ground_truth` field to `TopicSeed` to synchronize real-time search context across `VisionInsight`, `AssetHunter`, and `CreativePen`.
- **Golden Thread Refinement:** Updated `AssetHunter` and `CreativePen` prompts to strictly respect discovered truth (e.g., distinguishing between brands and biological species).

### Fixed
- **Master Purge (Phase 14):** Implemented a full state and data purge (`fullPurge`) on campaign deletion or publication, ensuring no "stale" context or assets remain in the UI/Store.
- **Entity Hallucination:** Effectively resolved the issue where AI misidentified product brands as biological fungus or martial arts schools.

## [22.3.25.01] - 2026-03-25
### Added
- **Elite Backup & Restore (Elite V2.2):** Integrated professional-grade **password-protected** backup/restore suite into `xohi.sh` featuring **AES-256-CBC encryption**, SHA256 integrity checks, manifest-based versioning (Git Hash), auto-pruning (last 5 backups), a pre-restore safety net, and a **secure purge function** with **Admin Password verification** against the database.
- **Standardized SSE Discipline (Elite V2.2):** Implemented mandatory 15s heartbeats and strict lifecycle cut-offs (Pulse: 4h, Content: 30m, Intent: 5m) to eliminate zombie resource leaks.
- **Proxy-Aware Header Suite:** Injected `X-Accel-Buffering: no`, `Cache-Control: no-cache`, and `Connection: keep-alive` into all streaming responses to bypass proxy buffering.
- **Trinity Boot Architecture (Backend):** Refactored lifespan logic into a 3-stage asynchronous sequence with unified Elite log aesthetics and silenced infrastructure noise (SQLAlchemy, Uvicorn).
- **Lazy AI Warmup:** Introduced `get_shared_encoder()` for `fastembed` to eliminate blocking side-effects during module import.

### Changed
- **Elite DI Purge:** Converted `ArticleVectorService`, `ProductVectorService`, and business services from global singletons to Litestar-injected instances, achieving 100% architectural decoupling.
- **Caddy Protocol Optimization:** Patched `Caddyfile` to exclude binary/event streams from compression, resolving `ERR_HTTP2_PROTOCOL_ERROR` and `502` disconnects.

### Fixed
- **Pulse Stream Stability:** Resolved persistent HTTP/2 protocol errors through compression exclusion and heartbeat synchronization.
- **Vector Service Type Safety:** Fixed `match_score` calculation to handle potential `None` values and enforced strict float conversion.

## [22.3.24.01] - 2026-03-24

### Added
- **Centralized Z-Index Management (Elite V2.2):** Introduced `src/lib/core/constants/zIndex.ts` to eliminate magic numbers and ensure consistent stacking of VUI, Modals, and Toasts.
- **Portal Action Integration:** Applied `use:portal` to `VoiceModal` to decouple it from the main layout's stacking context.

### Fixed
- **VUI Stream Stability:** Resolved `ReferenceError: dataPkg is not defined` in `VuiStreamManager.ts`.
- **Data Synchronization (Smart Flattening):** Implemented automated promotion of nested payload data in `intent_manager.svelte.ts` to ensure widgets (e.g., `RevenueChart`) receive structured datasets correctly.
- **Revenue Chart UI:** Fixed discrepancy between spoken values and visual display; the "Big Number" now reflects the AI's reported total instead of the full series sum.
- **Overlay Stacking:** Resolved z-index conflicts between `VoiceModal` and `UniversalModal` (Modals now correctly appear on top of the Assistant).
- **VUI Lifecycle:** Decoupled VUI auto-close from navigation actions to ensure UI elements remain visible after the assistant finishes speaking.

### Changed
- **ContentOrchestrator Logic:** Tighter semantic checks introduced when mapping new voice inputs to active campaigns to avoid false positives.

---
*Note: This log follows the War Room Protocol (R00) and Evolution Protocol (R03) of Elite V2.2 Architecture.*
