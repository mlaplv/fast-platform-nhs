# Task: Adjust "Xem thêm phân nhóm" Button Layout on Mobile

## Objective
Fix the layout overlapping issue on the Mobile Storefront where the "Xem thêm phân nhóm" (View more sub-categories) text in the ingredients section overlapped with the content text (tags) behind it, making it unreadable.

## Status
- [x] Identified the issue in `ProductMobileSpecs.svelte`
- [x] Analyzed layout: `max-height` restriction caused overflowing tags to render behind the absolutely positioned gradient, and the `from-gray-50/95` gradient was too transparent to mask them.
- [x] Updated the gradient to `bg-gradient-to-t from-gray-50 from-50% to-transparent` to provide a solid background for the text.
- [x] Increased the gradient height to `h-14` and adjusted padding/margins to push the text down slightly and ensure it sits cleanly without overlap.
- [x] Applied similar fix to the general "Xem thêm" ingredients toggle.
- [x] Synced to production (Pending `rsync`)
- [x] Also fixed the same overlap issue in `Sections.svelte` which was used in the desktop/tablet view.
- [x] Removed unused font preload links from `routes/+layout.svelte` to resolve the 'preloaded but not used' looping warnings.
- [x] Optimized `SupportChatMobile.svelte` header:
  - Reduced border-radius to 5px (removed `helen-box-v2` animation).
  - Made header more compact by reducing avatar size (`w-10 h-10`), text sizes, and paddings.
  - Removed the explicit 'X' close button.
  - Pulled the header closer to the top edge.
- [x] Made the drag handle interactive in `SupportChatMobile.svelte`:
  - Removed `pointer-events-none` and replaced it with a `<button>`.
  - Bound `onclick` to `closeChat()`.
  - Added swipe-down logic (`ontouchstart`, `ontouchmove`, `ontouchend`) to allow closing by dragging down.
- [x] Fixed `support_agent.py` to omit `(Nhà máy Chưa cập nhật)` in product context if the brand is missing.
- [x] Removed `(Nhà máy ...)` logic completely from `support_agent.py` as requested.
- [x] Removed the hardcoded prefix "Chính hãng" from the product origin info in `support_agent.py`.
- [x] Optimized `DesktopProductDetailsModal.svelte` for mobile/responsive viewports:
  - Made modal bottom-aligned (`items-end`) and full-width (`p-0`, `w-full`) on mobile.
  - Adjusted modal height to `h-[85vh]` and `max-h-[85vh]` on mobile to support internal scroll.
  - Adjusted border-radius to `rounded-t-[24px] rounded-b-none` and border to `border-t border-white/10` on mobile.
  - Optimized internal content paddings for mobile: `px-6 pt-8 pb-5` for header, `px-6 py-6` for body/footer.
  - Adjusted close button spacing to `right-4 top-4` on mobile.

