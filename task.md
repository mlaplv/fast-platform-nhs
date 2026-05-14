# Task: Elite V2.2 Landing Optimization (Performance, SEO & Semantics)

- [x] **Phase 1: Vietnamese Semantics**
    - [x] Standardize terminology: Replace "lột xác" with "đặc quyền" and "thăng hạng nhan sắc" across all marketing components.
    - [x] Fix sentence casing and professionalism in `OfferGrid`, `ViralFunnelLanding`.
- [x] **Phase 2: Performance Optimization (< 1s)**
    - [x] Implement JIT/Lazy loading for below-the-fold images in `OfferCard`.
    - [x] Enable `decoding="async"` for all high-impact storefront images.
    - [x] Cleanup legacy regex and unused reactivity in `HeroBanner`, `OfferGrid`.
- [x] **Phase 3: SEO & AI SGE Protocol**
    - [x] Remove hidden H1 tags (`clip: rect`) in `HomeMobile.svelte`.
    - [x] Integrate visible H1 tags into the natural layout in `HeroBanner` (Desktop) and `MobileHero` (Mobile).
    - [x] Optimize accessibility with `aria-hidden` for decorative elements.
