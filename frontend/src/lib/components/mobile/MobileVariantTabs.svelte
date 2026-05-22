<script lang="ts">

  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import SmartSearchMobile from '$lib/components/storefront/product/SmartSearchMobile.svelte';

  interface MobileVariantTabsProps {
    hidden?: boolean;
  }

  let { hidden = false }: MobileVariantTabsProps = $props();

  const shopStore = getShopStore();
  const searchStore = getSearchStore();
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
  class="absolute top-0 left-0 right-0 flex justify-center pt-tabs tabs-container z-[60] pointer-events-none"
  class:tabs-hidden={hidden}
>
  <div class="relative w-full flex items-center justify-center px-4 pointer-events-auto">
    <!-- TikTok Tabs -->
    <div class="flex items-center gap-5 overflow-x-auto no-scrollbar scroll-smooth px-2 max-w-[85%]">
      {#each variants as variant, i}
        <button
          class="relative flex flex-col items-center justify-center transition-all duration-300 pt-2 pb-1.5 {activeIndex === i ? 'opacity-100' : 'opacity-80'}"
          onclick={() => selectVariant(i)}
        >
          <!-- Red dot on the second tab for that TikTok feel -->
          {#if i === 1}
             <div class="absolute top-1 -right-2 w-2 h-2 bg-[#fe2c55] rounded-full shadow-sm border-[1.5px] border-black/10"></div>
          {/if}
          
          <span class="text-[16px] {activeIndex === i ? 'font-bold' : 'font-medium'} text-white whitespace-nowrap drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">
            {variant}
          </span>
          <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-[3px] bg-white rounded-full transition-all duration-300 ease-out {activeIndex === i ? 'opacity-100 scale-100' : 'opacity-0 scale-50'} shadow-[0_1px_2px_rgba(0,0,0,0.5)]"></div>
        </button>
      {/each}
    </div>

    <!-- TikTok Search Icon -->
    <button onclick={() => searchStore.isOverlayOpen = true} class="absolute right-4 p-1 opacity-90 hover:opacity-100 transition-opacity shrink-0">
       <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="drop-shadow-[0_1px_2px_rgba(0,0,0,0.6)]">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
       </svg>
    </button>
  </div>
</div>

<SmartSearchMobile />

<style lang="postcss">
  .pt-tabs {
    padding-top: calc(env(safe-area-inset-top, 20px) + 12px);
  }

  .tabs-container {
    opacity: 1;
    transition: opacity 0.3s ease, visibility 0.3s ease;
    visibility: visible;
  }

  .tabs-hidden {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
  }
  
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
