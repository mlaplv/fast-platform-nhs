<script lang="ts">
  import { onMount } from 'svelte';
  import { setShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import HeroBanner from '$lib/components/client/HeroBanner.svelte';
  import StealthCheckout from '$lib/components/client/StealthCheckout.svelte';
  
  // New Modular Components
  import DiagnosticsSection from '$lib/components/client/slug/DiagnosticsSection.svelte';
  import ScienceBento from '$lib/components/client/slug/ScienceBento.svelte';
  import VerifiedReviews from '$lib/components/client/slug/VerifiedReviews.svelte';
  import OfferGrid from '$lib/components/client/slug/OfferGrid.svelte';
  
  import MobileLandingLayout from '$lib/components/mobile/MobileLandingLayout.svelte';
  
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  // 🚀 ELITE CONTEXT INJECTION (Elite V2.2)
  const shopStore = setShopStore();

  // Protection & Derived State
  const product = $derived(data?.product);
  const metadata = $derived(product?.metadata || {});
  const isMobile = $derived(data?.isMobile || false);

  const loadingText = $derived(metadata.sync_loading_text || 'SYNCHRONIZING ELITE ASSETS...');
  const siteName = $derived(metadata.seo_site_name || 'Elite Storefront');

  // Loại bỏ hardcode slug, sử dụng metadata từ DB để quyết định layout
  const useMobileLayout = $derived(isMobile && metadata?.landing_type === 'tiktok');

  // Quantum Sync: Init store immediately for SSR stability
  if (product?.id) {
     shopStore.init(product);
  }

  $effect.pre(() => {
    if (product?.id) {
       shopStore.init(product);
    }
  });

  // Cleanup Timer on unmount
  onMount(() => {
    return () => shopStore.dispose();
  });

  const scrollToQuiz = () => {
    const el = document.getElementById('diagnostics');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };
</script>

<svelte:head>
  <title>{product?.name || 'Loading...'} | {siteName}</title>
</svelte:head>

{#if useMobileLayout}
  {#if product}
    <MobileLandingLayout {product} />
  {/if}
{:else}
  <div class="client-page-root selection:bg-blue-600 selection:text-white h-screen overflow-y-scroll scroll-smooth">

  {#if product?.id}
    <HeroBanner {scrollToQuiz} />

    <!-- DIAGNOSTICS: AI Analysis & Personalized Quiz -->
    <DiagnosticsSection />

    <!-- SCIENCE: Bento Grid with Technology Highlights -->
    <ScienceBento />

    <!-- REVIEWS: Verified Stealth Reviews -->
    <VerifiedReviews />

    <!-- OFFER: Pricing Packages & Scarcity Timer -->
    <OfferGrid />

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
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-canvas);
    color: var(--text-base);
  }

  :root {
    --standard-pt: 12vh;
  }

  :global(.snap-session) {
    scroll-snap-align: start;
    scroll-snap-stop: always;
    height: 100vh;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
    overflow: hidden;
  }

  /* Ensure smooth transitions inside snap sessions */
  :global(section) {
    transition: opacity 0.8s ease;
  }
</style>
