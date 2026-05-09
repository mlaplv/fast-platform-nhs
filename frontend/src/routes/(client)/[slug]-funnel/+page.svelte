<script lang="ts">
  import '../client.css';
  import { onMount } from 'svelte';
  import { setShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import HeroBanner from '$lib/components/client/HeroBanner.svelte';
  import LiquidHeader from '$lib/components/client/LiquidHeader.svelte';
  import { browser } from '$app/environment';
  import type { Action } from 'svelte/action';
  
  // JIT Component Flags
  let loadJIT = $state(false);
  
  import MobileLandingLayout from '$lib/components/mobile/MobileLandingLayout.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  
  import type { PageData } from './$types';
  
  // Admin Live Editor (Elite V2.2)
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { permissionState } from '$lib/state/permissions.svelte';

  let { data }: { data: PageData } = $props();
  let themeMode = $state<'system' | 'light' | 'dark'>('system');

  // 🚀 ELITE CONTEXT INJECTION (Elite V2.2)
  const shopStore = setShopStore();

  // Protection & Derived State
  const product = $derived(data?.product);
  const metadata = $derived(product?.metadata || {});
  const seoMeta = $derived(product?.seoMeta || product?.seo_meta || null);
  const isMobile = $derived(data?.isMobile || false);

  const loadingText = $derived(metadata.sync_loading_text || 'SYNCHRONIZING ELITE ASSETS...');
  const siteName = $derived(metadata.seo_site_name || 'osmo Elite');

  // Elite Smart-Adaptive: Reactive Layout Switching
  const clientUi = getClientUi();
  const useMobileLayout = $derived(clientUi?.isHydrated ? clientUi.isMobile : isMobile);

  // 🚀 QUANTUM SYNC (Elite V2.2 Protocol)
  // Inline init ensures SSR stability; Guarded initialization for client-side
  let isInitialized = false;
  
  if (product?.id && !isInitialized) {
    shopStore.init(product);
    if (data.unlockedVoucherIds) {
      shopStore.setUnlockedVouchers(data.unlockedVoucherIds);
    }
    isInitialized = true;
  }

  const updateDOM = (theme: 'light' | 'dark'): void => {
    if (!browser) return;
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
  };

  const applyTheme = (mode: 'system' | 'light' | 'dark') => {
    themeMode = mode;
    if (!browser) return;
    localStorage.setItem('hero-theme-mode', mode);
    if (mode === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      updateDOM(isDark ? 'dark' : 'light');
    } else {
      updateDOM(mode as 'light' | 'dark');
    }
  };

  // Shop Settings Sync (Elite V2.2)
  $effect.pre(() => {
    if (clientUi) {
      // Inject global shop settings into the UI state for sub-components (OfferGrid, etc.)
      if (data.shopInfo) {
        clientUi.settings = data.shopInfo;
      }
    }
  });

  // 🚀 ELITE QUANTUM COORDINATOR (Elite V2.2)
  onMount(() => {
    if (!browser) return;

    const savedTheme = localStorage.getItem('hero-theme-mode');
    applyTheme((savedTheme === 'light' || savedTheme === 'dark' || savedTheme === 'system') ? savedTheme : 'system');
      
    if (product) {
      liveEditStore.init(product);
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('live_edit') === 'true') {
        if (permissionState.hasRole('SUPER_ADMIN') || permissionState.hasRole('ADMIN')) {
          liveEditStore.isEditMode = true;
        } else {
          window.location.replace(window.location.origin + window.location.pathname);
        }
      }
    }
      
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const h = (e: MediaQueryListEvent): void => {
      if (themeMode === 'system') updateDOM(e.matches ? 'dark' : 'light');
    };
    mq.addEventListener('change', h);

    // JIT ASSET LOADER (Elite V2.2 Protocol) - FIRE EARLY
    const jitObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          loadJIT = true;
          jitObserver.disconnect();
        }
      });
    }, { rootMargin: '1200px', threshold: 0.01 });

    // SESSION COORDINATOR (Elite V2.2 HUD Sync) - FIRE AT CENTER
    const sessionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !isWheelLocked) {
          const idx = sectionIds.indexOf(entry.target.id);
          if (idx !== -1) currentSessionIdx = idx;
        }
      });
    }, {
      rootMargin: '-50% 0px -50% 0px',
      threshold: 0
    });

    // Register Assets
    const trigger = document.getElementById('jit-trigger');
    if (trigger) jitObserver.observe(trigger);

    sectionIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) sessionObserver.observe(el);
    });

    const cleanupObservers = clientUi.initObservers();

    return () => {
      shopStore.dispose();
      mq.removeEventListener('change', h);
      jitObserver.disconnect();
      sessionObserver.disconnect();
      if (cleanupObservers) cleanupObservers();
    };
  });

  const scrollToQuiz = () => {
    const el = document.getElementById('diagnostics');
    if (el) {
      currentSessionIdx = 1; // Sync programmatic tracker
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Elite 2026 Programmatic Scroll Coordinator (O(1) Speed/Memory)
  const hasQuiz = $derived((metadata?.quiz_questions?.length || 0) > 0);
  const sectionIds = $derived(hasQuiz 
    ? ['hero', 'diagnostics', 'science', 'reviews', 'offers']
    : ['hero', 'science', 'reviews', 'offers']
  );
  let currentSessionIdx = $state(0);
  const activeId = $derived(sectionIds[currentSessionIdx]);
  let isWheelLocked = false;

  const onWheelObserver = (e: WheelEvent) => {
    // Escape limiters: Mobile layout, Server, or interacting with Checkout
    if (useMobileLayout || !browser) return;

    // Viral 2026: Neural Activity Interception? (Optional)
    const target = e.target as HTMLElement;

    // Elite V2.2 Escape: Don't hijack scroll if we are in Edit Mode and hovering over an editor
    if (liveEditStore.isEditMode && (target?.closest('.edit-mode-container') || target?.closest('.editor-box'))) return;
    
    // Ignore micro-scrolls (e.g., trackpad resting)
    if (Math.abs(e.deltaY) < 15) return;
    
    // 100% Native Intercept - Bypass default DOM scrolling
    e.preventDefault();
    if (isWheelLocked) return;

    const direction = e.deltaY > 0 ? 1 : -1;
    let nextIdx = currentSessionIdx + direction;

    // Clamp boundaries
    if (nextIdx >= 0 && nextIdx < sectionIds.length) {
      isWheelLocked = true;
      currentSessionIdx = nextIdx;
      
      // O(1) Native C++ lookup
      const target = document.getElementById(sectionIds[currentSessionIdx]);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }

      // Memory-efficient cooling lock to prevent scroll-looping (450ms for ultra-fast snap)
      setTimeout(() => {
        isWheelLocked = false;
      }, 450);
    }
  };

  // Svelte 5 Native Action: Forced non-passive listener
  const initScrollObserver: Action<HTMLElement> = (node) => {
    node.addEventListener('wheel', onWheelObserver, { passive: false });
    return {
      destroy() {
        node.removeEventListener('wheel', onWheelObserver);
      }
    };
  };

  // ── SITE NAVIGATION LD (Google Sitelinks Support) ──────────────────────────
  const siteNavigationLd = $derived.by(() => {
    const sections = [
      { name: 'Đầu trang', url: '#hero' },
      { name: 'Chẩn đoán AI', url: '#diagnostics' },
      { name: 'Cơ chế Khoa học', url: '#science' },
      { name: 'Đánh giá thực tế', url: '#reviews' },
      { name: 'Ưu đãi Đặc biệt', url: '#offers' }
    ];
    
    return JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      "name": "Mục lục nội dung",
      "itemListElement": sections.map((s, i) => ({
        "@type": "ListItem",
        "position": i + 1,
        "name": s.name,
        "url": s.url
      }))
    });
  });
</script>

{#if seoMeta}
  <SeoHead
    pageType="product"
    title={seoMeta.title.split('|')[0].trim()}
    description={seoMeta.description}
    keywords={seoMeta.keywords}
    canonical={seoMeta.canonical_url}
    ogType="product"
    ogImage={product?.images?.[0] || ""}
    ogImageAlt={seoMeta.title}
    siteName={siteName}
    productData={{
      name: (product?.name || seoMeta.title).replace(/40gr/g, '40g'),
      images: product?.images,
      description: seoMeta.description,
      brand: metadata?.brand || "osmo",
      sku: product?.sku || "OSMO-LP",
      price: product?.price || 0,
      currency: "VND",
      availability: product?.stock_status === 'OUT_OF_STOCK' ? 'OutOfStock' : 'InStock',
      ratingValue: 4.9,
      reviewCount: 24
    }}
    jsonLdScripts={[
      seoMeta.json_ld_string,
      seoMeta.breadcrumb_ld_string,
      seoMeta.faq_ld_string,
      siteNavigationLd
    ]}
  />
{:else}
  <SeoHead
    pageType="product"
    title={(product?.name || 'Loading...').split('|')[0].trim()}
    description={metadata?.short_description || product?.name || ""}
    canonical=""
    siteName={siteName}
    ogType="product"
    image={product?.images?.[0] || ""}
    productData={{
      name: (product?.name || "").replace(/40gr/g, '40g'),
      images: product?.images,
      description: metadata?.short_description || "",
      brand: metadata?.brand || "osmo",
      price: product?.price || 0,
      ratingValue: 4.9,
      reviewCount: 24
    }}
  />
{/if}

{#if useMobileLayout}
  {#if product}
    <MobileLandingLayout 
      {product} 
      reviewStats={data.reviewStats} 
      reviews={data.reviews} 
      relatedProducts={data.relatedProducts} 
    />
  {/if}
{:else}
  <div class="client-page-root selection:bg-blue-600 selection:text-white h-screen overflow-y-scroll" translate="no" use:initScrollObserver>

  {#if product?.id}
    <LiquidHeader {product} {themeMode} {applyTheme} scrollToQuiz={scrollToQuiz} {activeId} />
    <HeroBanner {scrollToQuiz} />

    <!-- SECTIONS WITH INDEPENDENT JIT LOADING (Elite V2.2 Optimization) -->
    <!-- This preserves snap points while components are loading -->
    
    <div id="jit-trigger"></div>

    {#if hasQuiz}
      <section id="diagnostics" class="snap-session">
        {#if loadJIT}
          {#await import('$lib/components/client/slug/DiagnosticsSection.svelte') then { default: DiagnosticsSection }}
            <DiagnosticsSection {product} />
          {/await}
        {:else}
          <div class="w-full h-full bg-[#010101] animate-pulse rounded-t-3xl border-t border-[#111]"></div>
        {/if}
      </section>
    {/if}

    <section id="science" class="snap-session">
      {#if loadJIT}
        {#await import('$lib/components/client/slug/ScienceBento.svelte') then { default: ScienceBento }}
          <ScienceBento />
        {/await}
      {:else}
        <div class="w-full h-full bg-[#010101] animate-pulse"></div>
      {/if}
    </section>


    <section id="reviews" class="snap-session">
      {#if loadJIT}
        {#await import('$lib/components/client/slug/VerifiedReviews.svelte') then { default: VerifiedReviews }}
          <VerifiedReviews initialReviews={data.reviews} />
        {/await}
      {:else}
        <div class="w-full h-full bg-[#010101] animate-pulse"></div>
      {/if}
    </section>

    <section id="offers" class="snap-session">
      {#if loadJIT}
        {#await import('$lib/components/client/slug/OfferGrid.svelte') then { default: OfferGrid }}
          <OfferGrid />
        {/await}
      {:else}
        <div class="w-full h-full bg-[#010101] animate-pulse"></div>
      {/if}
    </section>


  {:else}
    <div class="flex flex-col items-center justify-center min-h-screen bg-[#050505] text-white">
       <div class="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
       <p class="text-sm tracking-[0.2em] font-light animate-pulse text-blue-400">{loadingText}</p>
    </div>
  {/if}
  </div>
{/if}

<!-- Administrative HUD (Elite V2.2 Overlay Layer - Severely Protected) -->
{#if liveEditStore.isAdmin}
  {#await import('$lib/components/admin/AdminActionBar.svelte') then { default: AdminActionBar }}
    <AdminActionBar />
  {/await}
  {#await import('$lib/components/admin/LiveEditorOverlay.svelte') then { default: LiveEditorOverlay }}
    <LiveEditorOverlay />
  {/await}
  {#await import('$lib/components/admin/LiveEditNotification.svelte') then { default: LiveEditNotification }}
    <LiveEditNotification />
  {/await}
{/if}

<style lang="postcss">
  .client-page-root {
    antialiased: true;
    overflow-x: hidden;
    height: 100vh;
    font-family: 'Be Vietnam Pro', 'Inter', sans-serif;
    background-color: #010101; /* Viral 2026: Luxury Black foundation */
    color: var(--text-base);
  }

  :root {
    --z-sticky-header: 100;
  }

  :global(.snap-session) {
    min-height: 100dvh;
    height: auto;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
    transform: translateZ(0); /* Hardware Acceleration */
    will-change: transform;
  }

  /* ELITE V2.2: Final section isolation - no forced min-height to prevent gaps */
  #offers.snap-session {
    min-height: auto;
  }

  /* Ensure smooth transitions inside snap sessions */
  :global(section) {
    transition: opacity 0.8s ease;
  }
</style>
