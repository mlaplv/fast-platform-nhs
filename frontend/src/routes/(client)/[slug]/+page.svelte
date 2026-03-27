<script lang="ts">
  import { onMount } from 'svelte';
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import HeroBanner from '$lib/components/client/HeroBanner.svelte';
  import StealthCheckout from '$lib/components/client/StealthCheckout.svelte';
  
  // New Modular Components
  import DiagnosticsSection from '$lib/components/client/slug/DiagnosticsSection.svelte';
  import ScienceBento from '$lib/components/client/slug/ScienceBento.svelte';
  import OfferGrid from '$lib/components/client/slug/OfferGrid.svelte';
  
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  // Protection thưa Sếp!
  if (!data || !data.product) {
    console.error('[SlugPage] Data missing');
  }
  const product = data?.product || {};

  let timeLeft = $state(1800);

  onMount(() => {
    if (product?.id) {
       shopStore.init(product);
    }
    const timer = setInterval(() => timeLeft > 0 && timeLeft--, 1000);
    return () => clearInterval(timer);
  });

  const scrollToQuiz = () => document.getElementById('diagnostics')?.scrollIntoView({ behavior: 'smooth' });
</script>

<svelte:head>
  <title>{product?.name || 'Loading...'} | Elite Storefront</title>
</svelte:head>

<div class="client-page-root selection:bg-blue-600 selection:text-white">
  
  {#if product?.id}
    <HeroBanner {product} {scrollToQuiz} />

    <!-- DIAGNOSTICS: AI Analysis & Personalized Quiz -->
    <DiagnosticsSection />

    <!-- SCIENCE: Bento Grid with Technology Highlights -->
    <ScienceBento {product} />

    <!-- OFFER: Pricing Packages & Scarcity Timer -->
    <OfferGrid {timeLeft} />

    <StealthCheckout />
  {:else}
    <div class="flex items-center justify-center min-h-screen bg-canvas text-white">
       <p class="animate-pulse">LOADING ELITE ASSETS...</p>
    </div>
  {/if}
</div>

<style lang="postcss">
  .client-page-root {
    antialiased: true;
    overflow-x: hidden;
    min-height: 100vh;
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-canvas);
    color: var(--text-base);
  }
</style>
