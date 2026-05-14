<script lang="ts">
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ChevronUp from "@lucide/svelte/icons/chevron-up";
  import Beaker from "@lucide/svelte/icons/beaker";
  import Info from "@lucide/svelte/icons/info";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import type { Product } from '$lib/types';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';
  import { getIngredientIcon } from '$lib/utils/product';

  let { product, onTriggerScan }: { 
    product: Product,
    onTriggerScan?: () => void
  } = $props();

  let isExpanded = $state(false);
  let isIngredientsExpanded = $state(false);
  let containerRef = $state<HTMLElement>();
  let hasMore = $state(false);
  let activeMobileFaq = $state<number | null>(0);
  let mounted = $state(false);
  const truncatedHeight = 400;

  import { onMount } from 'svelte';
  onMount(() => { mounted = true; });

  $effect(() => {
    if (containerRef) {
      hasMore = containerRef.scrollHeight > truncatedHeight;
    }
  });

  function isJson(str: string | null | undefined): boolean {
    if (typeof str !== 'string' || !str) return false;
    try {
      const parsed = JSON.parse(str);
      return typeof parsed === 'object' && parsed !== null && ('hero_headline' in parsed || 'spec_bento' in parsed);
    } catch {
      return false;
    }
  }

  const brand = $derived(product.attributes?.['Thương hiệu'] || product.attributes?.['Brand'] || product.metadata?.brand);
</script>

<section class="content-section">
  {#if product.attributes && Object.entries(product.attributes).length > 0}
    <div class="mb-6 grid grid-cols-2 gap-x-6 gap-y-1">
      {#each Object.entries(product.attributes) as [key, val]}
        <div class="flex flex-col py-1.5 border-b border-gray-50/50 overflow-hidden">
          <span class="text-[10px] text-gray-400 font-medium truncate">{key.replace(/_/g, ' ')}</span>
          <span class="text-[12px] text-gray-800 font-bold truncate">{val}</span>
        </div>
      {/each}
      {#if product.sku || product.metadata?.['barcode']}
        <button 
          class="flex flex-col py-1.5 border-b border-gray-50/50 overflow-hidden text-left bg-transparent active:opacity-60 transition-opacity"
          onclick={() => onTriggerScan?.()}
        >
          <span class="text-[10px] text-green-600 font-bold tracking-tight">Mã vạch (Verify)</span>
          <span class="text-[12px] text-gray-800 font-mono font-bold truncate">{product.sku || product.metadata?.['barcode']}</span>
        </button>
      {/if}
    </div>
  {/if}

  <!-- Elite V2.2: Featured Ingredients (Viral Cards) -->
  {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
    <div class="mb-6">
      <h2 class="section-title">Thành phần nổi bật</h2>
      <div class="grid grid-cols-1 gap-2">
        {#each product.metadata.featured_ingredients as ing}
          <div class="group bg-[#fdf2f2]/40 border border-[#ee4d2d]/10 p-2 rounded-xl flex items-center gap-3 transition-all hover:bg-white hover:shadow-md">
            <div class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-xl flex items-center justify-center text-[20px] shadow-sm group-hover:scale-110 transition-transform">
              {ing.icon || getIngredientIcon(ing.name)}
            </div>
            <div class="flex flex-col">
              <span class="text-[12px] font-black text-gray-900 leading-tight">{ing.name}</span>
              <p class="text-[10px] text-gray-500 leading-tight font-medium mt-0.5 line-clamp-2">
                {ing.benefit}
              </p>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Elite V2.2: Full Ingredients (Mobile Transparency) -->
  {#if product.metadata?.ingredients}
    <div class="mt-4 mb-6 flex flex-col gap-2">
      <h2 class="flex items-center gap-2 text-[11px] font-bold text-gray-400 tracking-wider">
        <Beaker size={12} class="text-teal-500" /> Bảng thành phần {product.name}
      </h2>
      <button 
        type="button"
        class="bg-gray-50/50 border border-gray-100 p-4 rounded-xl text-left relative overflow-hidden transition-all duration-500"
        onclick={() => isIngredientsExpanded = !isIngredientsExpanded}
        style:max-height={isIngredientsExpanded ? 'none' : '100px'}
      >
        <p class="text-[11px] text-gray-600 font-mono leading-relaxed tracking-tight {!isIngredientsExpanded ? 'line-clamp-3' : ''}">
          {product.metadata.ingredients}
        </p>
        {#if !isIngredientsExpanded}
          <div class="absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-gray-50/95 to-transparent flex items-end justify-center pb-1">
            <div class="flex items-center gap-1 text-gray-400 font-sans">
              <span class="text-[11px] font-medium">Xem thêm</span>
              <ChevronDown size={12} />
            </div>
          </div>
        {:else}
          <div class="mt-2 flex justify-center">
             <div class="flex items-center gap-1 text-gray-400 font-sans">
                <span class="text-[11px] font-medium">Thu gọn</span>
                <ChevronUp size={12} />
             </div>
          </div>
        {/if}
      </button>
      <div class="mt-1 flex items-center gap-2 px-1">
        <Info size={10} class="text-blue-500" />
        <span class="text-[9px] text-gray-400 font-bold italic">Chi tiết có trên bao bì sản phẩm chính hãng</span>
      </div>
    </div>
  {/if}
  
  <h2 class="section-title mt-6">Chi tiết {product.name}</h2>
  
  <div 
    class="description-wrapper {(!isExpanded && hasMore) ? 'collapsed' : ''}"
    style:max-height={isExpanded ? 'none' : (hasMore ? truncatedHeight + 'px' : 'none')}
  >
    <div bind:this={containerRef} class="prose-osmo pb-4">
      {#if isJson(product.description)}
         <InteractiveDashboard data={product.description} compact={true} />
      {:else}
         {@html product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
      {/if}
    </div>
  </div>

  {#if mounted && hasMore}
    <button 
      type="button"
      class="expand-btn-elite" 
      onclick={() => isExpanded = !isExpanded}
    >
      {#if isExpanded}
        Thu gọn <ChevronUp size={16} />
      {:else}
        Xem thêm <ChevronDown size={16} />
      {/if}
    </button>
  {/if}

  <!-- GEO 2026: Mobile FAQ Section -->
  {#if product.metadata?.faqs && product.metadata.faqs.length > 0}
    <div class="mt-8 border-t border-gray-100 pt-6">
      <h2 class="section-title">Câu hỏi về {product.name}</h2>
      <div class="flex flex-col gap-2 mt-4">
        {#each product.metadata.faqs as faq, i}
          <div class="bg-gray-50/50 border border-gray-100 rounded-[5px] overflow-hidden transition-all {activeMobileFaq === i ? 'border-[#ee4d2d]/30 bg-white shadow-sm' : ''}">
            <button 
              class="w-full flex items-center justify-between p-3 text-left bg-transparent border-none"
              onclick={() => activeMobileFaq = activeMobileFaq === i ? null : i}
            >
              <h3 class="text-[13px] font-bold text-gray-900 leading-tight pr-4">{faq.question}</h3>
              <ChevronDown size={14} class="text-gray-400 transition-transform {activeMobileFaq === i ? 'rotate-180 text-[#ee4d2d]' : ''}" />
            </button>
            {#if activeMobileFaq === i}
              <div class="px-3 pb-3 animate-[fadeIn_0.2s_ease-out]">
                <p class="text-[12px] text-gray-600 leading-relaxed border-t border-gray-50 pt-2">{faq.answer}</p>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</section>

<style>
  .content-section { padding: 8px 5px 16px 5px; background: white; margin-bottom: 8px; overflow: hidden; }
  .section-title { font-size: 13px; font-weight: 800; color: #333; margin-bottom: 12px; border-left: 3px solid #ee4d2d; padding-left: 10px; text-transform: none; }
  
  /* Elite V2.2: Smooth Description Truncation */
  .description-wrapper {
    position: relative;
    overflow: hidden;
    transition: max-height 0.8s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .description-wrapper.collapsed::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 100px;
    background: linear-gradient(to bottom, transparent, white 90%);
    pointer-events: none;
  }

  .expand-btn-elite {
    background: transparent;
    border: none;
    color: #ee4d2d;
    font-size: 13px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-top: 12px;
    padding: 10px;
    gap: 4px;
    border-radius: 0;
    box-shadow: none;
  }

  /* Elite V2.2: Mobile Premium Prose System (Viral Bullets) */
  :global(.prose-osmo) {
    font-size: 14px !important;
    line-height: 1.7 !important;
    color: #444 !important;
  }

  :global(.prose-osmo p) {
    margin-bottom: 1rem !important;
  }

  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #000 !important;
    font-weight: 900 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.75rem !important;
  }

  :global(.prose-osmo ul) {
    margin-bottom: 1rem !important;
    padding-left: 0 !important;
    list-style: none !important;
  }

  :global(.prose-osmo li) {
    margin-bottom: 0.5rem !important;
    position: relative;
    padding-left: 1.5rem;
  }

  :global(.prose-osmo li::before) {
    content: "✦";
    position: absolute;
    left: 0;
    color: #ee4d2d;
    font-weight: bold;
  }

  :global(.prose-osmo img) {
    border-radius: 12px;
    margin: 1rem 0 !important;
    width: 100% !important;
    height: auto !important;
  }
</style>
