<script lang="ts">
  import type { Product } from '$lib/types';
  import { X, ShieldCheck, Info, AudioLines, VolumeX } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { portal } from '$lib/core/actions/portal';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { ShoppingCart, ArrowRight } from 'lucide-svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { fly, fade } from 'svelte/transition';

  function isJson(str: string) {
    if (typeof str !== 'string') return false;
    try {
      const parsed = JSON.parse(str);
      return typeof parsed === 'object' && parsed !== null && ('hero_headline' in parsed || 'spec_bento' in parsed);
    } catch (e) {
      return false;
    }
  }

  let { active = $bindable(), product }: { active: boolean, product: Product } = $props();

  // Drag-to-Close Logic
  let dragY = $state(0);
  let isDragging = $state(false);
  let startY = 0;
  let contentRef = $state<HTMLElement | null>(null);
  let isAtBottom = $state(false);
  
  const shopStore = getShopStore();
  const cartStore = getCartStore();

  function handleScroll(e: Event) {
    if (!contentRef) return;
    const target = e.target as HTMLElement;
    // Check if within 100px of bottom
    isAtBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 100;
  }

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
    else dragY = delta * 0.2;
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

  // 🎙️ TTS: WEB AUDIO ENGINE (Elite V7.0 - OS-Codec-Free)
  // Uses AudioContext.decodeAudioData to bypass OS-level MP3 decoder requirements.
  // Compatible with Firefox/Linux (no gstreamer-ugly needed), Chrome, Safari.
  let isReading: boolean = $state(false);
  let isBuffering: boolean = $state(false);
  let abortController: AbortController | null = null;

  
  // R6.0 Memory State
  const CACHE_NAME: string = "osmo-tts-v2";
  let productSlug: string = $derived(product?.slug || "unknown");

  /**
   * Elite V7.1: TTS Text Sanitizer
   * Strips emojis, pictographs, and decorative Unicode that edge-tts reads aloud
   * as their Unicode description (e.g. ⚡ → "biển báo điện cao thế").
   */
  function sanitizeTtsText(raw: string): string {
    return raw
      // Strip all Emoji except digits/ASCII (Extended Pictographic)
      .replace(/\p{Extended_Pictographic}/gu, "")
      // Strip Miscellaneous Symbols & Dingbats blocks (☀ ★ ♦ etc.)
      .replace(/[\u2600-\u27BF]/g, "")
      // Strip enclosed/supplemental alphanumerics & symbols
      .replace(/[\u{1F000}-\u{1FFFF}]/gu, "")
      // Strip zero-width joiners & variation selectors left over
      .replace(/[\uFE00-\uFE0F\u200D]/g, "")
      // Strip English-only parenthetical labels: (The Hook), (CTA), (USP), (Hero), etc.
      // Vietnamese TTS reads these phonetically as gibberish ("thẻ hók")
      .replace(/\(\s*[A-Za-z][A-Za-z\s\-']{0,40}\s*\)/g, "")
      // Strip leading dash/hyphen left over after stripping parenthetical (e.g. "- ")
      .replace(/^\s*[-–—]\s*/gm, "")
      // Collapse multiple blank lines into single newline
      .replace(/\n{3,}/g, "\n\n")
      // Trim leading/trailing whitespace
      .trim();
  }

  let currentAudio: HTMLAudioElement | null = $state(null);

  async function toggleSpeech(): Promise<void> {
    if (isReading || isBuffering) {
      stopSpeech();
      return;
    }

    const rawText: string = contentRef?.innerText || "";
    const text: string = sanitizeTtsText(rawText);
    if (text.length < 10) return;

    isBuffering = true;

    try {
      let audioUrl = "";
      let usedCache = false;

      // 1. Check Cache
      const cache = await caches.open(CACHE_NAME);
      const cachedResponse = await cache.match(`/tts/${productSlug}`);
      
      if (cachedResponse) {
        const blob = await cachedResponse.blob();
        if (blob.size > 500 && blob.type.startsWith('audio/')) {
          audioUrl = URL.createObjectURL(blob);
          usedCache = true;
        } else {
          await cache.delete(`/tts/${productSlug}`);
        }
      }

      if (!usedCache) {
        // 2. Prepare Stream via POST (saves text to Redis)
        abortController = new AbortController();
        const prepRes: Response = await fetch('/api/v1/client/tts/prepare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text.slice(0, 20000) }),
          signal: abortController.signal
        });

        if (!prepRes.ok) throw new Error(`Prepare failed: ${prepRes.status}`);
        const { id } = await prepRes.json();
        if (!id) throw new Error('No stream ID returned');

        // 3. Native Streaming via GET endpoint
        // Browser natively streams chunked MP3 HTTP responses, working flawlessly on all browsers (incl. Firefox)
        audioUrl = `/api/v1/client/tts/stream?id=${id}`;
        
        // Note: Caching the full file is skipped here because it's a live native stream. 
        // We will cache it on the next page reload if needed, but native caching often handles it.
      }

      // 4. Play
      const audio = new Audio();
      audio.src = audioUrl;
      currentAudio = audio;

      audio.onplay = () => {
        isBuffering = false;
        isReading = true;
      };

      audio.onloadedmetadata = () => {
        const savedTime = localStorage.getItem(`tts_pos_${productSlug}`);
        if (savedTime) audio.currentTime = parseFloat(savedTime);
      };

      audio.ontimeupdate = () => {
        if (audio.currentTime > 0) {
          localStorage.setItem(`tts_pos_${productSlug}`, audio.currentTime.toString());
        }
      };

      audio.onended = () => {
        localStorage.removeItem(`tts_pos_${productSlug}`);
        localStorage.setItem(`tts_done_${productSlug}`, "true");
        cleanup();
      };
      
      audio.onerror = () => {
        caches.open(CACHE_NAME).then(c => c.delete(`/tts/${productSlug}`)).catch(() => {});
        cleanup();
      };

      await audio.play();

    } catch (e: unknown) {
      const err = e as Error;
      if (err?.name !== 'AbortError') console.error('[TTS] Error:', err);
      caches.open(CACHE_NAME).then(c => c.delete(`/tts/${productSlug}`)).catch(() => {});
      cleanup();
    }
  }

  function stopSpeech(): void {
    cleanup();
  }

  function cleanup(): void {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.ontimeupdate = null;
      currentAudio.onplay = null;
      currentAudio.onloadedmetadata = null;
      if (currentAudio.src.startsWith('blob:')) {
        URL.revokeObjectURL(currentAudio.src);
      }
      currentAudio.src = "";
      currentAudio = null;
    }
    isReading = false;
    isBuffering = false;
  }

  // Stop speech when modal closes

  let wasActive = false;
  $effect(() => {
    if (wasActive && !active) {
      stopSpeech();
    }
    wasActive = active;
  });
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
    <!-- 🚀 COMPACT HEADER (Elite V2.6) -->
    <div class="sticky top-0 w-full z-header bg-[#0a0a0a] border-b border-white/5 shrink-0">
      <!-- Minimalist Drag Handle -->
      <div 
        class="w-full flex justify-center pt-2.5 pb-1 touch-none cursor-grab active:cursor-grabbing"
        onpointerdown={onPointerDown}
        onpointermove={onPointerMove}
        onpointerup={onPointerUp}
        onpointercancel={onPointerUp}
      >
        <div class="w-8 h-[2px] bg-white/10 rounded-full"></div>
      </div>

      <!-- 🎙️ NEURAL VOICE CAPSULE (Elite V6.4 Lite) -->
      <button
        onclick={toggleSpeech}
        class="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 px-2.5 py-1.5 rounded-full transition-all duration-500 active:scale-90 {isReading || isBuffering ? 'bg-[#FFB7C5]/30 border-[#FFB7C5]/50 text-[#FFB7C5] shadow-[0_0_20px_rgba(255,183,197,0.4)]' : 'bg-white/10 border-white/20 text-white/80 shadow-[0_0_10px_rgba(255,255,255,0.05)]'} border backdrop-blur-md"
        aria-label={isReading ? "Dừng đọc" : "Đọc thông tin"}
      >
        {#if isBuffering}
          <div class="relative w-3 h-3">
            <div class="absolute inset-0 border-[1.5px] border-[#FFB7C5]/30 rounded-full"></div>
            <div class="absolute inset-0 border-[1.5px] border-[#FFB7C5] border-t-transparent rounded-full animate-spin"></div>
          </div>
          <span class="text-[7.5px] font-bold uppercase tracking-[0.2em] italic leading-none opacity-80">Wait</span>
        {:else if isReading}
          <div class="flex items-end gap-[1.5px] h-2.5 mb-[0.5px]">
            <div class="w-[1.5px] bg-[#FFB7C5] shadow-[0_0_5px_#FFB7C5] animate-voice-bar-1"></div>
            <div class="w-[1.5px] bg-[#FFB7C5] shadow-[0_0_5px_#FFB7C5] animate-voice-bar-2"></div>
            <div class="w-[1.5px] bg-[#FFB7C5] shadow-[0_0_5px_#FFB7C5] animate-voice-bar-3"></div>
          </div>
          <span class="text-[7.5px] font-black uppercase tracking-[0.2em] italic leading-none">Stop</span>
        {:else}
          <AudioLines size={12} class="text-white drop-shadow-[0_0_3px_rgba(255,255,255,0.5)]" />
          <span class="text-[7.5px] font-bold uppercase tracking-[0.2em] italic leading-none">
            {#if typeof window !== 'undefined' && localStorage.getItem(`tts_pos_${productSlug}`)}
              Resume
            {:else if typeof window !== 'undefined' && localStorage.getItem(`tts_done_${productSlug}`)}
              Replay
            {:else}
              Listen
            {/if}
          </span>
        {/if}
      </button>

      <!-- Compact Header Title Row -->
      <div class="flex items-center justify-center px-4 pb-2.5 pt-0">
        <h2 class="text-[10px] font-black uppercase tracking-[0.25em] italic text-transparent bg-clip-text bg-gradient-to-r from-[#FFB7C5] to-[#E8D5B0] flex items-center gap-1.5 py-1">
          <Info class="w-3 h-3 text-[#FFB7C5]" />
          Thông tin sản phẩm
        </h2>
      </div>

      <!-- Close Button (Elegant Integrated X) -->
      <button
        onclick={close}
        class="absolute right-3 top-1/2 -translate-y-1/2 text-white/20 hover:text-white transition-all p-2 active:scale-75 outline-none border-none bg-transparent"
        aria-label="Đóng"
      >
        <X size={18} strokeWidth={2} />
      </button>
    </div>

    <!-- Scrollable Description Body -->
    <div 
      bind:this={contentRef}
      onscroll={handleScroll}
      class="pl-[10px] pr-2.5 pt-2 pb-10 overflow-y-auto custom-scrollbar flex-1 relative elite-prose select-text"
    >
      {#if product?.description}
        {#if isJson(product.description)}
          <InteractiveDashboard data={product.description} compact={true} />
        {:else}
          <!-- eslint-disable-next-line svelte/no-at-html-tags -->
          {@html product.description}
        {/if}
      {:else}
        <div class="flex flex-col items-center justify-center h-full text-white/30 space-y-4 pb-20">
          <ShieldCheck class="w-12 h-12 opacity-50" />
          <p class="text-xs uppercase tracking-widest font-bold">Chưa có thông tin mô tả chi tiết</p>
        </div>
      {/if}
    </div>

    <!-- Footer sticky -->
    <div class="shrink-0 flex flex-col items-center justify-center px-4 py-4 border-t border-white/5 bg-[#0a0a0a] relative">
      {#if isAtBottom}
        <div class="absolute -top-16 left-0 right-0 px-4 pointer-events-none" in:fly={{ y: 20 }}>
           <button
             onclick={() => {
               active = false;
               shopStore.openCheckout(cartStore, product);
             }}
             class="w-full h-12 bg-gradient-to-r from-[#FFB7C5] to-[#E8D5B0] rounded-full flex items-center justify-between px-6 shadow-[0_0_30px_rgba(255,183,197,0.4)] pointer-events-auto active:scale-95 transition-all group"
           >
             <div class="flex flex-col items-start leading-none">
                <span class="text-[10px] font-black text-red-600 uppercase tracking-widest italic animate-pulse">Sắp hết suất ưu đãi</span>
                <span class="text-[14px] font-black text-black uppercase tracking-tight">NHẬN ƯU ĐÃI NGAY</span>
             </div>
             <div class="flex items-center gap-3">
                <div class="flex flex-col items-end">
                   <span class="text-[14px] font-black text-black leading-none">{formatCurrency(shopStore.totalAmount)}</span>
                   <span class="text-[8px] font-black text-black/40 uppercase tracking-tighter mt-0.5">Freeship</span>
                </div>
                <div class="w-8 h-8 rounded-full bg-black/10 flex items-center justify-center">
                   <ArrowRight size={16} class="text-black group-hover:translate-x-1 transition-transform" />
                </div>
             </div>
           </button>
        </div>
      {/if}

      <div class="flex items-center gap-2 text-[10px] font-bold text-white/30 uppercase tracking-[0.25em] italic">
        <ShieldCheck class="w-3.5 h-3.5 text-blue-500/80" />
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-white/60 to-white/30">Hệ thống thông tin chính hãng</span>
      </div>
    </div>
  </div>
</div>

<style lang="postcss">
  /* Elite Prose Typography - VIRAL 2026 PREMIUM EDITION */
  .elite-prose {
    font-family: var(--font-main);
    font-size: 15px;
    line-height: 1.5; /* Giảm độ giãn dòng để không bị hở */
    color: rgba(255, 255, 255, 0.95);
    text-align: left !important;
    word-break: break-word;
    letter-spacing: -0.01em;
  }

  /* 🏆 Premium Headings - VIRAL 2026 ELITE EDITION */
  :global(.elite-prose h1) {
    font-family: var(--font-main);
    font-size: 1.6rem;
    font-weight: 800; /* High-end Bold */
    line-height: 1.2; 
    margin-top: 0.5rem; /* Aggressively reduced */
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em; /* Relaxed for readability */
    color: #fff;
    text-transform: none; 
    position: relative;
    display: block;
    width: fit-content;
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
  }

  :global(.elite-prose h1::after) {
    content: '';
    display: block;
    width: 40px;
    height: 3px;
    background: linear-gradient(90deg, #FFB7C5, #E8D5B0);
    margin-top: 6px; /* Tightened */
    border-radius: 100px;
  }

  :global(.elite-prose h2, .elite-prose h3) {
    font-family: var(--font-main);
    color: white;
    font-weight: 800;
    line-height: 1.2;
    margin-top: 1.25rem; /* Reduced from 1.75rem */
    margin-bottom: 0.5rem;
    letter-spacing: -0.03em;
    text-transform: uppercase;
    position: relative;
    width: fit-content;
  }
  
  :global(.elite-prose h2) { 
    font-size: 1.05rem;
    color: #fff;
    border-left: 3px solid #FFB7C5;
    padding-left: 12px;
    margin-left: -15px;
    background: linear-gradient(90deg, rgba(255, 183, 197, 0.1) 0%, transparent 100%);
    padding-top: 6px;
    padding-bottom: 6px;
  }
  
  :global(.elite-prose h3) { 
    font-size: 0.9rem; 
    letter-spacing: 0.08em;
    color: rgba(255, 255, 255, 0.85);
    opacity: 0.9;
  }

  :global(.elite-prose p) {
    margin-bottom: 0.4rem; /* Tightened for specs-style layout */
    opacity: 1;
  }

  /* ⚡ Viral Fix: No gap after images */
  :global(.elite-prose img + *) {
    margin-top: 0 !important;
  }

  :global(.elite-prose > *:first-child) {
    margin-top: 0 !important;
  }

  :global(.elite-prose strong, .elite-prose b) {
    color: #fff;
    font-weight: 800;
  }

  /* Viral Glowy Bullets - ULTRA TIGHT RESET */
  :global(.elite-prose ul) {
    list-style-type: none !important;
    padding-left: 0 !important;
    margin-left: 0 !important;
    margin-bottom: 1rem;
  }

  :global(.elite-prose li) {
    position: relative;
    padding-left: 14px !important; /* Đủ rộng để chứa dấu chấm và một chút khoảng hở */
    margin-bottom: 0.3rem;
    line-height: 1.5;
    list-style: none !important;
  }

  :global(.elite-prose li::before) {
    content: '';
    position: absolute;
    left: 0; /* Đưa dấu chấm về lại bên trong để chắc chắn hiển thị */
    top: 0.55em;
    width: 3.5px;
    height: 3.5px;
    background: #FFB7C5;
    border-radius: 50%;
    box-shadow: 0 0 5px rgba(255, 183, 197, 0.5);
  }

  /* 🧪 iPhone Minimalist Scrollbar (Scoped to Modal) */
  :global(.mobile-modal-base::-webkit-scrollbar),
  :global(.custom-scrollbar::-webkit-scrollbar) {
    width: 2px !important;
    height: 2px !important;
  }
  
  :global(.mobile-modal-base::-webkit-scrollbar-thumb),
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) {
    background: rgba(255, 255, 255, 0.25) !important;
    border-radius: 100px !important;
  }

  :global(.mobile-modal-base),
  :global(.custom-scrollbar) {
    scrollbar-width: thin !important;
    scrollbar-color: rgba(255, 255, 255, 0.25) transparent !important;
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
    display: block; /* Eliminate baseline gap */
    max-width: 100%;
    height: auto;
    border-radius: 12px;
    margin: 0.25rem 0 0.5rem 0; /* Tight bottom margin */
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
  }
  
  :global(.elite-prose blockquote) {
    border-left: 3px solid #FFB7C5;
    padding-left: 1rem;
    font-style: italic;
    color: rgba(255, 255, 255, 0.7);
    margin: 1.5rem 0;
    background: linear-gradient(90deg, rgba(255, 183, 197, 0.1) 0%, transparent 100%);
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

  :global(.elite-prose th) {
    background: rgba(255,255,255,0.05);
    font-weight: 700;
    color: white;
  }

  /* 🎙️ Neural Voice Animations */
  @keyframes voice-bar {
    0%, 100% { height: 4px; }
    50% { height: 12px; }
  }

  .animate-voice-bar-1 { animation: voice-bar 0.6s infinite ease-in-out; }
  .animate-voice-bar-2 { animation: voice-bar 0.8s infinite ease-in-out 0.2s; }
  .animate-voice-bar-3 { animation: voice-bar 0.7s infinite ease-in-out 0.4s; }
</style>
