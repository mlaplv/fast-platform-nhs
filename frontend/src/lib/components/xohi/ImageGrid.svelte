<script lang="ts">
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import ImageSlot from "./ImageSlot.svelte";
  import { dndzone } from "svelte-dnd-action";
  import { flip } from "svelte/animate";
  import { Upload, LayoutGrid, Sparkles } from "lucide-svelte";

  const flipDurationMs = 300;

  function handleDndConsider(e: CustomEvent<{ items: MediaAsset[] }>) {
    xohiImageStore.reorderAssets(e.detail.items.map(i => String(i.id)));
  }

  function handleDndFinalize(e: CustomEvent<{ items: MediaAsset[] }>) {
    xohiImageStore.reorderAssets(e.detail.items.map(i => String(i.id)));
  }
</script>

<div class="space-y-8">
  <!-- Header Control -->
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
        <LayoutGrid size={20} class="text-blue-400" />
      </div>
      <div>
        <h3 class="text-sm font-black text-white uppercase tracking-widest">Cấu trúc hình ảnh</h3>
        <p class="text-[10px] text-white/30 font-bold uppercase tracking-tight">Master-Slave Configuration // V15.3</p>
      </div>
    </div>

    <label class="cursor-pointer group relative">
      <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
      <div class="relative bg-white/5 hover:bg-white/10 border border-white/10 px-4 py-2 rounded-xl text-[11px] font-black text-white uppercase tracking-widest transition-all flex items-center gap-2">
        <Upload size={14} class="text-blue-400" />
        Tải ảnh lên
      </div>
      <input
        type="file"
        multiple
        accept="image/*"
        class="hidden"
        onchange={(e) => e.target.files && xohiImageStore.addImages(e.target.files)}
      />
    </label>
  </div>

  <!-- Main Asset Highlight (Master Section) -->
  {#if xohiImageStore.primaryAsset}
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Master Slot -->
      <div class="lg:col-span-4 xl:col-span-3 space-y-3">
        <div class="flex items-center justify-between px-1">
          <span class="text-[9px] font-black text-blue-400 uppercase tracking-[0.2em]">Neural Main Slot</span>
          <Sparkles size={12} class="text-blue-500/40" />
        </div>
        <div class="p-1 rounded-[2rem] bg-gradient-to-b from-blue-500/20 to-transparent border border-white/5 shadow-2xl">
          <ImageSlot asset={xohiImageStore.primaryAsset} index={0} />
        </div>
        <p class="text-[10px] text-white/20 font-medium italic px-2">Ảnh này sẽ được dùng làm thumbnail và ảnh đại diện chính của bài viết.</p>
      </div>

      <!-- Secondary Assets Grid (Slaves) -->
      <div class="lg:col-span-8 xl:col-span-9 space-y-3">
        <div class="flex items-center justify-between px-1">
          <span class="text-[9px] font-black text-white/40 uppercase tracking-[0.2em]">Visual Sequence (Drag to reorder)</span>
          <span class="text-[10px] font-mono text-white/20 italic">BUFFER_SIZE: {xohiImageStore.secondaryAssets.length}</span>
        </div>

        <section
          class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 outline-none min-h-[150px] p-4 bg-white/[0.02] rounded-3xl border border-white/5 shadow-inner"
          use:dndzone={{
            items: xohiImageStore.secondaryAssets,
            flipDurationMs,
            dropTargetStyle: { outline: 'none' },
            type: 'secondary'
          }}
          onconsider={handleDndConsider}
          onfinalize={handleDndFinalize}
        >
          {#each xohiImageStore.secondaryAssets as asset, i (asset.id)}
            <div animate:flip={{ duration: flipDurationMs }}>
              <ImageSlot {asset} index={i + 1} />
            </div>
          {/each}
        </section>
      </div>
    </div>
  {:else}
    <!-- Empty State Cyberpunk -->
    <div class="flex flex-col items-center justify-center py-24 border-2 border-dashed border-white/5 rounded-[3rem] bg-white/[0.01] transition-all hover:bg-white/[0.02] group">
      <div class="w-20 h-20 bg-blue-500/5 rounded-full flex items-center justify-center mb-6 border border-blue-500/10 group-hover:scale-110 transition-transform duration-500">
        <Upload size={32} class="text-blue-500/20 group-hover:text-blue-400/50 transition-colors" />
      </div>
      <p class="text-white/40 font-black text-xs uppercase tracking-[0.3em]">Hệ thống rỗng</p>
      <p class="text-[10px] text-white/10 mt-2 font-mono uppercase tracking-widest">Waiting for neural visual input...</p>
    </div>
  {/if}
</div>
