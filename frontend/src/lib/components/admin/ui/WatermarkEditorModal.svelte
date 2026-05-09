<script lang="ts">
  import { fade, scale } from 'svelte/transition';
  import Check from "@lucide/svelte/icons/check";
  import Maximize2 from "@lucide/svelte/icons/maximize-2";
  import Move from "@lucide/svelte/icons/move";
  import Type from "@lucide/svelte/icons/type";
  import ImageIcon from "@lucide/svelte/icons/image";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
import X from "@lucide/svelte/icons/x";
  import { mediaStore } from '$lib/state/media.svelte';
  import type { MediaAsset } from '$lib/state/types';
  import { resolveMediaUrl, resolveThumbnailUrl } from '$lib/state/utils';
  import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
  import { portal } from '$lib/core/actions/portal';

  import { useNanobot } from '$lib/state/nanobot.svelte';
  const nanobot = useNanobot();

  const onClose = () => nanobot.closeWatermarkEditor();

  // Runes for watermark state
  let logoX = $state(0.8); 
  let logoY = $state(0.8);
  let logoScale = $state(0.12);
  
  let textX = $state(0.1);
  let textY = $state(0.1);
  let textScale = $state(0.05);
  
  let activeLayer = $state<'logo' | 'text' | null>(null);
  let isDragging = $state(false);
  let containerWidth = $state(0);
  let containerHeight = $state(0);
  let imgRef = $state<HTMLImageElement | null>(null);

  // Logo metadata
  const LOGO_SRC = "/uploads/img/logo_transparent.webp";
  let logoRatio = $state(1);

  $effect(() => {
    if (nanobot.watermarkEditor.show) {
      const img = new Image();
      img.src = LOGO_SRC;
      img.onload = () => {
        logoRatio = img.width / img.height;
      };
      
      // Default positions if not set
      if (!nanobot.watermarkEditor.text) {
          nanobot.watermarkEditor.text = "";
          nanobot.watermarkEditor.textEnabled = false;
      }
    }
  });

  function startDragging(layer: 'logo' | 'text') {
    activeLayer = layer;
    isDragging = true;
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isDragging || !activeLayer) return;
    
    const rect = document.getElementById('watermark-canvas')?.getBoundingClientRect();
    if (!rect) return;
    
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    if (activeLayer === 'logo') {
      const scale = logoScale;
      logoX = Math.max(0, Math.min(1 - scale, x - (scale / 2)));
      logoY = Math.max(0, Math.min(1 - (scale / logoRatio), y - ((scale / logoRatio) / 2)));
    } else {
      const scale = textScale;
      // Text width is dynamic, but for dragging we use a normalized 20% width assumption for the handle
      textX = Math.max(0, Math.min(0.98, x - 0.1)); 
      textY = Math.max(0, Math.min(0.98, y - 0.02));
    }
  }

  function handleMouseUp() {
    isDragging = false;
    activeLayer = null;
  }

  function resetAll() {
      logoX = 0.8; logoY = 0.8; logoScale = 0.12;
      textX = 0.1; textY = 0.1; textScale = 0.05;
      nanobot.watermarkEditor.logoEnabled = true;
      nanobot.watermarkEditor.textEnabled = false;
      nanobot.watermarkEditor.text = "";
  }

  function confirm() {
    nanobot.watermarkEditor.onApply?.({
      logo_enabled: nanobot.watermarkEditor.logoEnabled,
      logo_x: logoX,
      logo_y: logoY,
      logo_scale: logoScale,
      text: nanobot.watermarkEditor.textEnabled ? nanobot.watermarkEditor.text : null,
      text_x: textX,
      text_y: textY,
      text_scale: textScale,
      text_color: nanobot.watermarkEditor.textColor
    });
  }
</script>

{#if nanobot.watermarkEditor.show}
  {@const asset = nanobot.watermarkEditor.asset || mediaStore.assets.find(a => a.id === nanobot.watermarkEditor.assetId)}
  {#if asset}
    <div
      use:portal
      class="fixed inset-0 bg-black/95 backdrop-blur-2xl flex items-center justify-center p-4 sm:p-12"
      style="z-index: {Z_INDEX_ADMIN.SUPREME_POWER};"
      transition:fade
      onmousemove={handleMouseMove}
      onmouseup={handleMouseUp}
      role="presentation"
    >
      <div 
        class="relative w-full max-w-6xl bg-[#0c0e14] rounded-[2.5rem] border border-white/10 shadow-2xl flex flex-col md:flex-row overflow-hidden h-[90vh]"
        transition:scale={{ start: 0.95, duration: 400 }}
      >
        <!-- Left Sidebar: Controls -->
        <div class="w-full md:w-80 border-r border-white/5 flex flex-col shrink-0 bg-[#08090d]">
            <div class="p-6 border-b border-white/5 flex items-center gap-3">
                <div class="p-2 bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-500/20">
                    <Maximize2 size={18} />
                </div>
                <div>
                  <h2 class="text-xs font-black uppercase tracking-[0.2em] text-white">Editor Phân Tầng</h2>
                  <p class="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mt-1">Logo & Văn bản Neural</p>
                </div>
            </div>

            <div class="flex-1 overflow-y-auto p-6 space-y-8">
                <!-- Layer 1: Logo -->
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <ImageIcon size={14} class="text-indigo-400" />
                            <span class="text-[10px] font-black uppercase tracking-wider text-zinc-300">Logo Thương Hiệu</span>
                        </div>
                        <button 
                            onclick={() => nanobot.watermarkEditor.logoEnabled = !nanobot.watermarkEditor.logoEnabled}
                            class="w-8 h-4 rounded-full relative transition-colors {nanobot.watermarkEditor.logoEnabled ? 'bg-indigo-600' : 'bg-zinc-800'}"
                        >
                            <div class="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-all {nanobot.watermarkEditor.logoEnabled ? 'translate-x-4' : 'translate-x-0'}"></div>
                        </button>
                    </div>

                    {#if nanobot.watermarkEditor.logoEnabled}
                    <div class="space-y-3 pl-2 border-l border-indigo-500/20" transition:fade>
                        <div class="flex items-center justify-between text-[9px] font-bold text-zinc-500 uppercase">
                            <span>Kích thước logo</span>
                            <span class="text-indigo-400 font-mono">{Math.round(logoScale * 100)}%</span>
                        </div>
                        <input type="range" min="0.05" max="0.4" step="0.01" bind:value={logoScale} class="w-full h-1 bg-zinc-800 rounded-full appearance-none accent-indigo-500" />
                    </div>
                    {/if}
                </div>

                <!-- Layer 2: Text -->
                <div class="space-y-4 pt-4 border-t border-white/5">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <Type size={14} class="text-emerald-400" />
                            <span class="text-[10px] font-black uppercase tracking-wider text-zinc-300">Văn bản Overlay</span>
                        </div>
                        <button 
                            onclick={() => nanobot.watermarkEditor.textEnabled = !nanobot.watermarkEditor.textEnabled}
                            class="w-8 h-4 rounded-full relative transition-colors {nanobot.watermarkEditor.textEnabled ? 'bg-emerald-600' : 'bg-zinc-800'}"
                        >
                            <div class="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-all {nanobot.watermarkEditor.textEnabled ? 'translate-x-4' : 'translate-x-0'}"></div>
                        </button>
                    </div>

                    {#if nanobot.watermarkEditor.textEnabled}
                    <div class="space-y-4 pl-2 border-l border-emerald-500/20" transition:fade>
                        <div class="space-y-2">
                            <label class="text-[9px] font-bold text-zinc-500 uppercase">Nội dung (SĐT/Domain)</label>
                            <input 
                                type="text" 
                                bind:value={nanobot.watermarkEditor.text} 
                                placeholder="Ví dụ: 0909.123.456" 
                                class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder:text-zinc-700 focus:outline-none focus:border-emerald-500/50"
                            />
                        </div>

                        <div class="space-y-3">
                            <div class="flex items-center justify-between text-[9px] font-bold text-zinc-500 uppercase">
                                <span>Cỡ chữ</span>
                                <span class="text-emerald-400 font-mono">{Math.round(textScale * 1000)}pt</span>
                            </div>
                            <input type="range" min="0.02" max="0.15" step="0.005" bind:value={textScale} class="w-full h-1 bg-zinc-800 rounded-full appearance-none accent-emerald-500" />
                        </div>

                        <div class="flex items-center justify-between">
                            <span class="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Màu sắc</span>
                            <div class="flex gap-2">
                                {#each ['#FFFFFF', '#FFD700', '#FF3366', '#33FF66'] as color}
                                    <button 
                                        onclick={() => nanobot.watermarkEditor.textColor = color}
                                        class="w-5 h-5 rounded-full border-2 transition-transform active:scale-90 {nanobot.watermarkEditor.textColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent opacity-50'}"
                                        style="background-color: {color}"
                                    ></button>
                                {/each}
                            </div>
                        </div>
                    </div>
                    {/if}
                </div>
            </div>

            <!-- Sidebar Footer: Reset -->
            <div class="p-6 border-t border-white/5">
                <button 
                    onclick={resetAll}
                    class="w-full py-3 flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
                >
                    <RotateCcw size={14} />
                    Đặt lại mặc định
                </button>
            </div>
        </div>

        <!-- Right Side: Canvas -->
        <div class="flex-1 flex flex-col relative bg-black">
            <!-- Canvas Header -->
            <div class="px-8 py-4 border-b border-white/5 flex items-center justify-between bg-black/40 backdrop-blur-md z-10">
                <span class="text-[9px] font-mono text-zinc-500 uppercase tracking-[0.3em]">Neural Preview Engine // V2.2</span>
                <button onclick={onClose} class="text-zinc-500 hover:text-white transition-colors"><X size={18} /></button>
            </div>

            <!-- Canvas Container -->
            <div class="flex-1 relative flex items-center justify-center overflow-hidden p-8 sm:p-12">
                <div class="relative shadow-[0_0_100px_rgba(0,0,0,0.8)] border border-white/10 group select-none">
                  <!-- Base Image -->
                  <img
                    id="watermark-canvas-img"
                    src={resolveThumbnailUrl(asset)}
                    alt="Preview"
                    class="max-w-full max-h-[60vh] object-contain block rounded-lg"
                    bind:this={imgRef}
                  />

                  <!-- Draggable Workspace (Fits image exactly) -->
                  <div 
                    id="watermark-canvas"
                    class="absolute inset-0 cursor-crosshair"
                    bind:clientWidth={containerWidth}
                    bind:clientHeight={containerHeight}
                  >
                    <!-- Draggable Logo Layer -->
                    {#if nanobot.watermarkEditor.logoEnabled}
                    <div 
                      class="absolute cursor-move group/logo transition-shadow"
                      style="
                        left: {logoX * 100}%; 
                        top: {logoY * 100}%; 
                        width: {logoScale * 100}%;
                        filter: drop-shadow(0 10px 20px rgba(0,0,0,0.5));
                        z-index: 20;
                      "
                      onmousedown={(e) => { e.stopPropagation(); startDragging('logo'); }}
                      role="presentation"
                    >
                       <img 
                         src={LOGO_SRC} 
                         alt="Logo" 
                         class="w-full h-auto opacity-90 border-2 border-dashed {activeLayer === 'logo' ? 'border-indigo-500 scale-105 shadow-[0_0_30px_rgba(99,102,241,0.4)]' : 'border-transparent group-hover/logo:border-white/30'} transition-all"
                         draggable="false"
                       />
                    </div>
                    {/if}

                    <!-- Draggable Text Layer -->
                    {#if nanobot.watermarkEditor.textEnabled && nanobot.watermarkEditor.text}
                    <div 
                      class="absolute cursor-move font-bold whitespace-nowrap p-2 group/text rounded"
                      style="
                        left: {textX * 100}%; 
                        top: {textY * 100}%; 
                        font-size: {textScale * containerWidth}px;
                        color: {nanobot.watermarkEditor.textColor};
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
                        z-index: 30;
                        border: 2px dashed {activeLayer === 'text' ? '#10b981' : 'transparent'};
                        background: {activeLayer === 'text' ? 'rgba(16,185,129,0.1)' : 'transparent'};
                      "
                      onmousedown={(e) => { e.stopPropagation(); startDragging('text'); }}
                      role="presentation"
                    >
                      {nanobot.watermarkEditor.text}
                    </div>
                    {/if}
                  </div>
                </div>
            </div>

            <!-- Canvas Footer -->
            <div class="px-8 py-6 bg-gradient-to-t from-black to-transparent flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="flex flex-col">
                        <span class="text-[9px] font-black text-indigo-400/80 uppercase tracking-widest">Tọa độ Neuron</span>
                        <span class="text-[10px] font-mono text-zinc-500 uppercase tracking-tighter">X:{Math.round(logoX*100)} Y:{Math.round(logoY*100)} // T:{Math.round(textX*100)}:{Math.round(textY*100)}</span>
                    </div>
                </div>

                <div class="flex items-center gap-3">
                    <button 
                         onclick={onClose}
                         class="px-8 py-4 text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] hover:text-white transition-all"
                    >
                        Hủy bỏ
                    </button>
                    <button 
                        onclick={confirm}
                        class="px-10 py-4 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] shadow-xl shadow-indigo-500/20 hover:scale-[1.05] active:scale-95 transition-all flex items-center gap-3"
                    >
                        <Check size={16} />
                        XÁC NHẬN ĐÓNG DẤU
                    </button>
                </div>
            </div>
        </div>
      </div>
    </div>
    {/if}
  {/if}

<style>
  /* Custom slider styling fallback */
  input[type='range']::-webkit-slider-thumb {
    appearance: none;
    width: 14px;
    height: 14px;
    background: #6366f1;
    border-radius: 50%;
    border: 2px solid #fff;
    cursor: pointer;
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);
  }
</style>
