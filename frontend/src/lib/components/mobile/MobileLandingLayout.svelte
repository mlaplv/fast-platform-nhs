<script lang="ts">
  import { onMount } from 'svelte';
  import { Music } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import MobileActionStack from './MobileActionStack.svelte';
  import MobileBottomSheet from './MobileBottomSheet.svelte';
  import MobileVariantTabs from './MobileVariantTabs.svelte';
  
  // Dedicated Mobile Sections
  import MobileHero from './sections/MobileHero.svelte';
  import MobileDiagnostics from './sections/MobileDiagnostics.svelte';
  import MobileScience from './sections/MobileScience.svelte';
  import MobileReviews from './sections/MobileReviews.svelte';
  import MobileOffer from './sections/MobileOffer.svelte';
  
  import './mobile.css';

  const shopStore = getShopStore();
  const product = $derived(shopStore.product);
</script>

<div class="mobile-snap-container relative">
  <!-- PERSISTENT OVERLAYS -->
  <MobileVariantTabs />
  <MobileActionStack {product} onPurchase={() => shopStore.openCheckout()} />

  <!-- SECTION 1: NATIVE HERO -->
  <section class="mobile-snap-section">
    <MobileHero {product} />
  </section>

  <!-- SECTION 2: NATIVE DIAGNOSTICS -->
  <section class="mobile-snap-section">
    <MobileDiagnostics {product} />
  </section>

  <!-- SECTION 3: NATIVE SCIENCE -->
  <section class="mobile-snap-section">
    <MobileScience {product} />
  </section>

  <!-- SECTION 4: NATIVE REVIEWS -->
  <section class="mobile-snap-section">
    <MobileReviews {product} />
  </section>

  <!-- SECTION 5: NATIVE OFFER -->
  <section class="mobile-snap-section">
    <MobileOffer {product} />
  </section>

  <MobileBottomSheet bind:active={shopStore.isCheckoutOpen} {product} />
</div>

<style lang="postcss">
  /* Override section internal padding for mobile snap */
  :global(.mobile-snap-section section) {
    padding-top: 8vh !important;
    min-height: 100dvh;
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
