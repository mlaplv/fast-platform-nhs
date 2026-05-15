<script lang="ts">

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
  class="absolute top-0 left-0 right-0 flex justify-center pt-tabs tabs-container"
  class:tabs-hidden={hidden}
>
  <div class="glass-capsule relative flex items-center p-1 bg-white/[0.03] backdrop-blur-[40px] border border-white/10 rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.3)]">
    <!-- 🚀 iOS 26 Sliding Active Pill -->
    {#if activeIndex !== -1}
      <div 
        class="absolute top-1 bottom-1 bg-white/10 backdrop-blur-md border border-white/10 rounded-full transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] shadow-[0_2px_10px_rgba(0,0,0,0.2),inset_0_1px_1px_rgba(255,255,255,0.1)]"
        style="width: calc((100% - 8px) / {variants.length}); left: calc(4px + {activeIndex} * (100% - 8px) / {variants.length})"
      ></div>
    {/if}

    {#each variants as variant, i}
      <button
        class="relative px-6 py-2.5 rounded-full transition-all duration-500 z-10 {activeIndex === i ? 'text-white' : 'text-white/30 hover:text-white/60'}"
        onclick={() => selectVariant(i)}
      >
        <span class="text-[10px] font-black tracking-[0.25em] italic whitespace-nowrap drop-shadow-sm">
          {variant}
        </span>
      </button>
    {/each}
  </div>
</div>

<style lang="postcss">
  .pt-tabs {
    padding-top: calc(env(safe-area-inset-top, 20px) + 16px);
  }

  .tabs-container {
    opacity: 1;
    transition: opacity 0.3s ease, visibility 0.3s ease;
    visibility: visible;
    z-index: var(--z-mobile-tabs);
  }

  .tabs-hidden {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
  }
</style>
