<script lang="ts">
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { fade, scale } from "svelte/transition";
  import { Star, Trash2, Check, Crop, Square, Layout, Smartphone, Tablet, Sparkles, Flame } from "lucide-svelte";
  import { resolveMediaUrl } from "$lib/state/utils";
  import { vuiController } from "$lib/vui";

  let {
    asset, 
    index, 
    isDndShadow = false,
    onPurge,
    onSelect
  }: { 
    asset: MediaAsset, 
    index: number, 
    isDndShadow?: boolean,
    onPurge?: (asset: MediaAsset) => void,
    onSelect?: (url: string) => void
  } = $props();

  let showCropPresets = $state(false);
  let isCropping = $state(false);

  const isPrimary = $derived(asset.is_primary);
  const isLocal = $derived(
    asset.file_path && (
      asset.file_path.startsWith('/uploads/') ||
      asset.file_path.startsWith('uploads/') ||
      asset.file_path.startsWith('/static/') ||
      asset.file_path.startsWith('static/') ||
      (!asset.file_path.startsWith('http') && !asset.file_path.startsWith('//') && !asset.file_path.startsWith('blob:'))
    )
  );

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
  class="relative group aspect-square rounded-[1.5rem] overflow-hidden transition-all duration-700 shadow-2xl
         {isPrimary
            ? 'ring-2 ring-blue-500/50 shadow-[0_0_40px_rgba(59,130,246,0.3)] scale-[1.03] z-10'
            : 'bg-white/[0.02] border border-white/10 hover:border-white/20'}"
  class:opacity-50={isDndShadow}
  class:pointer-events-none={isCropping}
  in:scale={{ duration: 500, start: 0.98, opacity: 0 }}
>
  <!-- Thumbnail -->
  <img
    src={resolveMediaUrl(asset.file_path || asset.url)}
    alt="Asset {index}"
    class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
    class:blur-sm={isCropping}
  />

  {#if isCropping}
    <div class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm" transition:fade>
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-[9px] font-black text-blue-400 uppercase tracking-widest animate-pulse">Đang xử lý...</span>
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
                    onclick={() => pendingPreset && handleSmartCrop(pendingPreset, 'ai')}
                >
                    <div class="relative z-10 flex items-center justify-center gap-1.5">
                        <Sparkles size={10} class="text-blue-200 group-hover:text-white" />
                        <span class="text-[8px] font-black text-white uppercase tracking-wider">Cắt ảnh AI</span>
                    </div>
                </button>

                <button 
                    class="bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 text-white/70 hover:text-white py-2 rounded-xl text-[8px] font-black uppercase tracking-wider transition-all hover:scale-[1.03] active:scale-95"
                    onclick={() => { if (pendingPreset) handleSmartCrop(pendingPreset, 'normal'); }}
                >
                    Cắt thường
                </button>

                <button 
                    class="mt-0.5 text-[7px] text-white/30 hover:text-white/60 font-black uppercase tracking-widest transition-colors"
                    onclick={() => pendingPreset = null}
                >
                    Khác
                </button>
            </div>
        </div>
    </div>
  {/if}

  <!-- CNS V76: Logic Badge Display (Enhanced) -->
  <div class="absolute top-3 right-3 flex flex-col items-end gap-1.5 z-20">
      {#if asset.media_metadata?.ai_analyzed || asset.media_metadata?.focal_point}
        <div 
            class="bg-indigo-500/30 backdrop-blur-2xl border border-indigo-400/40 px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-lg"
            transition:scale
        >
            <div class="w-1 h-1 rounded-full bg-indigo-300 animate-pulse"></div>
            <span class="text-[7px] font-black text-indigo-50 uppercase tracking-[0.15em]">Tối ưu AI</span>
        </div>
      {:else if asset.dimensions && !isCropping}
        <div 
            class="bg-black/30 backdrop-blur-2xl border border-white/10 px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-md"
            transition:scale
        >
            <span class="text-[7px] font-black text-white/50 uppercase tracking-[0.15em]">Chuẩn</span>
        </div>
      {/if}
  </div>

  <!-- Badge Ảnh Chính (Master Indicator) -->
  {#if isPrimary}
    <div
      class="absolute top-3 left-3 flex items-center gap-1.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white text-[9px] font-black px-3 py-1.5 rounded-full shadow-[0_8px_20px_rgba(59,130,246,0.5)] uppercase tracking-[0.15em] border border-white/20"
      transition:scale={{ duration: 300 }}
    >
      <Star size={10} fill="currentColor" class="text-blue-100" />
      Ảnh chính
    </div>
  {:else}
     <div class="absolute top-3 left-3 bg-black/50 backdrop-blur-2xl text-white/60 text-[9px] font-black px-2.5 py-1 rounded-full border border-white/10 shadow-lg tracking-widest">
        #{index + 1}
     </div>
  {/if}

  <!-- Modern Controls (Minimalist Icon Ensemble) -->
  <div class="absolute inset-0 bg-black/40 backdrop-blur-[1px] opacity-0 group-hover:opacity-100 transition-all duration-500 flex items-center justify-center">
    {#if !showCropPresets}
      <div class="flex items-center justify-center gap-1.5 p-2 bg-black/40 rounded-2xl backdrop-blur-3xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] transition-all" transition:scale>
        {#if !isPrimary}
          <button
            class="p-2 text-white/40 hover:text-yellow-400 hover:bg-yellow-400/10 rounded-xl transition-all active:scale-95 group/star"
            onclick={() => xohiImageStore.swapPrimary(asset.id)}
            title="Đẩy làm ảnh chính"
          >
            <Star size={16} class="group-hover/star:fill-yellow-400" />
          </button>
        {/if}

        {#if onSelect}
          <button
            class="p-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-xl transition-all active:scale-95 shadow-lg shadow-indigo-500/20 group/select"
            onclick={(e) => { e.stopPropagation(); onSelect?.(resolveMediaUrl(asset.file_path || asset.url)); }}
            title="SỬ DỤNG ẢNH NÀY"
          >
            <Check size={16} strokeWidth={3} />
          </button>
        {/if}

        <button
          class="p-2 text-white/40 hover:text-blue-400 hover:bg-blue-400/10 rounded-xl transition-all active:scale-95"
          onclick={() => showCropPresets = true}
          title="Crop & Optimize"
        >
          <Crop size={16} />
        </button>

        <!-- Remove from Post Button (Soft Delete) -->
        <button
          class="p-2 text-white/40 hover:text-zinc-300 hover:bg-white/10 rounded-xl transition-all active:scale-95"
          onclick={(e) => { e.stopPropagation(); e.preventDefault(); xohiImageStore.removeAsset(asset.id); vuiController.speak("Dạ, đã gỡ ảnh rồi ạ."); }}
          title="Gỡ khỏi bài (Remove)"
        >
          <Trash2 size={16} />
        </button>

        {#if onPurge && isLocal}
          <div class="w-px h-4 bg-white/10 mx-0.5"></div>
          <!-- Purge Button (V78: Hard Delete) -->
          <button 
              class="relative overflow-hidden group/purge bg-red-500/10 hover:bg-red-500/30 border border-red-500/20 hover:border-red-500/50 p-2 rounded-xl transition-all duration-300 active:scale-90"
              onclick={(e) => { e.stopPropagation(); onPurge?.(asset); }}
              title="XOÁ TRIỆT ĐỂ (FILE LOCAL)"
          >
              <div class="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse shadow-[0_0_10px_#ef4444]"></div>
              <Flame size={16} class="text-red-400 group-hover/purge:text-red-200 group-hover/purge:scale-110 transition-all drop-shadow-[0_0_8px_rgba(239,68,68,0.4)]" />
          </button>
        {/if}
      </div>
    {:else}
      <div class="flex items-center justify-center gap-2 p-2 bg-black/60 rounded-3xl backdrop-blur-2xl border border-white/10 shadow-2xl" transition:scale>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'square'}
          title="Hình vuông (1:1)"
        >
          <Square size={14} />
          <span class="text-[7px] font-bold mt-1 opacity-0 group-hover/p:opacity-100 transition-opacity">1:1</span>
        </button>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'banner'}
          title="Ảnh nền (16:9)"
        >
          <Layout size={14} />
          <span class="text-[7px] font-bold mt-1 opacity-0 group-hover/p:opacity-100 transition-opacity">16:9</span>
        </button>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'story'}
          title="Dọc (9:16)"
        >
          <Smartphone size={14} />
          <span class="text-[7px] font-bold mt-1 opacity-0 group-hover/p:opacity-100 transition-opacity">9:16</span>
        </button>
        <button
          class="w-9 h-9 flex flex-col items-center justify-center hover:bg-blue-500 rounded-xl text-white transition-all group/p"
          onclick={() => pendingPreset = 'feed'}
          title="Tỉ lệ 4:5"
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
    <div class="absolute bottom-3 right-3 w-7 h-7 bg-blue-500 rounded-full flex items-center justify-center text-white shadow-[0_4px_15px_rgba(59,130,246,0.6)] border-2 border-slate-950/50" transition:scale>
      <Check size={16} strokeWidth={4} />
    </div>
  {/if}

  <!-- Dimensions Indicator -->
  {#if asset.dimensions}
    <div class="absolute bottom-3 left-3 px-2 py-1 bg-black/60 backdrop-blur-2xl rounded-lg border border-white/10 text-[8px] text-white/50 font-black tracking-widest uppercase shadow-md pointer-events-none group-hover:opacity-0 transition-opacity">
      {asset.dimensions}
    </div>
  {/if}
</div>
