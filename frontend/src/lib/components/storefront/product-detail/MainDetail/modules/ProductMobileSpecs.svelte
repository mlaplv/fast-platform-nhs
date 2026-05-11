<script lang="ts">
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ChevronUp from "@lucide/svelte/icons/chevron-up";
  import Beaker from "@lucide/svelte/icons/beaker";
  import Info from "@lucide/svelte/icons/info";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import type { Product } from '$lib/types';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';
  import { getIngredientIcon } from '$lib/utils/product';

  let { product }: { product: Product } = $props();

  let isExpanded = $state(false);
  let isIngredientsExpanded = $state(false);
  let containerRef = $state<HTMLElement>();
  let hasMore = $state(false);
  const truncatedHeight = 400;

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
  <!-- Elite V2.2: Featured Ingredients (Viral Cards) -->
  {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
    <div class="mb-6">
      <h2 class="section-title">Thành phần nổi bật</h2>
      <div class="grid grid-cols-1 gap-3">
        {#each product.metadata.featured_ingredients as ing}
          <div class="flex gap-3 bg-[#fdf2f2]/50 border border-[#ee4d2d]/5 p-3 rounded-xl">
            <div class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-full flex items-center justify-center text-[18px]">
              {ing.icon || getIngredientIcon(ing.name)}
            </div>
            <div class="flex flex-col">
              <span class="text-[13px] font-black text-gray-900 leading-none mb-1">{ing.name}</span>
              <span class="text-[11px] text-gray-500 leading-relaxed font-medium">{ing.benefit}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Elite V2.2: Full Ingredients (Mobile Transparency) -->
  {#if product.metadata?.ingredients}
    <div class="mt-4 flex flex-col gap-2">
      <div class="flex items-center gap-2 text-[10px] font-black text-gray-400 tracking-widest uppercase">
        <Beaker size={12} class="text-teal-500" /> Bảng thành phần (Full INCI)
      </div>
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

  {#if product.attributes && Object.keys(product.attributes).length > 0}
    <div class="mt-6 grid grid-cols-2 gap-2">
      {#each Object.entries(product.attributes) as [key, val]}
        <div class="flex flex-col p-2 bg-gray-50/50 rounded-lg">
          <span class="text-[10px] text-gray-400 font-bold uppercase">{key.replace(/_/g, ' ')}</span>
          <span class="text-[12px] text-gray-800 font-medium">{val}</span>
        </div>
      {/each}
    </div>
  {/if}
  
  <h2 class="section-title mt-8">Mô tả sản phẩm</h2>
  
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

  {#if hasMore}
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
      <h2 class="section-title">Câu hỏi thường gặp</h2>
      <div class="flex flex-col gap-3 mt-4">
        {#each product.metadata.faqs as faq}
          <div class="bg-gray-50/50 border border-gray-100 rounded-lg p-3">
            <h3 class="text-[13px] font-bold text-gray-900 mb-1.5 leading-tight">{faq.question}</h3>
            <p class="text-[12px] text-gray-600 leading-relaxed">{faq.answer}</p>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</section>

<style>
  .content-section { background: white; padding: 20px; overflow: hidden; }
  .section-title { font-size: 15px; font-weight: 900; color: #222; margin-bottom: 16px; letter-spacing: -0.01em; border-left: 4px solid #ee4d2d; padding-left: 12px; }
  
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
    background: white;
    border: 1px solid #f0f0f0;
    color: #ee4d2d;
    font-size: 12px;
    font-weight: 900;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin-top: 16px;
    padding: 12px;
    gap: 6px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
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
