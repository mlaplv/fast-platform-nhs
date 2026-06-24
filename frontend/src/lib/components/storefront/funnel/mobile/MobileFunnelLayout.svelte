<script lang="ts">
  import { onMount } from 'svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import type { Product } from '$lib/types';
  import MobileActionStack from './MobileActionStack.svelte';

  // Dedicated Mobile Sections
  import MobileVideoBanner from './sections/MobileVideoBanner.svelte';
  import MobileHero from './sections/MobileHero.svelte';
  // Lazy-load heavy modal components (reduce mobile initial bundle)
  import type { Component } from 'svelte';
  let ScannerHUDComponent = $state<Component<Record<string, unknown>> | null>(null);
  let MobileVerificationCenterComponent = $state<Component<Record<string, unknown>> | null>(null);
  let MobileProductDetailsModalComponent = $state<Component | null>(null);
  let BottomSheetComponent = $state<Component | null>(null);
  let loadJIT = $state(false);
  async function loadScannerHUD() {
    if (!ScannerHUDComponent) {
      const mod = await import('../../product-detail/shared/ScannerHUD.svelte');
      ScannerHUDComponent = mod.default as Component<Record<string, unknown>>;
    }
  }
  async function loadMobileVerificationCenter() {
    if (!MobileVerificationCenterComponent) {
      const mod = await import('../../product-detail/shared/MobileVerificationCenter.svelte');
      MobileVerificationCenterComponent = mod.default as Component<Record<string, unknown>>;
    }
    if (!BottomSheetComponent) {
      const mod = await import('./BottomSheet.svelte');
      BottomSheetComponent = mod.default as Component;
    }
  }

  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';

  import './mobile.css';

  const shopStore = getShopStore();

  // ⚡ Elite V2.2: $props() MUST be declared before any $derived that references props
  let { product: propProduct, reviewStats, reviews = [], relatedProducts = [], resolvedLcpUrl }: Props = $props();

  // Elite V2.2: Reactive switching between live data and edited data
  const product = $derived(shopStore.product || propProduct);

  // Active section index tracked via IntersectionObserver (O(1) – no scroll listeners)
  let activeSectionIndex = $state(0);
  let isDetailsModalOpen = $state(false);

  import Diagnostics from './sections/MobileDiagnostics.svelte';
  import Science from './sections/MobileScience.svelte';
  import Reviews from './sections/MobileReviews.svelte';
  import Offer from './sections/MobileOffer.svelte';

  async function openDetailsModal() {
    if (!MobileProductDetailsModalComponent) {
      const mod = await import('./MobileProductDetailsModal.svelte');
      MobileProductDetailsModalComponent = mod.default;
    }
    isDetailsModalOpen = true;
  }

  let isScanning = $state(false);
  let showVerification = $state(false);
  let verificationData: Record<string, unknown> | null = $state(null);

  async function triggerScan() {
    await loadScannerHUD();
    isScanning = true;
    showVerification = false;
  }

  async function handleScanComplete(event: { verificationData: Record<string, unknown> }) {
    isScanning = false;
    verificationData = event.verificationData;
    await loadMobileVerificationCenter();
    showVerification = true;
  }


  interface Props {
    product: Product;
    reviewStats?: Record<string, unknown>;
    reviews?: Record<string, unknown>[];
    relatedProducts?: Product[];
    resolvedLcpUrl?: string;
  }
  // NOTE: $props() moved above — must precede $derived(propProduct)

  // Check mobile_video_url, video_url (admin field), and hero_video_url (desktop fallback) for compatibility
  const hasVideo = $derived(
    !!(product?.metadata?.mobile_video_url || product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video)
  );

  const isTikTokVideo = $derived.by((): boolean => {
    const url = product?.metadata?.mobile_video_url || product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video || '';
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

    let jitObserver: IntersectionObserver | null = null;
    const jitTimer = setTimeout(() => {
      jitObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            loadJIT = true;
            jitObserver?.disconnect();
          }
        });
      }, { rootMargin: '150px', threshold: 0.01 });

      const jitTrigger = document.getElementById('mobile-jit-trigger');
      if (jitTrigger) jitObserver.observe(jitTrigger);
    }, 1200);

    sections.forEach((el, idx) => {
      el.dataset.sectionIdx = String(idx);
      observer.observe(el);
    });

    return () => {
      observer.disconnect();
      clearTimeout(jitTimer);
      jitObserver?.disconnect();
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
    onOpenDetails={openDetailsModal}
    onChat={() => supportAgent.toggle()}
    onVerify={triggerScan}
  />
  {#if hasVideo}
    <section id="video-banner" class="mobile-snap-section video-section" data-section-idx="0">
      <MobileVideoBanner {product} posterUrl={resolvedLcpUrl} />
    </section>
  {/if}

  <!-- SECTION 1 (or 0 if no video): NATIVE HERO (variant slider) -->
  <section id="hero" class="mobile-snap-section" data-section-idx={hasVideo ? 1 : 0}>
    <MobileHero {product} {resolvedLcpUrl} />
  </section>

  <div id="mobile-jit-trigger"></div>

  <!-- SECTION 2: NATIVE DIAGNOSTICS -->
  <section id="diagnostics" class="mobile-snap-section" data-section-idx={hasVideo ? 2 : 1}>
    <Diagnostics {product} />
  </section>

  <!-- SECTION 3: NATIVE SCIENCE -->
  <section id="science" class="mobile-snap-section" data-section-idx={hasVideo ? 3 : 2}>
    <Science {product} />
  </section>

  <!-- SECTION 4: NATIVE REVIEWS -->
  <section id="reviews" class="mobile-snap-section" data-section-idx={hasVideo ? 4 : 3}>
    <Reviews {product} initialReviews={reviews} />
  </section>

  <!-- SECTION 5: NATIVE OFFER -->
  <section id="offers" class="mobile-snap-section" data-section-idx={hasVideo ? 5 : 4}>
    <Offer {product} onOpenDetails={openDetailsModal} {relatedProducts} {reviewStats} />
  </section>


  {#if isDetailsModalOpen && MobileProductDetailsModalComponent}
    {@const DetailsModal = MobileProductDetailsModalComponent}
    <DetailsModal bind:active={isDetailsModalOpen} {product} />
  {/if}

  {#if isScanning && ScannerHUDComponent}
    {@const ScannerHUD = ScannerHUDComponent}
    <ScannerHUD barcode={product.metadata?.barcode || product.sku} oncomplete={handleScanComplete} />
  {/if}

  {#if showVerification && BottomSheetComponent}
    {@const BottomSheet = BottomSheetComponent}
    <BottomSheet bind:active={showVerification} title="Verified" fullWidth={true} tight={true} extraStyle="padding-left: 5px !important; padding-right: 5px !important;">
       {#if MobileVerificationCenterComponent}
         {@const VerificationCenter = MobileVerificationCenterComponent}
         <VerificationCenter {product} {verificationData} />
       {/if}
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


