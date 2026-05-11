<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Droplet from "@lucide/svelte/icons/droplet";
  import Info from "@lucide/svelte/icons/info";

  const shopStore = getShopStore();
  let { product: propProduct } = $props();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : (propProduct || shopStore.product));
  const metadata = $derived(product?.metadata || {});

  const hasSpecs = $derived(metadata.brand || metadata.origin || metadata.weight || product?.sku);
  const hasIngredients = $derived(metadata.featured_ingredients?.length > 0 || metadata.ingredients);
</script>

{#if hasSpecs || hasIngredients}
<div class="specs-section-mobile py-12 px-6 bg-black relative overflow-hidden" id="specs">
  <!-- HUD Header -->
  <div class="flex items-center gap-3 mb-8">
    <div class="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
      <Info class="w-5 h-5 text-pink-300" />
    </div>
    <div class="flex flex-col">
      <h2 class="text-xl font-black text-white italic tracking-tight uppercase">Thông số & Thành phần</h2>
      <span class="text-[8px] font-bold text-white/30 uppercase tracking-widest font-mono">PRODUCT_DATABANK // V2.6</span>
    </div>
  </div>

  <!-- Specs Grid -->
  {#if hasSpecs}
    <div class="grid grid-cols-2 gap-4 mb-10">
      {#if metadata.brand}
        <div class="bg-white/5 border border-white/5 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm transition-all hover:border-white/10 hover:bg-white/10">
          <span class="text-[9px] font-bold text-white/20 uppercase tracking-widest">Thương hiệu</span>
          <span class="text-sm font-black text-white italic">{metadata.brand}</span>
        </div>
      {/if}
      {#if metadata.origin}
        <div class="bg-white/5 border border-white/5 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm transition-all hover:border-white/10 hover:bg-white/10">
          <span class="text-[9px] font-bold text-white/20 uppercase tracking-widest">Xuất xứ</span>
          <span class="text-sm font-black text-white italic">{metadata.origin}</span>
        </div>
      {/if}
      {#if metadata.weight}
        <div class="bg-white/5 border border-white/5 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm transition-all hover:border-white/10 hover:bg-white/10">
          <span class="text-[9px] font-bold text-white/20 uppercase tracking-widest">Trọng lượng</span>
          <span class="text-sm font-black text-white italic">{metadata.weight}</span>
        </div>
      {/if}
      {#if product?.sku}
        <div class="bg-white/5 border border-white/5 rounded-2xl p-4 flex flex-col gap-1 backdrop-blur-sm transition-all hover:border-white/10 hover:bg-white/10">
          <span class="text-[9px] font-bold text-white/20 uppercase tracking-widest">SKU</span>
          <span class="text-sm font-black text-white italic font-mono uppercase text-[11px]">{product.sku}</span>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Featured Ingredients -->
  {#if metadata.featured_ingredients?.length > 0}
    <div class="space-y-4 mb-8">
      <div class="flex items-center gap-2 mb-4">
        <Droplet class="w-4 h-4 text-pink-300" />
        <span class="text-[10px] font-black text-white/40 uppercase tracking-widest">Thành phần chủ chốt</span>
      </div>
      
      {#each metadata.featured_ingredients as ing}
        <div class="flex items-start gap-4 p-4 bg-white/5 border border-white/5 rounded-2xl relative overflow-hidden">
          <div class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-pink-300 to-transparent"></div>
          <div class="flex-1">
            <h4 class="text-sm font-black text-white mb-1 italic">{ing.name}</h4>
            <p class="text-xs text-white/50 leading-relaxed">{ing.benefit}</p>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Full Ingredients -->
  {#if metadata.ingredients}
    <div class="p-5 bg-white/5 border border-white/5 rounded-3xl mt-8">
      <span class="text-[8px] font-black text-white/20 uppercase tracking-widest mb-3 block">Bảng thành phần đầy đủ</span>
      <p class="text-[10px] text-white/40 leading-relaxed italic text-justify font-medium">
        {metadata.ingredients}
      </p>
    </div>
  {/if}

  <!-- Design Flourish -->
  <div class="absolute -top-20 -right-20 w-64 h-64 bg-[#FFB7C5]/5 blur-[100px] rounded-full pointer-events-none"></div>
  <div class="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-500/5 blur-[100px] rounded-full pointer-events-none"></div>
</div>
{/if}

<style lang="postcss">
  .specs-section-mobile {
    background-color: #000;
  }
</style>
