# Task: Resolving Hardcoded Fake Discount UI

- [x] Identify root cause of `930.000₫` fake price displaying when original price is `600.000₫`.
- [x] Remove `* 1.55` hardcoded mock data from `MainDetail/Desktop.svelte`.
- [x] Remove `* 1.55` hardcoded mock data from `LandingPage/Desktop.svelte`.
- [x] Conditionally hide the original crossed-out price layout when there is no active discount in `MainDetail/modules/Info.svelte`.
- [x] Conditionally hide the original crossed-out price layout when there is no active discount in `LandingPage/modules/Info.svelte`.
- [x] Fix `0đ` price displaying in product category lists and grids due to `??` nullish coalescing operator treating `0` as a valid price.
- [x] Fix `0đ` price displaying in checkout and cart logic due to `"0"` string bypass of `||` logical OR operator.
