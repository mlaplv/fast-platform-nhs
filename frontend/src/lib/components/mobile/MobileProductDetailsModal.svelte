<script lang="ts">
  import type { Product } from '$lib/types';
  import { X, ShieldCheck, Info } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  import { portal } from '$lib/core/actions/portal';
  
  let { active = $bindable(), product }: { active: boolean, product: Product } = $props();

  // Drag-to-Close Logic
  let dragY = $state(0);
  let isDragging = $state(false);
  let startY = 0;

  function onPointerDown(e: PointerEvent) {
    isDragging = true;
    startY = e.clientY;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!isDragging) return;
    const delta = e.clientY - startY;
    if (delta > 0) dragY = delta;
    else dragY = delta * 0.2; // Tension when pulling up
  }

  function onPointerUp(e: PointerEvent) {
    if (!isDragging) return;
    isDragging = false;
    if (dragY > 120) {
      close();
    }
    dragY = 0;
  }

  function close() { 
    active = false;
  }
</script>

<div use:portal class="mobile-product-details-modal">
  <button
    type="button"
    class="mobile-bottom-sheet-bg border-none outline-none"
    style:z-index={Z_INDEX_CLIENT.OVERLAY}
    style:opacity={active ? 1 - Math.min(dragY / 400, 0.5) : 0}
    style:transition={isDragging ? 'none' : 'opacity 0.4s fade'}
    style:pointer-events={active ? 'auto' : 'none'}
    style:position="fixed"
    style:inset="0"
    style:background="rgba(0,0,0,0.6)"
    style:backdrop-filter="blur(8px)"
    onclick={close}
    aria-label="Đóng overlay"
  ></button>

  <div
    class="mobile-bottom-sheet bg-[#0a0a0a] text-white border-t border-white/10 flex flex-col shadow-[0_-20px_80px_rgba(0,0,0,0.9)] rounded-t-[32px] h-[85dvh] overflow-hidden fixed bottom-0 left-0 right-0 w-full"
    style:z-index={Z_INDEX_CLIENT.MODAL}
    style:padding-bottom="env(safe-area-inset-bottom, 24px)"
    style:transform="translateY({active ? dragY + 'px' : '100%'})"
    style:transition={isDragging ? 'none' : 'transform 0.5s cubic-bezier(0.23, 1, 0.32, 1)'}
    style:pointer-events={active ? 'auto' : 'none'}
    role="dialog"
    aria-modal="true"
  >
    <!-- Drag Handle -->
    <div 
      class="w-full flex justify-center pt-3 pb-2 relative touch-none cursor-grab active:cursor-grabbing border-b border-white/5 shrink-0"
      onpointerdown={onPointerDown}
      onpointermove={onPointerMove}
      onpointerup={onPointerUp}
      onpointercancel={onPointerUp}
    >
      <div class="w-10 h-1 bg-white/10 rounded-full"></div>
    </div>

    <!-- Close Button -->
    <button 
      onclick={close} 
      class="absolute right-0 top-0 w-12 h-12 flex items-center justify-center text-white/20 hover:text-white transition-all z-20 active:scale-90 active:bg-white/5 rounded-tr-[inherit]"
      aria-label="Đóng"
    >
      <X class="w-5 h-5" strokeWidth={1.5} />
    </button>

    <!-- Header: Sticky at the top -->
    <div class="relative flex items-center justify-center px-6 pb-2 pt-1 border-b border-white/5 bg-[#0a0a0a] shrink-0">
      <h2 class="text-[12px] font-black uppercase tracking-[0.2em] italic text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 py-2 flex items-center gap-2">
        <Info class="w-4 h-4 text-emerald-400" />
        Thông tin sản phẩm
      </h2>
    </div>

    <!-- Scrollable Description Body -->
    <div class="px-6 py-6 overflow-y-auto custom-scrollbar flex-1 relative elite-prose">
      {#if product?.description}
        <!-- eslint-disable-next-line svelte/no-at-html-tags -->
        {@html product.description}
      {:else}
        <div class="flex flex-col items-center justify-center h-full text-white/30 space-y-4 pb-20">
          <ShieldCheck class="w-12 h-12 opacity-50" />
          <p class="text-xs uppercase tracking-widest font-bold">Chưa có thông tin mô tả chi tiết</p>
        </div>
      {/if}
    </div>

    <!-- Footer sticky -->
    <div class="shrink-0 flex items-center justify-center px-6 py-4 border-t border-white/5 bg-[#0a0a0a]">
      <div class="flex items-center gap-2 text-[9px] font-bold text-white/30 uppercase tracking-[0.25em] italic">
        <ShieldCheck class="w-3.5 h-3.5 text-blue-500/80" />
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-white/60 to-white/30">Hệ thống thông tin chính hãng</span>
      </div>
    </div>
  </div>
</div>

<style lang="postcss">
  /* Elite Prose Typography for Admin HTML content */
  .elite-prose {
    font-size: 15px;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.85);
  }

  /* Safe subset of prose styles to format arbitrary HTML gracefully in dark mode */
  :global(.elite-prose h1, .elite-prose h2, .elite-prose h3) {
    color: white;
    font-weight: 900;
    line-height: 1.3;
    margin-top: 2rem;
    margin-bottom: 1rem;
    letter-spacing: -0.02em;
  }
  
  :global(.elite-prose h1) { font-size: 1.5rem; }
  :global(.elite-prose h2) { font-size: 1.25rem; }
  :global(.elite-prose h3) { font-size: 1.125rem; }

  :global(.elite-prose p) {
    margin-bottom: 1.25rem;
  }

  :global(.elite-prose strong, .elite-prose b) {
    color: white;
    font-weight: 700;
  }

  :global(.elite-prose ul) {
    list-style-type: disc;
    padding-left: 1.25rem;
    margin-bottom: 1.25rem;
  }

  :global(.elite-prose ol) {
    list-style-type: decimal;
    padding-left: 1.25rem;
    margin-bottom: 1.25rem;
  }

  :global(.elite-prose li) {
    margin-bottom: 0.5rem;
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
    border-radius: 12px;
    margin: 1.5rem 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
  }
  
  :global(.elite-prose blockquote) {
    border-left: 3px solid #3b82f6;
    padding-left: 1rem;
    font-style: italic;
    color: rgba(255,255,255,0.7);
    margin: 1.5rem 0;
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
    padding: 1rem;
    border-radius: 0 8px 8px 0;
  }
  
  :global(.elite-prose table) {
    width: 100%;
    margin-bottom: 1.5rem;
    border-collapse: collapse;
  }

  :global(.elite-prose th, .elite-prose td) {
    padding: 0.75rem;
    border: 1px solid rgba(255,255,255,0.1);
    text-align: left;
  }

  :global(.elite-prose th) {
    background: rgba(255,255,255,0.05);
    font-weight: 700;
    color: white;
  }
</style>
