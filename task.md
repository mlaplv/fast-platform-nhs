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
