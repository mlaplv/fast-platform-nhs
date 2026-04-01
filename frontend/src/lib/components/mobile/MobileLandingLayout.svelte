<script lang="ts">
  import { onMount } from 'svelte';
  import { Music } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import MobileActionStack from './MobileActionStack.svelte';
  import MobileBottomSheet from './MobileBottomSheet.svelte';
  import MobileVariantTabs from './MobileVariantTabs.svelte';

  // Dedicated Mobile Sections
  import MobileVideoBanner from './sections/MobileVideoBanner.svelte';
  import MobileHero from './sections/MobileHero.svelte';
  import MobileDiagnostics from './sections/MobileDiagnostics.svelte';
  import MobileScience from './sections/MobileScience.svelte';
  import MobileReviews from './sections/MobileReviews.svelte';
  import MobileOffer from './sections/MobileOffer.svelte';

  import './mobile.css';

  const shopStore = getShopStore();
  const product = $derived(shopStore.product);

  // Active section index tracked via IntersectionObserver (O(1) – no scroll listeners)
  let activeSectionIndex = $state(0);

  // Variant tabs should be hidden when user is on the video banner (section 0)
  // Check both `video_url` (admin field) and `hero_video_url` (desktop fallback) for compatibility
  const hasVideo = $derived(
    !!(product?.metadata?.video_url || product?.metadata?.hero_video_url)
  );

  const isTikTokVideo = $derived.by(() => {
    const url = (product?.metadata?.video_url || product?.metadata?.hero_video_url || '') as string;
    return url.includes('tiktok.com');
  });

  const isTikTokActive = $derived(activeSectionIndex === 0 && isTikTokVideo);

  const heroIndex = $derived(hasVideo ? 1 : 0);
  const tabsHidden = $derived(activeSectionIndex !== heroIndex);

  // Scroll Reactive Logic
  let isScrollingDown = $state(false);
  let lastScrollTop = 0;

  function handleScroll(e: Event) {
    const container = e.target as HTMLElement;
    const currentScroll = container.scrollTop;
    
    // Threshold to prevent jitter
    if (Math.abs(currentScroll - lastScrollTop) < 10) return;

    isScrollingDown = currentScroll > lastScrollTop;
    lastScrollTop = currentScroll;
  }

  onMount(() => {
    const sections = document.querySelectorAll<HTMLElement>('.mobile-snap-section');
    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const idx = Number((entry.target as HTMLElement).dataset.sectionIdx ?? 0);
            activeSectionIndex = idx;
            break;
          }
        }
      },
      { threshold: 0.6 }
    );

    sections.forEach((el, idx) => {
      el.dataset.sectionIdx = String(idx);
      observer.observe(el);
    });

    return () => observer.disconnect();
  });
</script>

<div class="mobile-snap-container relative h-screen overflow-y-auto" onscroll={handleScroll}>
  <!-- PERSISTENT OVERLAYS -->
  <MobileVariantTabs hidden={tabsHidden} />
  <MobileActionStack 
    {product} 
    {isTikTokActive}
    {isScrollingDown}
    onPurchase={() => shopStore.openCheckout()} 
  />

  <!-- SECTION 0: VIDEO BANNER (conditional – only renders if hero_video_url is set) -->
  {#if hasVideo}
    <section class="mobile-snap-section" data-section-idx="0">
      <MobileVideoBanner {product} />
    </section>
  {/if}

  <!-- SECTION 1 (or 0 if no video): NATIVE HERO (variant slider) -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 1 : 0}>
    <MobileHero {product} />
  </section>

  <!-- SECTION 2: NATIVE DIAGNOSTICS -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 2 : 1}>
    <MobileDiagnostics {product} />
  </section>

  <!-- SECTION 3: NATIVE SCIENCE -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 3 : 2}>
    <MobileScience {product} />
  </section>

  <!-- SECTION 4: NATIVE REVIEWS -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 4 : 3}>
    <MobileReviews {product} />
  </section>

  <!-- SECTION 5: NATIVE OFFER -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 5 : 4}>
    <MobileOffer {product} />
  </section>

  <MobileBottomSheet bind:active={shopStore.isCheckoutOpen} {product} />
</div>

<style lang="postcss">
  /* Override section internal padding for mobile snap */
  :global(.mobile-snap-section section) {
    padding-top: var(--mobile-top-space, 10px) !important;
    padding-bottom: calc(var(--mobile-bottom-space) + 20px + env(safe-area-inset-bottom)) !important;
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
  }

  :global(.mobile-snap-section .section-title) {
    font-size: 2.5rem !important;
    line-height: 1;
  }

  :global(.mobile-snap-section .container) {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
  }
</style>
