# Task Checklist - Restoring Support System Connectivity

- [x] Restart the exited `fast_platform_api` container and verify it is running and healthy. (Done)
- [x] Verify end-to-end delivery of the Telegram notification pipeline using the `test_notification.py` framework. (Done)
- [x] Clean up the exited orphan `fast_platform_ui` container. (Done - verified cleaned and purged)
- [x] Add the `restart: always` directive to the `api` service in `docker-compose.yml` to prevent future silent downings. (Done - verified configured and active)
- [x] Perform a full system status verify and ensure no memory leaks or stuck background workers exist. (Done - increased worker_fraud limit to 384M to secure memory cushion)

# Task Checklist - Chat UI Aesthetic & Space Optimization (Elite V2.2)

- [x] Transition chat window from irregular morphing blob (`helen-box-v2`) to static, ultra-premium iOS-style rounded rectangle (`helen-box-premium`, `rounded-[36px]`). (Done)
- [x] Replace zero-background floating message text with elegant glassmorphic bubbles (User: pink gradient glass, Helen: subtle white/gray glass). (Done)
- [x] Optimize chat thread vertical flow (reduce spacing from `space-y-12` to `space-y-6`, adjust message label padding). (Done)
- [x] Refine the bottom input capsule (reduce bloat, shrink input height, and scale down the send button). (Done)
- [x] Polish quick action tags and tooltips to avoid overflowing and visual clutter. (Done)
- [x] Verify there are zero runtime warnings, layout shifts, or horizontal scroll bleedings. (Done - svelte-check compiles 100% clean and type-safe)

# Task Checklist - SOC Infrastructure Controls & Container Monitoring (Elite V2.2)

- [x] Create non-blocking async Docker monitoring endpoints in `/api/v1/security/containers` to fetch raw container stats. (Done)
- [x] Create administrative trigger control in `/api/v1/security/containers/action` for starting, stopping, and restarting containers. (Done)
- [x] Update SOC admin dashboard with real-time memory/CPU metrics, PID counts, and status indicators. (Done)
- [x] Configure safe visual alerts for high-memory containers in Svelte 5 dashboard to prevent OOM events. (Done)
- [x] Implement robust TypeScript interface typing to achieve 100% type-safety (svelte-check zero warning/error compliance). (Done)

# Task Checklist - Advanced Product Variant Gifts (Elite V2.2)

- [x] Keep existing free-form manual gift text & image upload feature in product variants configuration table. (Done)
- [x] Integrate advanced DB-linked product search API call inside gift rows, utilizing safe debounced inputs. (Done)
- [x] Support automatic variant detection and dynamic variant selection dropdown for DB-linked gifts. (Done)
- [x] Sync gift thumbnail image dynamically when variant selection changes. (Done)
- [x] Achieve 100% type safety and clean reactive loading using Svelte 5 Runes. (Done)
- [x] Integrate click-to-product navigation using dynamic slug mapping across all client interfaces (MainDetail Desktop/Mobile, LandingPage, MobileOffer, OfferCard). (Done)

# Task Checklist - Voucher & Promotion Management (Elite V2.2)

- [x] Design a highly premium, unified **ON/OFF Toggle Switch** (`AUTO-STICK: ON` / `AUTO-STICK: OFF`) to replace split badges/buttons in voucher list items. (Done)
- [x] Enhance `BulkActionBar.svelte` to support optional mass default configuration and state restoration buttons (`onUnsetDefaultBulk`). (Done)
- [x] Fix backend `bulk_update_status` query to securely support `is_default: false` so that unsetting auto-stick defaults only targets the selected voucher IDs. (Done)

# Task Checklist - Storefront Campaign Aesthetics Refinement (Elite V2.2)

- [x] Completely remove dynamic "FOMO" and "VIRAL" strips from all product detail interfaces (`OfferCard.svelte`, `MainDetail/modules/Info.svelte`, `LandingPage/modules/Info.svelte`) to maintain high-end, premium, and clean user experience. (Done)

# Task Checklist - Storefront Offer Card Voucher Visual Refinement (Elite V2.2)

- [x] Relocate the dynamic voucher text directly below the price cluster, replacing the old free ship/discount stickers. (Done)
- [x] Add an elegant "Xem thêm" flat text button next to the voucher display that triggers bottom-sheet view via `onOpenVouchers(variant.id)`. (Done)
- [x] Completely delete the `package-offer-box` container block and its specular highlight/rotating border layers from the bottom of the card. (Done)
- [x] Verify zero lints, warnings, or layout shifts and complete successful static production build. (Done)

# Task Checklist - Image Overlay Gift Capsule Redesign (Elite V2.2)

- [x] Redesign the image gift overlay block inside `OfferCard.svelte` to be a highly-compact horizontal capsule. (Done)
- [x] Integrate premium glassmorphism (`bg-black/60 backdrop-blur-xl`), active pulsing dot indicator, and high-tech metallic shimmer sweep animation. (Done)
- [x] Format product thumbnail as a sleek circular avatar (`rounded-full`) with a glowing fine border. (Done)
- [x] Ensure perfect alignment, responsive styling, and complete successful static production build. (Done)


# Task Checklist - Minimalist Convertive Gift Display & Dynamic DB Price Injection (Elite V2.2)

- [x] Remove legacy "Quà" text and pulsing neon indicator from the image gift overlay capsule to achieve an ultra-clean minimalist look. (Done)
- [x] Format gift thumbnail images inside the capsule as rounded-square avatars (`rounded-lg`) instead of circles, scaling to `w-8 h-8` for optimal detail. (Done)
- [x] Implement a highly robust dynamic `getGiftPrice(gift)` value resolver that dynamically calculates the authentic product pricing from DB/attributes. (Done)
- [x] Inject an exclusive dynamic sub-text line below the gift name inside the image overlay capsule: "Quà tặng độc quyền trị giá [giá trị]". (Done)
- [x] Ensure perfect responsiveness, zero layout shifting, 100% Svelte 5 compilation compliance, and verify build stability. (Done)


# Task Checklist - Storefront Offer Card Shadow & Overflow Optimization (Elite V2.2)

- [x] Reduce inline card active shadow from `0 0 80px` (too large, causing clipping) to a modern, clean `0 8px 24px` in `OfferCard.svelte`. (Done)
- [x] Reduce `.active` card box shadow from `0 0 60px` to `0 8px 24px` with a subtle inner shadow of `0 0 12px` in `OfferGrid.css` to prevent border cutoff. (Done)
- [x] Tame hover vertical translation (`translateY`) from a dramatic `-15px` to a smooth, elegant `-4px` and scale down the hover shadow to `0 12px 24px` to secure layout safety. (Done)
- [x] Verify layout responsiveness and complete successful Svelte 5 static build. (Done)

# Task Checklist - White Glass Gift Capsule Redesign (Elite V2.2)

- [x] Redesign the gift overlay capsule in `OfferCard.svelte` to premium white glassmorphism (`bg-white/75`, `border-white/40`, and glossy light refraction `inset_0_1px_1px_rgba(255,255,255,0.6)`). (Done)
- [x] Adapt contrast for maximum legibility using premium `text-slate-800` title text and deep-rose quantity badge `text-rose-700 bg-rose-500/15`. (Done)
- [x] Clean up blend mode/invert filters from fallback thumbnails on the light background. (Done)


# Task Checklist - Zalo Social Login Ordering & Icon Aesthetic Refinement (Elite V2.2)

- [x] Put Zalo login button before Google button inside `AuthForm.svelte` for priority sign-in experience. (Done)
- [x] Replace the broken Zalo SVG path in `AuthForm.svelte` with the clean, official Zalo wordmark path, scaled and centered perfectly inside the bubble. (Done)
- [x] Verify Svelte 5 static build status and ensure no compilation warnings or errors in the modified file. (Done - built successfully)


# Task Checklist - Google Tag Manager (GTM) Integration (Elite V2.2)

- [x] Add formal database/API support for `google_tag_manager_id` inside `SeoAnalytics` pydantic schema in the backend. (Done)
- [x] Implement robust, non-blocking asynchronous GTM loader with session caching inside `app.html`. (Done)
- [x] Support multiple setting fields dynamically (`google_tag_manager_id`, `gtm_id`, and standard GA ID fallback). (Done)



