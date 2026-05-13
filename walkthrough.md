# Walkthrough: Fix Diagnostic Layout and Add Swipe Support

## 1. Problem
1. The status labels are jumping down a line due to a CSS conflict between Tailwind's `block` and the custom `inline-block` for Sentence Case.
2. The results slider does not support manual swiping, making it feel "stuck" after autoplay was disabled.

## 2. Solution
- Refine CSS to ensure `sentence-case-target` doesn't override intended layout modes.
- Implement `touchstart` and `touchend` event handlers in `MobileDiagnostics.svelte` to support manual swiping of the results slider.

## 3. Evidence
Fixed diagnostic layout and added swipe interaction in `MobileDiagnostics.svelte`:
- Refined CSS to prevent `sentence-case-target` from overriding Tailwind's `block` class on status labels, fixing the line-jumping issue.
- Implemented `handleTouchStart` and `handleTouchEnd` functions to detect horizontal swipes.
- Attached swipe listeners to the results slider container.
- Now users can manually swipe left or right to switch between "Tổng quan lâm sàng" and "Liệu trình tối ưu" slides.

