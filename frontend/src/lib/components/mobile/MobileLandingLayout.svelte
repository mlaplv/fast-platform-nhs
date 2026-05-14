<script lang="ts">
  import { onMount } from 'svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { Product } from '$lib/types';
  import MobileActionStack from './MobileActionStack.svelte';

  // Dedicated Mobile Sections
  import MobileVideoBanner from './sections/MobileVideoBanner.svelte';
  import MobileHero from './sections/MobileHero.svelte';
  import MobileProductDetailsModal from './MobileProductDetailsModal.svelte';
  import ScannerHUD from '../storefront/product-detail/shared/ScannerHUD.svelte';
  import MobileVerificationCenter from '../storefront/product-detail/shared/MobileVerificationCenter.svelte';
  import BottomSheet from './BottomSheet.svelte';

  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';

  import './mobile.css';

  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  const shopStore = getShopStore();
  const isEditMode = $derived(liveEditStore.isEditMode);

  // Elite V2.2: Reactive switching between live data and edited data
  const product = $derived(isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);

  // Active section index tracked via IntersectionObserver (O(1) – no scroll listeners)
  let activeSectionIndex = $state(0);
  let isDetailsModalOpen = $state(false);
  let loadJIT = $state(false);
  let isScanning = $state(false);
  let showVerification = $state(false);
  let verificationData: Record<string, unknown> | null = $state(null);

  function triggerScan() {
    isScanning = true;
    showVerification = false;
  }

  function handleScanComplete(event: { verificationData: Record<string, unknown> }) {
    isScanning = false;
    verificationData = event.verificationData;
    showVerification = true;
  }

  interface Props {
    product: Product;
    reviewStats?: Record<string, unknown>;
    reviews?: Record<string, unknown>[];
    relatedProducts?: Product[];
  }
  let { reviewStats, reviews = [], relatedProducts = [] }: Props = $props();

  // Check both `video_url` (admin field) and `hero_video_url` (desktop fallback) for compatibility
  const hasVideo = $derived(
    !!(product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video)
  );

  const isTikTokVideo = $derived.by((): boolean => {
    const url = product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video || '';
    return typeof url === 'string' && url.includes('tiktok.com');
  });

  const isTikTokActive = $derived(activeSectionIndex === 0 && isTikTokVideo);

  // 🚀 ELITE MOBILE SCROLL COORDINATOR (O(1) – Non-reactive DOM mutation)
  let isScrollingDown = $state(false);
  let lastScrollTop = 0;
  let scrollTicking = false;

  function handleScroll(e: Event): void {
    if (scrollTicking) return;
    scrollTicking = true;
    
    requestAnimationFrame(() => {
      const container = e.target as HTMLElement;
      if (!container) {
        scrollTicking = false;
        return;
      }
      
      const currentScroll = container.scrollTop;
      const delta = currentScroll - lastScrollTop;
      if (Math.abs(delta) >= 10) {
        const goingDown = delta > 0;
        // Only trigger Svelte reactivity when direction actually changes
        if (goingDown !== isScrollingDown) {
          isScrollingDown = goingDown;
        }
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

<div class="mobile-snap-container relative h-dvh overflow-y-auto" translate="no" onscroll={handleScroll}>
  <!-- PERSISTENT OVERLAYS -->
  <MobileActionStack 
    {product} 
    {isTikTokActive}
    {isScrollingDown}
    onPurchase={() => {
      document.getElementById('offers')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }} 
    onOpenDetails={() => isDetailsModalOpen = true}
    onChat={() => supportAgent.toggle()}
    onVerify={triggerScan}
  />
  {#if hasVideo}
    <section id="video-banner" class="mobile-snap-section video-section" data-section-idx="0">
      <MobileVideoBanner {product} />
    </section>
  {/if}

  <!-- SECTION 1 (or 0 if no video): NATIVE HERO (variant slider) -->
  <section id="hero" class="mobile-snap-section" data-section-idx={hasVideo ? 1 : 0}>
    <MobileHero {product} />
  </section>

  <div id="mobile-jit-trigger"></div>

  <!-- SECTION 2: NATIVE DIAGNOSTICS -->
  <section id="diagnostics" class="mobile-snap-section" data-section-idx={hasVideo ? 2 : 1}>
    {#if loadJIT}
      {#await import('./sections/MobileDiagnostics.svelte') then { default: MobileDiagnostics }}
        <MobileDiagnostics {product} />
      {/await}
    {:else}
      <div class="w-full min-h-[50vh] bg-black animate-pulse"></div>
    {/if}
  </section>

  <!-- SECTION 3: NATIVE SCIENCE -->
  <section id="science" class="mobile-snap-section" data-section-idx={hasVideo ? 3 : 2}>
    {#if loadJIT}
      {#await import('./sections/MobileScience.svelte') then { default: MobileScience }}
        <MobileScience {product} />
      {/await}
    {:else}
      <div class="w-full min-h-[50vh] bg-black animate-pulse"></div>
    {/if}
  </section>

  <!-- SECTION 4: NATIVE REVIEWS -->
  <section id="reviews" class="mobile-snap-section" data-section-idx={hasVideo ? 4 : 3}>
    {#if loadJIT}
      {#await import('./sections/MobileReviews.svelte') then { default: MobileReviews }}
        <MobileReviews {product} initialReviews={reviews} />
      {/await}
    {:else}
      <div class="w-full min-h-[50vh] bg-black animate-pulse"></div>
    {/if}
  </section>

  <!-- SECTION 5: NATIVE OFFER -->
  <section id="offers" class="mobile-snap-section" data-section-idx={hasVideo ? 5 : 4}>
    {#if loadJIT}
      {#await import('./sections/MobileOffer.svelte') then { default: MobileOffer }}
        <MobileOffer {product} onOpenDetails={() => isDetailsModalOpen = true} {relatedProducts} {reviewStats} />
      {/await}
    {:else}
      <div class="w-full min-h-[100vh] bg-black animate-pulse"></div>
    {/if}
  </section>


  <MobileProductDetailsModal bind:active={isDetailsModalOpen} {product} />

  {#if isScanning}
    <ScannerHUD barcode={product.metadata?.barcode || product.sku} oncomplete={handleScanComplete} />
  {/if}

  {#if showVerification}
    <BottomSheet bind:active={showVerification} title="Verified" fullWidth={true} tight={true} extraStyle="padding-left: 5px !important; padding-right: 5px !important;">
       <MobileVerificationCenter {product} {verificationData} />
    </BottomSheet>
  {/if}

  <!-- 🔍 SEO INTERNAL LINKING (Google Sitelinks Support) -->
  <nav class="sr-only" aria-label="Nội dung chính">
    <ul>
      <li><a href="#hero">Đầu trang</a></li>
      <li><a href="#diagnostics">Chẩn đoán da liễu</a></li>
      <li><a href="#science">Cơ chế khoa học</a></li>
      <li><a href="#reviews">Đánh giá khách hàng</a></li>
      <li><a href="#offers">Ưu đãi mua hàng</a></li>
    </ul>
  </nav>
</div>


