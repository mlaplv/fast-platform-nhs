<script lang="ts">
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ChevronUp from "@lucide/svelte/icons/chevron-up";
  import Beaker from "@lucide/svelte/icons/beaker";
  import Info from "@lucide/svelte/icons/info";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import type { Product } from '$lib/types';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';
  import { getIngredientIcon, parseDescriptionAndCommitments } from '$lib/utils/product';

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

  const parsedDescription = $derived(parseDescriptionAndCommitments(product.description));

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
    </div>
  {/if}

  <!-- Elite V2.2: Featured Ingredients (Viral Cards) -->
  {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
    <div class="mb-6">
      <h2 class="section-title">Thành phần nổi bật</h2>
      <div class="grid grid-cols-1 gap-2">
        {#each product.metadata.featured_ingredients as ing}
          <div class="group bg-[#fdf2f2]/40 border border-[#ee4d2d]/10 p-2 rounded-xl flex items-center gap-3 transition-all hover:bg-white hover:shadow-md">
            <div class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-xl flex items-center justify-center text-[18px] shadow-sm group-hover:scale-110 transition-transform">
              {ing.icon || getIngredientIcon(ing.name)}
            </div>
            <div class="flex flex-col justify-center">
              <span class="text-[14px] font-bold text-gray-900 leading-tight">{ing.name}</span>
              <p class="text-[12px] text-gray-500 leading-normal mt-0.5">
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
      <h2 class="flex items-center gap-2 text-[16px] font-bold text-gray-800 tracking-tight">
        <Beaker size={16} class="text-teal-500" /> Bảng thành phần
      </h2>
      <button 
        type="button"
        class="bg-gray-50/50 border border-gray-100 p-4 rounded-xl text-left relative overflow-hidden transition-all duration-500"
        onclick={() => isIngredientsExpanded = !isIngredientsExpanded}
        style:max-height={isIngredientsExpanded ? 'none' : '100px'}
      >
        <p class="text-[12px] text-gray-600 font-mono leading-relaxed tracking-tight {!isIngredientsExpanded ? 'line-clamp-3' : ''}">
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
  
  <h2 class="section-title mt-6">Chi tiết</h2>
  
  <div 
    class="description-wrapper {(!isExpanded && hasMore) ? 'collapsed' : ''}"
    style:max-height={isExpanded ? 'none' : (hasMore ? truncatedHeight + 'px' : 'none')}
  >
    <div bind:this={containerRef} class="prose-osmo pb-4">
      {#if isJson(product.description)}
         <InteractiveDashboard data={product.description} compact={true} />
      {:else}
         {@html parsedDescription.cleanDescription || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
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

  {#if parsedDescription.commitments}
    {@const commitments = parsedDescription.commitments}
    <div class="commitment-card-luxury mt-6 p-4 rounded-xl border border-emerald-500/10 bg-white/40 relative overflow-hidden shadow-[0_10px_20px_rgba(4,120,87,0.01)] backdrop-blur-md transition-all duration-300">
      <!-- Subtle Mobile backlights -->
      <div class="absolute -top-6 -right-6 w-20 h-20 rounded-full bg-emerald-100/20 blur-xl pointer-events-none"></div>
      <div class="absolute -bottom-6 -left-6 w-20 h-20 rounded-full bg-teal-100/20 blur-xl pointer-events-none"></div>
      
      <div class="relative z-10 flex flex-col gap-2">
        <!-- Mobile Header: Single horizontal line -->
        <div class="flex items-center gap-1.5 pb-2 border-b border-emerald-500/10">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="text-[11px] font-black text-slate-800 uppercase tracking-wider truncate">{commitments.title}</span>
          <span class="text-gray-300 text-[10px]">|</span>
          <span class="text-[10px] font-bold text-[#ee4d2d] truncate">{commitments.subtitle}</span>
        </div>

        <!-- Mobile Items: 3 compact rows -->
        <div class="flex flex-col gap-1 my-1">
          {#each commitments.items as item}
            {@const parts = item.split(':')}
            {@const boldPart = parts[0]}
            {@const normalPart = parts.slice(1).join(':')}
            <div class="flex items-center gap-2 px-2 py-1 bg-white/70 border border-emerald-500/5 rounded-lg">
              <svg class="w-3 h-3 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <div class="flex items-baseline gap-1 min-w-0">
                <span class="text-[10.5px] font-black text-slate-800 shrink-0">{boldPart.trim()}</span>
                {#if normalPart}
                  <span class="text-[9.5px] text-gray-500 truncate">{normalPart.trim()}</span>
                {/if}
              </div>
            </div>
          {/each}
        </div>

        <!-- Mobile Slate FOMO Ribbon (Clickable entire ribbon) -->
        <a href="/chinh-sach-doi-tra-hoan-tien" class="flex items-center justify-between gap-3 pt-2 border-t border-emerald-500/10 mt-1 group no-underline text-slate-700 hover:text-emerald-600 transition-all duration-300">
          <div class="flex items-center gap-1.5 relative z-10 min-w-0">
            <svg class="w-3.5 h-3.5 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span class="text-[9.5px] font-black text-slate-800 uppercase tracking-wider shrink-0">FREESHIP:</span>
            <span class="text-[10px] font-medium text-gray-500 truncate">{commitments.fomo}</span>
          </div>
          
          <div class="flex items-center gap-0.5 relative z-10 shrink-0 text-emerald-600 text-[10px] font-bold group-hover:translate-x-1 transition-transform duration-300">
            <span>Xem thêm</span>
            <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </a>
      </div>
    </div>
  {/if}

  <!-- GEO 2026: Mobile FAQ Section -->
  {#if product.metadata?.faqs && product.metadata.faqs.length > 0}
    <div class="mt-8 border-t border-gray-100 pt-6">
      <h2 class="section-title">Câu hỏi thường gặp</h2>
      <div class="flex flex-col gap-2 mt-4">
        {#each product.metadata.faqs as faq, i}
          <div class="bg-gray-50/50 border border-gray-100 rounded-[5px] overflow-hidden transition-all {activeMobileFaq === i ? 'border-[#ee4d2d]/30 bg-white shadow-sm' : ''}">
            <button 
              class="w-full flex items-center justify-between p-3 text-left bg-transparent border-none"
              onclick={() => activeMobileFaq = activeMobileFaq === i ? null : i}
            >
              <h3 class="text-[14px] font-bold text-gray-900 leading-tight pr-4">{faq.question}</h3>
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
  .section-title { 
    font-size: 16px; 
    font-weight: 700; 
    color: #111; 
    margin-bottom: 4px; 
    border-left: 4px solid #ee4d2d; 
    padding-left: 6px; 
    text-transform: none; 
    letter-spacing: -0.02em;
  }
  
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

  :global(.prose-osmo) {
    font-size: 14px !important; /* Sleek mobile e-commerce standard (Lazada/Shopee) */
    line-height: 1.6 !important;
    color: #374151 !important;
  }

  :global(.prose-osmo p) {
    margin-bottom: 0.75rem !important;
    font-weight: 400 !important;
    letter-spacing: -0.011em !important;
  }

  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #6b7280 !important;
    font-weight: 900 !important;
    margin-top: 1rem !important;
    margin-bottom: 0.3rem !important;
    line-height: 1.3 !important;
    text-transform: lowercase !important;
  }

  :global(.prose-osmo h2::first-letter, .prose-osmo h3::first-letter) {
    text-transform: uppercase !important;
  }

  :global(.prose-osmo ul) {
    margin-bottom: 1rem !important;
    padding-left: 0 !important;
    list-style: none !important;
  }

  :global(.prose-osmo ol) {
    counter-reset: osmo-counter;
    margin-bottom: 1rem !important;
    padding-left: 0 !important;
    list-style: none !important;
  }

  :global(.prose-osmo ul li) {
    margin-bottom: 0.5rem !important;
    position: relative !important;
    padding-left: 0 !important;
  }

  :global(.prose-osmo ol li) {
    margin-bottom: 0.5rem !important;
    position: relative !important;
    padding-left: 0 !important;
  }

  :global(.prose-osmo ul > li::before) {
    content: "✦" !important;
    position: static !important;
    display: inline-block !important;
    color: #ee4d2d !important;
    font-weight: bold !important;
    margin-right: 0.35rem !important;
  }

  :global(.prose-osmo ol > li) {
    counter-increment: osmo-counter;
  }

  :global(.prose-osmo ol > li::before) {
    content: counter(osmo-counter) "." !important;
    position: static !important;
    display: inline-block !important;
    color: #ee4d2d !important;
    font-weight: 900 !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    margin-right: 0.35rem !important;
  }

  :global(.prose-osmo img) {
    border-radius: 12px;
    margin: 1rem 0 !important;
    width: 100% !important;
    height: auto !important;
  }
</style>
