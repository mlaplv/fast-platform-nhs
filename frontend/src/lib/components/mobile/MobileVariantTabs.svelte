<script lang="ts">
  import { scale } from 'svelte/transition';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { SHOP_CONFIG } from '$lib/constants/shop';

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

<div class="fixed top-0 left-0 right-0 z-[100] flex justify-center pt-safe-top">
  <div class="flex items-center gap-6 px-6 py-4">
    {#each variants as variant, i}
      <button
        class="relative flex flex-col items-center group transition-all duration-300"
        onclick={() => selectVariant(i)}
      >
        <span
          class="text-[17px] font-bold tracking-tight transition-all duration-300 {activeIndex === i ? 'text-white scale-110' : 'text-white/60 hover:text-white/80'}"
        >
          {variant}
        </span>
        {#if activeIndex === i}
          <div
            class="absolute -bottom-1 w-6 h-[3px] bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.8)]"
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
</style>
