<script lang="ts">
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { fade, scale } from "svelte/transition";
  import { Star, Trash2, Check, Crop, Square, Layout, Smartphone, Tablet, Sparkles } from "lucide-svelte";

  let { asset, index, isDndShadow = false }: { asset: MediaAsset, index: number, isDndShadow?: boolean } = $props();

  let showCropPresets = $state(false);
  let isCropping = $state(false);

  const isPrimary = $derived(asset.is_primary);

  let pendingPreset = $state<'square' | 'banner' | 'story' | 'feed' | null>(null);

  async function handleSmartCrop(preset: 'square' | 'banner' | 'story' | 'feed', mode: 'ai' | 'normal') {
    isCropping = true;
    showCropPresets = false;
    pendingPreset = null;
    await xohiImageStore.smartCrop(asset.id, preset, mode);
    isCropping = false;
  }
</script>

<div
  class="relative group aspect-square rounded-none overflow-hidden transition-all duration-500 shadow-2xl
         {isPrimary
            ? 'shadow-[0_0_30px_rgba(59,130,246,0.2)] scale-[1.02] z-10'
            : 'bg-white/[0.02]'}"
  class:opacity-50={isDndShadow}
  class:pointer-events-none={isCropping}
  in:scale={{ duration: 400, start: 0.95 }}
>
  <!-- Thumbnail -->
  <img
    src={asset.file_path}
    alt="Asset {index}"
    class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
    class:blur-sm={isCropping}
  />

  {#if isCropping}
    <div class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm" transition:fade>
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-[9px] font-black text-blue-400 uppercase tracking-widest animate-pulse">Processing...</span>
      </div>
    </div>
  {/if}

  <!-- CNS V76: Selection Confirmation Modal (Premium & Adaptive) -->
  {#if pendingPreset}
    <div 
      class="absolute inset-0 z-50 flex flex-col items-center justify-center p-2 overflow-hidden" 
      transition:fade={{ duration: 300 }}
    >
        <!-- Deep Glass Background with Animated Glow -->
        <!-- CNS V77: Removed Deep Glass Overlay per Sếp's request to keep image visible -->
        <div class="absolute -inset-[100%] bg-gradient-to-tr from-blue-500/10 via-transparent to-indigo-500/10 animate-[pulse_8s_infinite]"></div>
        
        <!-- Adaptive Floating Glass Card (Ultra-Minimalist) -->
        <div 
            class="relative w-[95%] max-w-[130px] p-2 rounded-[1.2rem] border border-white/10 bg-white/[0.05] shadow-[0_15px_40px_rgba(0,0,0,0.6)] flex flex-col items-center group/card"
            transition:scale={{ duration: 400, start: 0.9, opacity: 0 }}
        >
            <!-- Neon Accent Top -->
            <div class="absolute top-0 left-1/2 -translate-x-1/2 w-6 h-[1.5px] bg-gradient-to-r from-transparent via-blue-500 to-transparent shadow-[0_0_8px_#3b82f6]"></div>

            <div class="flex flex-col w-full gap-1.5 mt-1">
                <button 
                    class="relative overflow-hidden group/btn bg-blue-600/80 hover:bg-blue-600 border border-white/10 hover:border-blue-400 py-2 rounded-xl transition-all duration-300 hover:scale-[1.03] active:scale-95 shadow-lg"
                    onclick={() => handleSmartCrop(pendingPreset!, 'ai')}
                >
                    <div class="relative z-10 flex items-center justify-center gap-1.5">
                        <Sparkles size={10} class="text-blue-200 group-hover:text-white" />
                        <span class="text-[8px] font-black text-white uppercase tracking-wider">Smart AI</span>
                    </div>
                </button>

                <button 
                    class="bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 text-white/70 hover:text-white py-2 rounded-xl text-[8px] font-black uppercase tracking-wider transition-all hover:scale-[1.03] active:scale-95"
                    onclick={() => handleSmartCrop(pendingPreset!, 'normal')}
                >
                    Normal
                </button>

                <button 
                    class="mt-0.5 text-[7px] text-white/30 hover:text-white/60 font-black uppercase tracking-widest transition-colors"
                    onclick={() => pendingPreset = null}
                >
                    Cancel
                </button>
            </div>
        </div>
    </div>
  {/if}

  <!-- CNS V76: Logic Badge Display (Enhanced) -->
  <div class="absolute top-4 right-4 flex flex-col items-end gap-1.5 z-20">
      {#if asset.media_metadata?.ai_analyzed || asset.media_metadata?.focal_point}
        <div 
            class="bg-indigo-500/20 backdrop-blur-xl border border-indigo-500/40 px-3 py-1 rounded-full flex items-center gap-1.5"
            transition:scale
        >
            <div class="w-1 h-1 rounded-full bg-indigo-400 animate-pulse"></div>
            <span class="text-[7px] font-black text-indigo-100 uppercase tracking-widest">AI Optimized</span>
        </div>
      {:else if asset.dimensions && !isCropping}
        <div 
            class="bg-white/5 backdrop-blur-xl border border-white/10 px-3 py-1 rounded-full flex items-center gap-1.5"
            transition:scale
        >
            <span class="text-[7px] font-black text-white/40 uppercase tracking-widest">Standard</span>
        </div>
      {/if}
  </div>

  <!-- Badge Ảnh Chính (Master Indicator) -->
  {#if isPrimary}
    <div
      class="absolute top-3 left-3 flex items-center gap-1.5 bg-blue-500 text-white text-[9px] font-black px-2.5 py-1 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.5)] uppercase tracking-widest border border-white/20"
      transition:scale={{ duration: 300 }}
    >
      <Star size={10} fill="currentColor" />
      Master
    </div>
  {:else}
     <div class="absolute top-3 left-3 bg-black/40 backdrop-blur-md text-white/40 text-[9px] font-bold px-2 py-0.5 rounded-full border border-white/5">
        #{index + 1}
     </div>
  {/if}

  <!-- Modern Controls (Glassmorphism) -->
  <div class="absolute inset-0 bg-blue-900/20 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-2">
    {#if !showCropPresets}
      <div class="flex items-center justify-center gap-3" transition:fade>
        {#if !isPrimary}
          <button
            class="w-10 h-10 flex items-center justify-center bg-white/10 hover:bg-blue-500 rounded-2xl text-white backdrop-blur-xl border border-white/10 transition-all hover:scale-110"
            onclick={() => xohiImageStore.swapPrimary(asset.id)}
            title="Đẩy làm ảnh chính"
          >
            <Star size={18} />
          </button>
        {/if}

        <button
          class="w-10 h-10 flex items-center justify-center bg-white/10 hover:bg-amber-500 rounded-2xl text-white backdrop-blur-xl border border-white/10 transition-all hover:scale-110"
          onclick={() => showCropPresets = true}
          title="Crop & Optimize"
        >
          <Crop size={18} />
        </button>

        <button
          class="w-10 h-10 flex items-center justify-center bg-white/10 hover:bg-red-500 rounded-2xl text-white backdrop-blur-xl border border-white/10 transition-all hover:scale-110"
          onclick={() => xohiImageStore.removeAsset(asset.id)}
          title="Xóa ảnh"
        >
          <Trash2 size={18} />
        </button>
      </div>
    {:else}
      <div class="flex items-center justify-center gap-2 p-2 bg-black/60 rounded-3xl backdrop-blur-2xl border border-white/10 shadow-2xl" transition:scale>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'square'}
          title="1:1 Square"
        >
          <Square size={14} />
          <span class="text-[7px] font-bold mt-1 opacity-0 group-hover/p:opacity-100 transition-opacity">1:1</span>
        </button>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'banner'}
          title="16:9 Banner"
        >
          <Layout size={14} />
          <span class="text-[7px] font-bold mt-1 opacity-0 group-hover/p:opacity-100 transition-opacity">16:9</span>
        </button>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'story'}
          title="9:16 Story"
        >
          <Smartphone size={14} />
          <span class="text-[7px] font-bold mt-1 opacity-0 group-hover/p:opacity-100 transition-opacity">9:16</span>
        </button>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'feed'}
          title="4:5 Feed"
        >
          <Tablet size={14} />
          <span class="text-[7px] font-bold mt-1 opacity-0 group-hover/p:opacity-100 transition-opacity">4:5</span>
        </button>
        <div class="w-[1px] h-6 bg-white/10 mx-1"></div>
        <button
          class="w-9 h-9 flex items-center justify-center hover:bg-white/10 rounded-xl text-white/60 hover:text-white transition-all"
          onclick={() => showCropPresets = false}
          title="Hủy"
        >
          <Trash2 size={14} class="rotate-45" />
        </button>
      </div>
    {/if}
  </div>

  <!-- Selection Checkmark if Primary -->
  {#if isPrimary}
    <div class="absolute bottom-3 right-3 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white shadow-lg border border-white/20" transition:fade>
      <Check size={14} strokeWidth={4} />
    </div>
  {/if}

  <!-- Dimensions Indicator -->
  {#if asset.dimensions}
    <div class="absolute bottom-3 left-3 px-2 py-0.5 bg-black/40 backdrop-blur-md rounded-md border border-white/5 text-[8px] text-white/60 font-mono">
      {asset.dimensions}
    </div>
  {/if}
</div>
