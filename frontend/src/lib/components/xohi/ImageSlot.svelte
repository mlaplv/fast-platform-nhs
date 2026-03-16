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
  class="relative group aspect-square rounded-[2rem] overflow-hidden transition-all duration-700
         {isPrimary
            ? 'z-10 shadow-[0_20px_50px_rgba(59,130,246,0.3)] ring-1 ring-blue-500/50 scale-[1.03]'
            : 'bg-white/[0.03] shadow-[0_10px_30px_rgba(0,0,0,0.2)] hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)] hover:scale-[1.02]'}"
  class:opacity-50={isDndShadow}
  class:pointer-events-none={isCropping}
  in:scale={{ duration: 600, start: 0.9, opacity: 0 }}
>
  <!-- Tight Fit Image (No excessive padding) -->
  <div class="absolute inset-0">
    <img
        src={asset.file_path}
        alt="Asset {index}"
        class="w-full h-full object-cover transition-all duration-1000 ease-[cubic-bezier(0.23,1,0.32,1)] group-hover:scale-110"
        class:blur-md={isCropping || pendingPreset}
    />

    <!-- Minimal Liquid Overlay -->
    <div class="absolute inset-0 bg-gradient-to-tr from-black/60 via-transparent to-white/5 opacity-60"></div>
    
    {#if isCropping}
        <div class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-md" transition:fade>
            <div class="w-8 h-8 relative">
                <div class="absolute inset-0 border-2 border-blue-500/20 rounded-full"></div>
                <div class="absolute inset-0 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        </div>
    {/if}
  </div>

  <!-- Utilitarian Crop Modal (No redundant info) -->
  {#if pendingPreset}
    <div 
      class="absolute inset-0 z-50 flex flex-col items-center justify-center p-4 overflow-hidden" 
      transition:fade={{ duration: 300 }}
    >
        <div class="absolute inset-0 bg-black/40 backdrop-blur-[32px] saturate-[180%]"></div>
        
        <div 
            class="relative w-full max-w-[120px] p-4 rounded-[2.5rem] bg-white/[0.05] border border-white/10 shadow-2xl flex flex-col items-center gap-3"
            transition:scale={{ duration: 400, start: 0.8 }}
        >
            <button 
                class="w-full flex flex-col items-center gap-1.5 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 transition-all hover:scale-105 active:scale-95"
                onclick={() => handleSmartCrop(pendingPreset!, 'ai')}
            >
                <Sparkles size={16} class="text-white" />
                <span class="text-[8px] font-black text-white uppercase tracking-widest">Neural</span>
            </button>

            <button 
                class="w-full py-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 text-[8px] font-black text-white uppercase tracking-widest transition-all"
                onclick={() => handleSmartCrop(pendingPreset!, 'normal')}
            >
                Standard
            </button>

            <button 
                class="text-[7px] font-black text-white/30 hover:text-white/60 uppercase tracking-widest"
                onclick={() => pendingPreset = null}
            >
                Cancel
            </button>
        </div>
    </div>
  {/if}

  <!-- Status Badges (Compact & Fixed Position) -->
  <div class="absolute top-4 right-4 flex flex-col items-end gap-1.5 z-20">
      {#if asset.media_metadata?.ai_analyzed || asset.media_metadata?.focal_point}
        <div 
            class="bg-blue-500/20 backdrop-blur-3xl border border-blue-500/30 px-2 py-1 rounded-full flex items-center gap-1"
            transition:scale
        >
            <div class="w-1 h-1 rounded-full bg-blue-400 animate-pulse"></div>
            <span class="text-[6px] font-black text-blue-200 uppercase tracking-widest">AI</span>
        </div>
      {:else if asset.dimensions && !isCropping}
        <div 
            class="bg-white/5 backdrop-blur-3xl border border-white/10 px-2 py-1 rounded-full"
            transition:scale
        >
            <span class="text-[6px] font-black text-white/30 uppercase tracking-widest">Raw</span>
        </div>
      {/if}
  </div>

  <!-- Master Indication (Clean) -->
  <div class="absolute top-4 left-4 z-20">
    {#if isPrimary}
        <div
            class="flex items-center gap-1.5 bg-blue-600/80 backdrop-blur-xl text-white text-[8px] font-black px-2.5 py-1.5 rounded-xl border border-white/20 shadow-lg shadow-blue-500/20 uppercase tracking-widest"
            transition:scale
        >
            <Star size={10} fill="currentColor" />
            Master
        </div>
    {:else}
        <div class="bg-black/30 backdrop-blur-md text-white/40 text-[8px] font-black px-2 py-1 rounded-lg border border-white/5">
            {index + 1}
        </div>
    {/if}
  </div>

  <!-- Controls Overlay (Pure Functional) -->
  <div class="absolute inset-0 bg-blue-900/10 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-500 flex items-center justify-center">
    {#if !showCropPresets}
      <div class="flex items-center gap-4 p-4 rounded-[2.5rem] bg-black/40 backdrop-blur-2xl border border-white/5 shadow-2xl" transition:scale>
        {#if !isPrimary}
          <button
            class="w-10 h-10 flex items-center justify-center bg-white/5 hover:bg-blue-600 rounded-xl text-white transition-all hover:scale-110"
            onclick={() => xohiImageStore.swapPrimary(asset.id)}
          >
            <Star size={18} />
          </button>
        {/if}

        <button
          class="w-10 h-10 flex items-center justify-center bg-white/5 hover:bg-amber-600 rounded-xl text-white transition-all hover:scale-110"
          onclick={() => showCropPresets = true}
        >
          <Crop size={18} />
        </button>

        <button
          class="w-10 h-10 flex items-center justify-center bg-white/5 hover:bg-red-600 rounded-xl text-white transition-all hover:scale-110"
          onclick={() => xohiImageStore.removeAsset(asset.id)}
        >
          <Trash2 size={18} />
        </button>
      </div>
    {:else}
      <div class="grid grid-cols-2 gap-2 p-3 bg-black/60 rounded-[2rem] backdrop-blur-3xl border border-white/5" transition:scale>
        <button
          class="w-10 h-10 flex flex-col items-center justify-center hover:bg-blue-600 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'square'}
        >
          <Square size={14} />
          <span class="text-[7px] font-black mt-1 uppercase opacity-40">1:1</span>
        </button>
        <button
          class="w-10 h-10 flex flex-col items-center justify-center hover:bg-blue-600 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'banner'}
        >
          <Layout size={14} />
          <span class="text-[7px] font-black mt-1 uppercase opacity-40">16:9</span>
        </button>
        <button
          class="w-10 h-10 flex flex-col items-center justify-center hover:bg-blue-600 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'story'}
        >
          <Smartphone size={14} />
          <span class="text-[7px] font-black mt-1 uppercase opacity-40">9:16</span>
        </button>
        <button
          class="w-10 h-10 flex flex-col items-center justify-center hover:bg-blue-600 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'feed'}
        >
          <Tablet size={14} />
          <span class="text-[7px] font-black mt-1 uppercase opacity-40">4:5</span>
        </button>
        <button
          class="col-span-2 py-1.5 flex items-center justify-center hover:bg-white/10 rounded-lg text-white/30 hover:text-white transition-all border-t border-white/5 mt-1"
          onclick={() => showCropPresets = false}
        >
          <Trash2 size={14} class="rotate-45" />
        </button>
      </div>
    {/if}
  </div>

  <!-- Primary Indicator (Active Fit) -->
  {#if isPrimary}
    <div class="absolute bottom-4 right-4 w-7 h-7 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-xl shadow-blue-500/40 border border-white/20" transition:fade>
      <Check size={16} strokeWidth={4} />
    </div>
  {/if}
</div>
