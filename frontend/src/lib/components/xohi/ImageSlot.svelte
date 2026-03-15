<script lang="ts">
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { fade, scale } from "svelte/transition";
  import { Star, Trash2, Check } from "lucide-svelte";

  let { asset, index, isDndShadow = false }: { asset: MediaAsset, index: number, isDndShadow?: boolean } = $props();

  const isPrimary = $derived(asset.is_primary);
</script>

<div
  class="relative group aspect-square rounded-2xl overflow-hidden border transition-all duration-500 shadow-2xl
         {isPrimary
            ? 'border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.2)] scale-[1.02] z-10'
            : 'border-white/5 hover:border-white/20 bg-white/[0.02]'}"
  class:opacity-50={isDndShadow}
  in:scale={{ duration: 400, start: 0.95 }}
>
  <!-- Thumbnail -->
  <img
    src={asset.url}
    alt="Asset {index}"
    class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
  />

  <!-- Gradient Overlay for contrast -->
  <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60"></div>

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
  <div class="absolute inset-0 bg-blue-900/20 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-4">
    {#if !isPrimary}
      <button
        class="w-10 h-10 flex items-center justify-center bg-white/10 hover:bg-blue-500 rounded-2xl text-white backdrop-blur-xl border border-white/10 transition-all hover:scale-110 hover:shadow-[0_0_20px_rgba(59,130,246,0.4)]"
        onclick={() => xohiImageStore.swapPrimary(asset.id)}
        title="Đẩy làm ảnh chính"
      >
        <Star size={18} />
      </button>
    {/if}

    <button
      class="w-10 h-10 flex items-center justify-center bg-white/10 hover:bg-red-500 rounded-2xl text-white backdrop-blur-xl border border-white/10 transition-all hover:scale-110 hover:shadow-[0_0_20px_rgba(239,68,68,0.4)]"
      onclick={() => xohiImageStore.removeAsset(asset.id)}
      title="Xóa ảnh"
    >
      <Trash2 size={18} />
    </button>
  </div>

  <!-- Selection Checkmark if Primary -->
  {#if isPrimary}
    <div class="absolute bottom-3 right-3 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white shadow-lg border border-white/20" transition:fade>
      <Check size={14} strokeWidth={4} />
    </div>
  {/if}
</div>
