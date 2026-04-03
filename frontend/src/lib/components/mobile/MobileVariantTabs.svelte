<script lang="ts">
  import { scale } from 'svelte/transition';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  interface MobileVariantTabsProps {
    hidden?: boolean;
  }

  let { hidden = false }: MobileVariantTabsProps = $props();

  const shopStore = getShopStore();
  const product = $derived(shopStore.product);
  const currentVariant = $derived(shopStore.variant);

  // Elite V2.2: Extract variant options from tierVariations
  const variants = $derived(product?.tierVariations?.[0]?.options || []);
  const activeIndex = $derived(currentVariant?.tierIndex?.[0] ?? -1);

  function selectVariant(index: number) {
    shopStore.selectVariantByTier([index]);
  }
</script>

<div
  class="fixed top-0 left-0 right-0 flex justify-center pt-safe-top tabs-container"
  class:tabs-hidden={hidden}
>
  <div class="flex items-center gap-6 px-6 py-4">
    {#each variants as variant, i}
      <button
        class="relative flex flex-col items-center group transition-all duration-300"
        onclick={() => selectVariant(i)}
      >
        <span
          class="text-[11px] font-black tracking-widest transition-all duration-300 uppercase {activeIndex === i ? 'text-white scale-110 shadow-glow-text' : 'text-white/30'}"
        >
          {variant}
        </span>
        
        {#if activeIndex === i}
          <div
            class="absolute -bottom-2 w-4 h-[3px] bg-white rounded-full shadow-[0_0_12px_rgba(255,255,255,1)]"
            transition:scale={{ duration: 300, start: 0 }}
          ></div>
        {/if}
      </button>
    {/each}
  </div>
</div>

<style lang="postcss">
  .pt-safe-top {
    padding-top: env(safe-area-inset-top, 20px);
  }

  .tabs-container {
    opacity: 1;
    transition: opacity 0.3s ease, visibility 0.3s ease;
    visibility: visible;
    z-index: 100; /* Z_INDEX_CLIENT.MOBILE_TAB_BAR */
  }

  .tabs-hidden {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
  }

  .shadow-glow-text {
    /* Adaptive shadow: visible on white, transparent on black */
    text-shadow: 
      0 1px 2px rgba(0, 0, 0, 0.8),
      0 0 15px rgba(0, 0, 0, 0.4);
  }
</style>
