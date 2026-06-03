# Walkthrough: Fixing "Xem thêm phân nhóm" Overlap on Mobile

## 1. Issue Analysis
The user reported an issue where the "Xem thêm phân nhóm" (View more sub-categories) text at the bottom of the Mobile product ingredients section was overlapping with the underlying content text (e.g. ingredient tags). 
The overlapping was caused because the button containing the text had a `max-height` (180px) and `overflow-hidden`. As the flex content exceeded this height, it bled into the padding area at the bottom of the button. The "Xem thêm" text was absolutely positioned at the bottom using a semi-transparent gradient (`from-gray-50/95`), which allowed the underlying white ingredient tags to shine through, ruining readability.

## 2. Technical Fixes
File: `frontend/src/lib/components/storefront/product-detail/MainDetail/modules/ProductMobileSpecs.svelte`
- Upgraded the bottom fade gradient from `from-gray-50/95` (which was partially transparent near the text) to `from-gray-50 from-50%`. This ensures that the bottom 50% of the gradient is entirely solid (`#f9fafb`), completely masking the underlying overflow content.
- Increased the absolute gradient container height from `h-12` (48px) to `h-14` (56px) for more coverage.
- Adjusted the positioning of the "Xem thêm" text. Changed `pb-1` to `pb-0` and added `mb-1.5` along with `text-gray-500` to lower the text slightly, pushing it away from the content bounds and achieving a cleaner look.
- Applied the same visual and layout fix for both the `ingredients_groups` branch and the plain `ingredients` string branch.

## 3. Verification & Deployment
- The structural CSS changes ensure that no matter how long the ingredient list is, the "View more" text always rests on a solid background and cannot be overlapped by white tags.
- Pending execution of `rsync` to synchronize the changes to the production VPS `mlap@103.1.236.14`.
