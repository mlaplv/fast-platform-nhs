<script lang="ts">
  import type { Product } from '$lib/types';
  import { X, ShieldCheck, Info } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { portal } from '$lib/core/actions/portal';

  let { active = $bindable(), product }: { active: boolean, product: Product } = $props();

  // Drag-to-Close Logic
  let dragY = $state(0);
  let isDragging = $state(false);
  let startY = 0;
  let contentRef = $state<HTMLElement | null>(null);

  // Elite V2.2: Reset scroll position when opening to ensure starting at top
  $effect(() => {
    if (active && contentRef) {
      contentRef.scrollTop = 0;
    }
  });

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
    class="mobile-overlay border-none outline-none"
    style:--drag-opacity-reduce={active ? Math.min(dragY / 400, 0.5) : 0}
    class:active
    class:dragging={isDragging}
    onclick={close}
    aria-label="Đóng overlay"
  ></button>

  <div
    class="mobile-modal-base"
    class:active
    class:dragging={isDragging}
    style:--drag-y={active ? dragY + 'px' : '100%'}
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

    <!-- Close Button (Elegant Ghost - Elite V2.2) -->
    <button
      onclick={close}
      class="absolute right-6 top-6 text-white/30 hover:text-white transition-all z-[1100] active:scale-75 outline-none border-none bg-transparent"
      aria-label="Đóng"
    >
      <X size={22} strokeWidth={1.2} />
    </button>

    <!-- Header: Sticky at the top -->
    <div class="relative flex items-center justify-center px-6 pb-2 pt-1 border-b border-white/5 bg-[#0a0a0a] shrink-0 z-header">
      <h2 class="text-[12px] font-black uppercase tracking-[0.2em] italic text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 py-2 flex items-center gap-2">
        <Info class="w-4 h-4 text-emerald-400" />
        Thông tin sản phẩm
      </h2>
    </div>

    <!-- Scrollable Description Body -->
    <div 
      bind:this={contentRef}
      class="px-6 py-6 overflow-y-auto custom-scrollbar flex-1 relative elite-prose select-text"
    >
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
  /* Elite Prose Typography - VIRAL 2026 PREMIUM EDITION */
  .elite-prose {
    font-family: 'Be Vietnam Pro', sans-serif;
    font-size: 15px;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.7);
    text-align: left; /* 🚀 CRITICAL FIX: Stops the "chuối" justified text gaps */
    word-break: break-word;
    letter-spacing: -0.01em;
  }

  /* Premium Headings with Sapphire-to-Emerald Gradient */
  :global(.elite-prose h1, .elite-prose h2, .elite-prose h3) {
    font-family: 'Be Vietnam Pro', sans-serif;
    color: white;
    font-weight: 950;
    line-height: 1.2;
    margin-top: 2.5rem;
    margin-bottom: 1.25rem;
    letter-spacing: -0.03em;
    text-transform: uppercase;
    position: relative;
    width: fit-content;
  }
  
  :global(.elite-prose h1) { font-size: 1.4rem; }
  :global(.elite-prose h2) { 
    font-size: 1.15rem;
    color: #fff;
    border-left: 3px solid #00A3FF;
    padding-left: 14px;
    margin-left: -20px;
    background: linear-gradient(90deg, rgba(0, 163, 255, 0.1) 0%, transparent 100%);
    padding-top: 8px;
    padding-bottom: 8px;
  }
  
  :global(.elite-prose h3) { 
    font-size: 0.95rem; 
    letter-spacing: 0.05em;
    color: rgba(255, 255, 255, 0.9);
  }

  :global(.elite-prose p) {
    margin-bottom: 1.5rem;
    opacity: 0.85;
  }

  :global(.elite-prose strong, .elite-prose b) {
    color: #fff;
    font-weight: 800;
  }

  /* Viral Glowy Bullets */
  :global(.elite-prose ul) {
    list-style-type: none;
    padding-left: 0.5rem;
    margin-bottom: 2rem;
  }

  :global(.elite-prose li) {
    position: relative;
    padding-left: 1.75rem;
    margin-bottom: 1rem;
    line-height: 1.6;
  }

  :global(.elite-prose li::before) {
    content: '';
    position: absolute;
    left: 0;
    top: 0.6em;
    width: 6px;
    height: 6px;
    background: #00A3FF;
    border-radius: 50%;
    box-shadow: 0 0 12px #00A3FF, 0 0 4px #00A3FF;
  }

  :global(.elite-prose a) {
    color: #00A3FF;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.2s;
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
