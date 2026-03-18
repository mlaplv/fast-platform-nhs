# Changelog

All notable changes to the **Fast Platform Core** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
