<script lang="ts">
  import type { Product } from '$lib/types';
    import X from "@lucide/svelte/icons/x";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Info from "@lucide/svelte/icons/info";
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { portal } from '$lib/core/actions/portal';
  import { fade, scale } from 'svelte/transition';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
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
  let { active = $bindable(), product: propProduct } = $props();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : (propProduct || shopStore.product));

  function close() { 
    active = false;
  }
</script>

{#if active}
<div use:portal class="desktop-product-details-modal fixed inset-0 flex items-center justify-center p-6 md:p-12" style:z-index={Z_INDEX_CLIENT.MODAL}>
  <!-- Backdrop -->
  <button
    transition:fade={{ duration: 300 }}
    type="button"
    class="absolute inset-0 bg-black/60 backdrop-blur-md border-none outline-none cursor-default"
    onclick={close}
    aria-label="Đóng overlay"
  ></button>

  <!-- Modal Content -->
  <div
    transition:scale={{ duration: 400, start: 0.95, opacity: 0 }}
    class="relative w-full max-w-5xl h-fit max-h-[90vh] bg-[#0a0a0a] text-white border border-white/10 rounded-[32px] shadow-[0_40px_100px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col"
    role="dialog"
    aria-modal="true"
  >
    <!-- Close Button -->
    <button 
      onclick={close} 
      class="absolute right-6 top-6 w-10 h-10 flex items-center justify-center text-white/20 hover:text-white hover:bg-white/5 transition-all rounded-full" style="z-index: var(--z-content);"
      aria-label="Đóng"
    >
      <X class="w-6 h-6" strokeWidth={1.5} />
    </button>

    <!-- Header -->
    <div class="px-10 pt-10 pb-6 border-b border-white/5 bg-[#0a0a0a] shrink-0">
      <h2 class="text-[14px] font-black tracking-[0.3em] italic text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 flex items-center gap-3">
        <Info class="w-5 h-5 text-emerald-400" />
        Thông tin chi tiết sản phẩm
      </h2>
    </div>

    <!-- Scrollable Description Body -->
    <div class="px-10 py-8 overflow-y-auto custom-scrollbar flex-1 elite-prose">
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

    <!-- Footer -->
    <div class="px-10 py-6 border-t border-white/5 bg-[#0a0a0a] flex items-center justify-between">
      <div class="flex items-center gap-3 text-[10px] font-bold text-white/30 tracking-[0.3em] italic">
        <ShieldCheck class="w-4 h-4 text-blue-500/80" />
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-white/60 to-white/30">Hệ thống thông tin chính hãng Elite</span>
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
