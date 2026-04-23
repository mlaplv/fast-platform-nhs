<script lang="ts">
  import { onMount } from 'svelte';
  import { Music } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import MobileActionStack from './MobileActionStack.svelte';
  import MobileVariantTabs from './MobileVariantTabs.svelte';

  // Dedicated Mobile Sections
  import MobileVideoBanner from './sections/MobileVideoBanner.svelte';
  import MobileHero from './sections/MobileHero.svelte';
  import MobileProductDetailsModal from './MobileProductDetailsModal.svelte';

  // Support Agent
  import SupportChatMobile from '$lib/components/client/support/SupportChatMobile.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';

  import './mobile.css';

  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  const shopStore = getShopStore();
  const isEditMode = $derived(liveEditStore.isEditMode);

  // Elite V2.2: Reactive switching between live data and edited data
  const product = $derived(isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);

  // ── SEO Derived State (Elite V2.2 – Mobile Parity) ──────────────────────────
  const seoMeta = $derived(product?.seoMeta ?? product?.seo_meta ?? null);
  const siteName = $derived(product?.metadata?.seo_site_name ?? 'Elite Storefront');
  const ogImage = $derived(product?.images?.[0] ?? '');

  // Active section index tracked via IntersectionObserver (O(1) – no scroll listeners)
  let activeSectionIndex = $state(0);
  let isDetailsModalOpen = $state(false);
  let loadJIT = $state(false);

  // Variant tabs should be hidden when user is on the video banner (section 0)
  // Check both `video_url` (admin field) and `hero_video_url` (desktop fallback) for compatibility
  const hasVideo = $derived(
    !!(product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video)
  );

  const isTikTokVideo = $derived.by((): boolean => {
    const url = product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video || '';
    return typeof url === 'string' && url.includes('tiktok.com');
  });

  const isTikTokActive = $derived(activeSectionIndex === 0 && isTikTokVideo);

  const heroIndex = $derived(hasVideo ? 1 : 0);
  const tabsHidden = $derived(activeSectionIndex !== heroIndex);

  // 🚀 ELITE MOBILE SCROLL COORDINATOR (O(1))
  let isScrollingDown = $state(false);
  let lastScrollTop = 0;
  let scrollTicking = false;

  function handleScroll(e: Event): void {
    if (scrollTicking) return;
    scrollTicking = true;
    
    requestAnimationFrame(() => {
      const container = e.target as HTMLElement;
      if (!container) return;
      
      const currentScroll = container.scrollTop;
      if (Math.abs(currentScroll - lastScrollTop) >= 10) {
        isScrollingDown = currentScroll > lastScrollTop;
        lastScrollTop = currentScroll;
      }
      scrollTicking = false;
    });
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

    const jitObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          loadJIT = true;
          jitObserver.disconnect();
        }
      });
    }, { rootMargin: '600px', threshold: 0.01 });

    const jitTrigger = document.getElementById('mobile-jit-trigger');
    if (jitTrigger) jitObserver.observe(jitTrigger);

    sections.forEach((el, idx) => {
      el.dataset.sectionIdx = String(idx);
      observer.observe(el);
    });

    return () => {
      observer.disconnect();
      jitObserver.disconnect();
    };
  });
</script>

<div class="mobile-snap-container relative h-screen overflow-y-auto" onscroll={handleScroll}>
  <!-- PERSISTENT OVERLAYS -->
  <MobileVariantTabs hidden={tabsHidden} />
  <MobileActionStack 
    {product} 
    {isTikTokActive}
    {isScrollingDown}
    onPurchase={() => {
      document.getElementById('offer-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }} 
    onOpenDetails={() => isDetailsModalOpen = true}
    onChat={() => supportAgent.toggle()}
  />
  {#if hasVideo}
    <section class="mobile-snap-section video-section" data-section-idx="0">
      <MobileVideoBanner {product} />
    </section>
  {/if}

  <!-- SECTION 1 (or 0 if no video): NATIVE HERO (variant slider) -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 1 : 0}>
    <MobileHero {product} />
  </section>

  <div id="mobile-jit-trigger"></div>

  <!-- SECTION 2: NATIVE DIAGNOSTICS -->
  <section id="diagnostics-section" class="mobile-snap-section" data-section-idx={hasVideo ? 2 : 1}>
    {#if loadJIT}
      {#await import('./sections/MobileDiagnostics.svelte') then { default: MobileDiagnostics }}
        <MobileDiagnostics {product} />
      {/await}
    {:else}
      <div class="w-full min-h-[50vh] bg-black animate-pulse"></div>
    {/if}
  </section>

  <!-- SECTION 3: NATIVE SCIENCE -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 3 : 2}>
    {#if loadJIT}
      {#await import('./sections/MobileScience.svelte') then { default: MobileScience }}
        <MobileScience {product} />
      {/await}
    {:else}
      <div class="w-full min-h-[50vh] bg-black animate-pulse"></div>
    {/if}
  </section>

  <!-- SECTION 4: NATIVE REVIEWS -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 4 : 3}>
    {#if loadJIT}
      {#await import('./sections/MobileReviews.svelte') then { default: MobileReviews }}
        <MobileReviews {product} />
      {/await}
    {:else}
      <div class="w-full min-h-[50vh] bg-black animate-pulse"></div>
    {/if}
  </section>

  <!-- SECTION 5: NATIVE OFFER -->
  <section id="offer-section" class="mobile-snap-section" data-section-idx={hasVideo ? 5 : 4}>
    {#if loadJIT}
      {#await import('./sections/MobileOffer.svelte') then { default: MobileOffer }}
        <MobileOffer {product} />
      {/await}
    {:else}
      <div class="w-full min-h-[100vh] bg-black animate-pulse"></div>
    {/if}
  </section>


  <MobileProductDetailsModal bind:active={isDetailsModalOpen} {product} />
</div>
