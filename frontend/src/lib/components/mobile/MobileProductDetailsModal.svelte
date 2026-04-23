<script lang="ts">
  import type { Product } from '$lib/types';
  import { X, ShieldCheck, Info, Volume2, VolumeX } from 'lucide-svelte';
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

  // 🎙️ TTS: MASTER STREAM (Elite V4.0 - Professional Standard)
  // Uses MediaSource for a single, continuous, gap-free stream.
  let isReading: boolean = $state(false);
  let isBuffering: boolean = $state(false);
  let currentAudio: HTMLAudioElement | null = $state(null);
  let mediaSource: MediaSource | null = null;
  let sourceBuffer: SourceBuffer | null = null;
  let abortController: AbortController | null = null;

  async function toggleSpeech(): Promise<void> {
    if (isReading || isBuffering) {
      stopSpeech();
      return;
    }

    const text: string = contentRef?.innerText || "";
    if (!text) return;

    isBuffering = true;
    
    try {
      abortController = new AbortController();
      const res: Response = await fetch('/api/v1/client/tts/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 4000) }),
        signal: abortController.signal
      });

      if (!res.ok) throw new Error("Connection failed");
      const reader: ReadableStreamDefaultReader<Uint8Array> | undefined = res.body?.getReader();
      if (!reader) throw new Error("No stream body");

      // Initialize Native Audio Element
      const audio: HTMLAudioElement = new Audio();
      currentAudio = audio;
      
      // Setup MediaSource Pipeline
      mediaSource = new MediaSource();
      audio.src = URL.createObjectURL(mediaSource);

      mediaSource.addEventListener('sourceopen', async () => {
        if (!mediaSource) return;
        
        // Elite R2: Force MPEG-1 Audio Layer III (Standard MP3)
        sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
        
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              if (mediaSource && mediaSource.readyState === 'open') {
                mediaSource.endOfStream();
              }
              break;
            }
            
            if (value && sourceBuffer) {
              // Append chunk to buffer with state-check
              if (!sourceBuffer.updating) {
                sourceBuffer.appendBuffer(value);
              } else {
                await new Promise<void>(resolve => sourceBuffer?.addEventListener('updateend', () => resolve(), { once: true }));
                if (sourceBuffer) sourceBuffer.appendBuffer(value);
              }

              // R4.0 Auto-Resume
              if (audio.paused && isBuffering) {
                audio.play().catch(() => {});
              }
            }
          }
        } catch (err) {
          console.error('[TTS] Stream error:', err);
        }
      });

      audio.onplay = () => {
        isBuffering = false;
        isReading = true;
      };

      audio.onended = () => cleanup();
      audio.onerror = () => cleanup();

    } catch (e: any) {
      if (e.name !== 'AbortError') {
        console.error('[TTS] Master Stream Error:', e);
      }
      cleanup();
    }
  }

  function stopSpeech(): void {
    cleanup();
  }

  function cleanup() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.src = "";
      currentAudio = null;
    }
    if (mediaSource && mediaSource.readyState === 'open') {
      try { mediaSource.endOfStream(); } catch(e) {}
    }
    mediaSource = null;
    sourceBuffer = null;
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

      <!-- 🎙️ READ ALOUD BUTTON (Left) -->
      <button
        onclick={toggleSpeech}
        class="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2 px-3 py-2 rounded-full transition-all active:scale-95 {isReading || isBuffering ? 'bg-[#FFB7C5]/20 text-[#FFB7C5]' : 'text-white/20'}"
        aria-label={isReading ? "Dừng đọc" : "Đọc thông tin"}
      >
        {#if isBuffering}
          <div class="w-4 h-4 border-2 border-[#FFB7C5] border-t-transparent rounded-full animate-spin"></div>
          <span class="text-[8px] font-black uppercase tracking-widest italic">...</span>
        {:else if isReading}
          <VolumeX size={16} class="animate-pulse" />
          <span class="text-[8px] font-black uppercase tracking-widest italic">Dừng</span>
        {:else}
          <Volume2 size={16} />
          <span class="text-[8px] font-black uppercase tracking-widest italic">Nghe</span>
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
      class="px-4 py-6 overflow-y-auto custom-scrollbar flex-1 relative elite-prose select-text"
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
    <div class="shrink-0 flex items-center justify-center px-4 py-4 border-t border-white/5 bg-[#0a0a0a]">
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
    font-size: 14px;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.7);
    text-align: left !important;
    word-break: break-word;
    letter-spacing: -0.01em;
  }

  /* Premium Headings with Sapphire-to-Emerald Gradient */
  :global(.elite-prose h1, .elite-prose h2, .elite-prose h3) {
    font-family: 'Be Vietnam Pro', sans-serif;
    color: white;
    font-weight: 950;
    line-height: 1.2;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    letter-spacing: -0.03em;
    text-transform: uppercase;
    position: relative;
    width: fit-content;
  }
  
  :global(.elite-prose h1) { font-size: 1.2rem; }
  :global(.elite-prose h2) { 
    font-size: 1.05rem;
    color: #fff;
    border-left: 3px solid #FFB7C5;
    padding-left: 12px;
    margin-left: -16px;
    background: linear-gradient(90deg, rgba(255, 183, 197, 0.1) 0%, transparent 100%);
    padding-top: 6px;
    padding-bottom: 6px;
  }
  
  :global(.elite-prose h3) { 
    font-size: 0.95rem; 
    letter-spacing: 0.05em;
    color: rgba(255, 255, 255, 0.9);
  }

  :global(.elite-prose p) {
    margin-bottom: 1rem;
    opacity: 0.8;
  }

  :global(.elite-prose strong, .elite-prose b) {
    color: #fff;
    font-weight: 800;
  }

  /* Viral Glowy Bullets */
  :global(.elite-prose ul) {
    list-style-type: none;
    padding-left: 0;
    margin-bottom: 1.5rem;
  }

  :global(.elite-prose li) {
    position: relative;
    padding-left: 1.5rem;
    margin-bottom: 0.75rem;
    line-height: 1.5;
  }

  :global(.elite-prose li::before) {
    content: '';
    position: absolute;
    left: 0;
    top: 0.5em;
    width: 6px;
    height: 6px;
    background: #FFB7C5;
    border-radius: 50%;
    box-shadow: 0 0 10px #FFB7C5;
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
    margin: 1rem 0;
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
</style>
