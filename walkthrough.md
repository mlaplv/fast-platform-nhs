# Walkthrough: Resolving Hardcoded Fake Discount UI

## 1. Diagnostics & Root Cause
- **Problem:** The storefront UI was displaying an artificially inflated original price (`930.000₫`) next to a fake discount ("Tiết kiệm 330.000₫") for a product that was priced at `600.000₫` with no discount in the Admin database.
- **Cause:** Discovered hardcoded `* 1.55` fallback logic in `Desktop.svelte` derived values. This mocked a 55% markup when `product.discountPrice` was falsey.

## 2. Hardcode Elimination
- **Action:** Removed `* 1.55` logic from `productInfo.originalPrice` and `activePrices.original` derivations in both `MainDetail/Desktop.svelte` and `LandingPage/Desktop.svelte`.
- **Result:** `originalPrice` now accurately mirrors `salePrice` when no discount is active.

## 3. UI Conditional Rendering
- **Action:** Updated `Info.svelte` in both `MainDetail` and `LandingPage` directories. Wrapped the crossed-out `<span class="original-price">` inside the `#if activePrices.original > activePrices.sale` block.
- **Result:** The original price line and the "Tiết kiệm" badge disappear entirely if no authentic discount is supplied from the backend, aligning with the strict Anti-Mock Data Protocol (Rule R00).

## 4. Product List "0đ" Price Resolution
- **Problem:** In category lists, search results, and product grids, the price was displayed as `0đ` when the discount price was manually set to `0` in the admin.
- **Cause:** The frontend code used the nullish coalescing operator `??` (`p.discountPrice ?? p.price`). Since `0` is neither `null` nor `undefined`, it bypassed the fallback and rendered exactly `0đ`.
- **Action:** Replaced `??` with `||` across all storefront components (`ProductGrid.svelte`, `ProductListDesktop.svelte`, `SmartSearchDesktop.svelte`, `CartMiniHover.svelte`, etc.). The logical OR `||` correctly treats `0` as falsy and falls back to the original `price`.

## 5. Cart/Checkout String "0" Bypass Resolution
- **Problem:** Despite replacing `??` with `||`, the cart and checkout pages still evaluated `discountPrice` to `0` and effectively calculated `0đ` as the item price.
- **Cause:** The backend API or local storage payload sometimes serializes the `0` input as a string `"0"`. In JavaScript, the non-empty string `"0"` is truthy, which bypasses the `||` operator fallback entirely.
- **Action:** Systematically wrapped all pricing variable evaluations with `Number()` coercion (e.g., `Number(p.discountPrice) || Number(p.price)`). This ensures string `"0"` is converted to the number `0` (which is falsy), triggering the correct fallback logic in both `CartStore` and all checkout UI components.
