<script lang="ts">
  import type { Product } from '$lib/types';
    import X from "@lucide/svelte/icons/x";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Info from "@lucide/svelte/icons/info";
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { portal } from '$lib/core/actions/portal';
  import { fade } from 'svelte/transition';
  import { lightLiveEdit } from '$lib/state/commerce/liveEditState.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';

  function isJson(str: string) {
    if (typeof str !== 'string') return false;
    try {
      const parsed = JSON.parse(str);
      return typeof parsed === 'object' && parsed !== null && ('hero_headline' in parsed || 'spec_bento' in parsed);
    } catch (e) {
      return false;
    }
  }

  const shopStore = getShopStore();
  let { active = $bindable(), product: propProduct, onTriggerScan }: { active: boolean; product?: Product; onTriggerScan?: () => void } = $props();
  const product = $derived(lightLiveEdit.isEditMode && lightLiveEdit.dirtyProduct ? lightLiveEdit.dirtyProduct : (propProduct || shopStore.product));

  // Bento Spec derived properties (Elite V3.0 Desktop)
  const specBrand = $derived(product?.metadata?.brand || product?.attributes?.["brand"] || product?.attributes?.["Thương hiệu"] || "");
  const specOrigin = $derived(product?.metadata?.origin || product?.attributes?.["origin"] || product?.attributes?.["Xuất xứ"] || "");
  const specWeight = $derived(product?.metadata?.weight || product?.attributes?.["weight"] || product?.attributes?.["Trọng lượng"] || product?.attributes?.["Quy cách"] || "");
  const specBarcode = $derived(product?.metadata?.barcode || product?.sku || "");

  const specAllAttrs = $derived(product?.attributes ? Object.entries(product.attributes).filter(([key, value]) => {
    const k = key.toLowerCase().replace(/_/g, " ").trim();
    return !(
      ((k === "xuất xứ" || k === "origin") && specOrigin) ||
      ((k === "trọng lượng" || k === "quy cách" || k === "weight") && specWeight) ||
      ((k === "mã vạch" || k === "barcode") && specBarcode) ||
      k === "thương hiệu" ||
      k === "brand"
    );
  }) : []);

  function close() { 
    active = false;
  }
</script>

{#if active}
<div 
  use:portal 
  transition:fade={{ duration: 300 }}
  class="desktop-product-details-modal fixed inset-0 w-full h-full bg-[#0a0a0a] text-white flex flex-col" 
  style:z-index={Z_INDEX_CLIENT.MODAL}
  role="dialog"
  aria-modal="true"
>
  <!-- Header -->
  <div class="w-full border-b border-white/5 bg-[#0a0a0a] shrink-0">
    <div class="max-w-5xl mx-auto w-full px-6 md:px-10 pt-8 md:pt-10 pb-5 md:pb-6 flex items-center justify-between">
      <h2 class="text-[14px] font-black tracking-[0.3em] italic text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 flex items-center gap-3">
        <Info class="w-5 h-5 text-emerald-400" />
        Thông tin chi tiết sản phẩm
      </h2>
      
      <!-- Close Button in Header -->
      <button 
        onclick={close} 
        class="w-10 h-10 flex items-center justify-center text-white/20 hover:text-white hover:bg-white/5 transition-all rounded-full"
        aria-label="Đóng"
      >
        <X class="w-6 h-6" strokeWidth={1.5} />
      </button>
    </div>
  </div>

  <!-- Scrollable Description Body -->
  <div class="w-full overflow-y-auto custom-scrollbar flex-1">
    <div class="max-w-5xl mx-auto w-full px-6 md:px-10 py-6 md:py-8 elite-prose">
      <!-- 📊 DETAILED TECHNICAL SPECIFICATIONS (Bento Grid) -->
      <div class="mb-8 p-6 bg-white/[0.02] border border-white/5 rounded-2xl">
        <h3 class="text-[12px] font-bold text-white/40 tracking-[0.2em] uppercase mb-5 flex items-center gap-2">
          <ShieldCheck class="w-4 h-4 text-emerald-400" />
          Thông số kỹ thuật sản phẩm
        </h3>
        
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <!-- Brand Card -->
          <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col gap-1 transition-all duration-300 hover:bg-white/[0.04] hover:border-white/10">
            <span class="text-[9px] font-bold text-white/30 uppercase tracking-widest">Thương hiệu</span>
            <span class="text-[14px] font-bold text-white/90">{specBrand || 'Osmo Elite'}</span>
          </div>

          <!-- Origin Card -->
          <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col gap-1 transition-all duration-300 hover:bg-white/[0.04] hover:border-white/10">
            <span class="text-[9px] font-bold text-white/30 uppercase tracking-widest">Xuất xứ</span>
            <span class="text-[14px] font-bold text-white/90">{specOrigin || 'Nhật Bản'}</span>
          </div>

          <!-- Weight/Quy cách Card -->
          <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col gap-1 transition-all duration-300 hover:bg-white/[0.04] hover:border-white/10">
            <span class="text-[9px] font-bold text-white/30 uppercase tracking-widest">Quy cách</span>
            <span class="text-[14px] font-bold text-white/90">{specWeight || '30g / Tuýp'}</span>
          </div>

          <!-- Barcode Scan Card -->
          <button
            class="bg-emerald-950/10 border border-emerald-500/10 rounded-xl p-4 flex flex-col gap-1 text-left cursor-pointer active:scale-98 transition-all hover:bg-emerald-950/20 hover:border-emerald-500/20"
            onclick={() => onTriggerScan?.()}
          >
            <span class="text-[9px] font-bold text-emerald-400/60 uppercase tracking-widest">Mã vạch (Verify)</span>
            <span class="text-[14px] font-bold text-emerald-400 flex items-center gap-1.5">
              {specBarcode}
              <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
            </span>
          </button>

          <!-- Dynamic attributes -->
          {#each specAllAttrs as [key, value]}
            {@const isLong = String(value).length > 20}
            <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col gap-1 transition-all duration-300 hover:bg-white/[0.04] hover:border-white/10 {isLong ? 'lg:col-span-2' : 'lg:col-span-1'} col-span-1">
              <span class="text-[9px] font-bold text-white/30 uppercase tracking-widest">{key}</span>
              <span class="text-[14px] font-bold text-white/90">{value}</span>
            </div>
          {/each}
        </div>
      </div>

      {#if product?.description}
        <EditableWrapper path="description" type="html" label="SỬA MÔ TẢ CHI TIẾT">
          <div class="elite-prose-container">
            {#if isJson(product.description)}
               <InteractiveDashboard data={product.description} compact={false} />
            {:else}
               <!-- eslint-disable-next-line svelte/no-at-html-tags -->
               {@html product.description}
            {/if}
          </div>
        </EditableWrapper>
      {:else}
        <div class="flex flex-col items-center justify-center h-full min-h-[300px] text-white/30 space-y-4">
          <ShieldCheck class="w-16 h-16 opacity-50" />
          <p class="text-[11px] tracking-[0.4em] font-bold">Chưa có thông tin mô tả chi tiết</p>
        </div>
      {/if}
    </div>
  </div>

  <!-- Footer -->
  <div class="w-full border-t border-white/5 bg-[#0a0a0a] shrink-0">
    <div class="max-w-5xl mx-auto w-full px-6 md:px-10 py-5 md:py-6 flex items-center justify-between">
      <div class="flex items-center gap-3 text-[10px] font-bold text-white/30 tracking-[0.3em] italic">
        <ShieldCheck class="w-4 h-4 text-blue-500/80" />
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-white/60 to-white/30">Hệ thống thông tin chính hãng</span>
      </div>
      <button 
        onclick={close}
        class="px-8 py-2.5 bg-white/5 hover:bg-white/10 text-white text-[10px] font-black tracking-[0.2em] rounded-full border border-white/10 transition-all font-bold"
      >
        Đóng lại
      </button>
    </div>
  </div>
</div>
{/if}

<style lang="postcss">
  /* Elite Prose Typography for Admin HTML content */
  .elite-prose {
    font-size: 16px;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.85);
  }

  :global(.elite-prose h1, .elite-prose h2, .elite-prose h3) {
    color: white;
    font-weight: 900;
    line-height: 1.3;
    margin-top: 2.5rem;
    margin-bottom: 1.25rem;
    letter-spacing: -0.02em;
  }
  
  :global(.elite-prose h1) { font-size: 1.875rem; }
  :global(.elite-prose h2) { font-size: 1.5rem; }
  :global(.elite-prose h3) { font-size: 1.25rem; }

  :global(.elite-prose p) {
    margin-bottom: 1.5rem;
  }

  :global(.elite-prose strong, .elite-prose b) {
    color: white;
    font-weight: 700;
  }

  :global(.elite-prose ul) {
    list-style-type: disc;
    padding-left: 1.5rem;
    margin-bottom: 1.5rem;
  }

  :global(.elite-prose ol) {
    list-style-type: decimal;
    padding-left: 1.5rem;
    margin-bottom: 1.5rem;
  }

  :global(.elite-prose li) {
    margin-bottom: 0.75rem;
  }
  
  :global(.elite-prose li::marker) {
    color: rgba(255, 255, 255, 0.4);
  }

  :global(.elite-prose a) {
    color: #3b82f6;
    text-decoration: underline;
    text-underline-offset: 4px;
    transition: color 0.2s;
  }

  :global(.elite-prose a:hover) {
    color: #60a5fa;
  }

  :global(.elite-prose img) {
    max-width: 100%;
    height: auto;
    border-radius: 16px;
    margin: 2rem 0;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
  }
  
  :global(.elite-prose blockquote) {
    border-left: 4px solid #3b82f6;
    padding: 1.5rem;
    font-style: italic;
    color: rgba(255,255,255,0.7);
    margin: 2rem 0;
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
    border-radius: 0 12px 12px 0;
  }
  
  :global(.elite-prose table) {
    width: 100%;
    margin-bottom: 2rem;
    border-collapse: collapse;
  }

  :global(.elite-prose th, .elite-prose td) {
    padding: 1rem;
    border: 1px solid rgba(255,255,255,0.1);
    text-align: left;
  }

  :global(.elite-prose th) {
    background: rgba(255,255,255,0.05);
    font-weight: 700;
    color: white;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }
</style>
