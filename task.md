# Task: Optimize LCP Image Discoverability

## Objective
Optimize LCP (Largest Contentful Paint) by making the main product image discoverable immediately from the HTML, avoiding lazy-loading, and using `fetchpriority="high"`.

## Checklist
- [x] Analyze `[slug]/+page.svelte` to remove `loading="eager"` from the SSR hero image.
- [x] Analyze `[slug]/+page.svelte` to add `type="image/webp"` to the LCP `<link rel="preload">` tag.
- [x] Update `ProductMobileMedia.svelte` to remove `loading="lazy"` (set to undefined) for the first image (`i === 0`) while keeping it for others.
- [x] Update `Gallery.svelte` (desktop) to remove `loading="eager"` from the main product image.
- [x] Update `Desktop.svelte` to remove `loading="lazy"` from the verified badge that appears above the fold.
- [ ] Sync changes to VPS upon user approval.
