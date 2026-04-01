<script lang="ts">
  import { onMount } from 'svelte';
  import { setShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import HeroBanner from '$lib/components/client/HeroBanner.svelte';
  import LiquidHeader from '$lib/components/client/LiquidHeader.svelte';
  import StealthCheckout from '$lib/components/client/StealthCheckout.svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client.ts';
  import { browser } from '$app/environment';
  
  // JIT Component Flags
  let loadJIT = $state(false);
  
  import MobileLandingLayout from '$lib/components/mobile/MobileLandingLayout.svelte';
  
  import type { PageData } from './$types';

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
  const siteName = $derived(metadata.seo_site_name || 'Elite Storefront');

  // Elite Smart-Adaptive: Reactive Layout Switching
  const clientUi = getClientUi();
  const useMobileLayout = $derived(clientUi?.isHydrated ? clientUi.isMobile : isMobile);

  // Quantum Sync: Init store immediately for SSR stability
  if (product?.id) {
     shopStore.init(product);
  }

  $effect.pre(() => {
    if (product?.id) {
       shopStore.init(product);
    }
  });

  // Removed duplicate getClientUi call

  const updateDOM = (theme: 'light' | 'dark') => {
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

  // Footer Control!
  $effect(() => {
    if (clientUi) {
      clientUi.isFooterHidden = useMobileLayout;
    }
    return () => { 
      if (clientUi) clientUi.isFooterHidden = false; 
    };
  });

  // Cleanup Timer on unmount
  onMount(() => {
    if (browser) {
      const savedTheme = localStorage.getItem('hero-theme-mode');
      const validTheme = (savedTheme === 'light' || savedTheme === 'dark' || savedTheme === 'system') ? savedTheme : 'system';
      applyTheme(validTheme);
      
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const h = (e: MediaQueryListEvent): void => {
        if (themeMode === 'system') updateDOM(e.matches ? 'dark' : 'light');
      };
      
      mq.addEventListener('change', h);

      // JIT Intersection Observer
      const jitObserver = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          loadJIT = true;
          jitObserver.disconnect();
        }
      }, { rootMargin: '400px' });
      
      const trigger = document.getElementById('jit-trigger');
      if (trigger) jitObserver.observe(trigger);

      // Elite Smart-Adaptive Init
      const cleanupObservers = clientUi.initObservers();
      
      return () => {
        shopStore.dispose();
        mq.removeEventListener('change', h);
        jitObserver.disconnect();
        if (cleanupObservers) cleanupObservers();
      };
    }
  });

  const scrollToQuiz = () => {
    const el = document.getElementById('diagnostics');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };
</script>

<svelte:head>
  {#if seoMeta}
    <title>{seoMeta.title} | {siteName}</title>
    <meta name="description" content={seoMeta.description} />
    <meta name="keywords" content={seoMeta.keywords} />
    <link rel="canonical" href={seoMeta.canonical_url} />
    {#if seoMeta.json_ld_string}
      <!-- eslint-disable-next-line svelte/no-at-html-tags -->
      {@html `<script type="application/ld+json">${seoMeta.json_ld_string}</script>`}
    {/if}
  {:else}
    <title>{product?.name || 'Loading...'} | {siteName}</title>
  {/if}
</svelte:head>

{#if useMobileLayout}
  {#if product}
    <MobileLandingLayout {product} />
  {/if}
{:else}
  <div class="client-page-root selection:bg-blue-600 selection:text-white h-screen overflow-y-scroll scroll-smooth">

  {#if product?.id}
    <LiquidHeader {product} {themeMode} {applyTheme} scrollToQuiz={scrollToQuiz} />
    <HeroBanner {scrollToQuiz} />

    <!-- SECTIONS WITH INDEPENDENT JIT LOADING (Elite V2.2 Optimization) -->
    <!-- This preserves snap points while components are loading -->
    
    <div id="jit-trigger"></div>

    <section id="diagnostics" class="snap-session">
      {#if loadJIT}
        {#await import('$lib/components/client/slug/DiagnosticsSection.svelte') then { default: DiagnosticsSection }}
          <DiagnosticsSection />
        {/await}
      {:else}
        <div class="w-full h-full bg-[#050505] animate-pulse rounded-t-3xl border-t border-[#111]"></div>
      {/if}
    </section>

    <section id="science" class="snap-session">
      {#if loadJIT}
        {#await import('$lib/components/client/slug/ScienceBento.svelte') then { default: ScienceBento }}
          <ScienceBento />
        {/await}
      {:else}
        <div class="w-full h-full bg-[#050505] animate-pulse"></div>
      {/if}
    </section>

    <section id="reviews" class="snap-session">
      {#if loadJIT}
        {#await import('$lib/components/client/slug/VerifiedReviews.svelte') then { default: VerifiedReviews }}
          <VerifiedReviews />
        {/await}
      {:else}
        <div class="w-full h-full bg-[#050505] animate-pulse"></div>
      {/if}
    </section>

    <section id="offers" class="snap-session">
      {#if loadJIT}
        {#await import('$lib/components/client/slug/OfferGrid.svelte') then { default: OfferGrid }}
          <OfferGrid />
        {/await}
      {:else}
        <div class="w-full h-full bg-[#050505] animate-pulse"></div>
      {/if}
    </section>

    <StealthCheckout />
  {:else}
    <div class="flex flex-col items-center justify-center min-h-screen bg-[#050505] text-white">
       <div class="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
       <p class="text-sm tracking-[0.2em] font-light animate-pulse text-blue-400">{loadingText}</p>
    </div>
  {/if}
  </div>
{/if}

<style lang="postcss">
  .client-page-root {
    antialiased: true;
    overflow-x: hidden;
    scroll-snap-type: y mandatory;
    height: 100vh;
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: var(--bg-canvas);
    color: var(--text-base);
  }

  :root {
    --standard-pt: 12vh;
    --z-sticky-header: 100;
  }

  :global(.snap-session) {
    scroll-snap-align: start;
    scroll-snap-stop: always;
    min-height: 100vh;
    height: auto;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
    overflow: visible;
  }

  /* Ensure smooth transitions inside snap sessions */
  :global(section) {
    transition: opacity 0.8s ease;
  }
</style>
