<script lang="ts">
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import ImageSlot from "./ImageSlot.svelte";
  import { dndzone } from "svelte-dnd-action";
  import { flip } from "svelte/animate";
  import { Sparkles, LayoutGrid, Upload } from "lucide-svelte";
  import { untrack } from "svelte";
  let { onPurge }: { onPurge?: (asset: MediaAsset) => void } = $props();

  const flipDurationMs = 300;

  // CNS V75: Local state for DND to prevent 'parentElement' crashes caused by rapid reactivity
  let items = $state([...xohiImageStore.secondaryAssets]);

  // CNS V75.1: Sync store to local items with untrack to prevent reactive loops
  $effect(() => {
    const storeAssets = xohiImageStore.secondaryAssets;
    untrack(() => {
      // CNS V76: Use shallow length & id check instead of heavy JSON.stringify
      const isDifferent =
        items.length !== storeAssets.length ||
        items.some((item, i) => item.id !== storeAssets[i]?.id);

      if (isDifferent) {
        items = [...storeAssets];
      }
    });
  });

  function handleDndConsider(e: CustomEvent<{ items: MediaAsset[] }>) {
    items = e.detail.items;
  }

  function handleDndFinalize(e: CustomEvent<{ items: MediaAsset[] }>) {
    items = e.detail.items;
    // CNS V75.2: Only sync to global store at the very end of the gesture
    xohiImageStore.reorderAssets(items.map((i) => String(i.id)));
  }
</script>

<!-- Main Asset Highlight (Master Section) -->
{#if xohiImageStore.primaryAsset}
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
    <!-- Master Slot -->
    <div class="lg:col-span-3 xl:col-span-3 space-y-3">
      <div class="flex items-center justify-between px-2">
        <div class="flex items-center gap-2">
          <span
            class="text-[10px] font-black text-blue-400 uppercase tracking-[0.3em]"
            >Ảnh đại diện chính</span
          >
          <div class="w-1 h-1 rounded-full bg-blue-500/50"></div>
        </div>
        <Sparkles size={14} class="text-blue-500/30" />
      </div>
      <div
        class="p-0.5 rounded-[1.8rem] bg-gradient-to-b from-blue-500/10 to-transparent border border-blue-500/20 shadow-2xl overflow-hidden"
      >
        <ImageSlot asset={xohiImageStore.primaryAsset} index={0} {onPurge} />
      </div>
      <p
        class="text-[7.5px] text-white/40 font-bold uppercase tracking-[0.2em] px-3 italic leading-relaxed"
      >
        Primary focal point // Thumbnail selection
      </p>
    </div>

    <!-- Secondary Assets Grid (Slaves) -->
    <div class="lg:col-span-9 xl:col-span-9 space-y-3">
      <div class="flex items-center justify-between px-2">
        <div class="flex items-center gap-2">
          <span
            class="text-[10px] font-black text-white/40 uppercase tracking-[0.3em]"
            >Hình ảnh bổ sung</span
          >
          <span
            class="text-[8px] font-black text-white/10 uppercase bg-white/5 px-2 py-0.5 rounded-full"
            >Kéo để sắp xếp</span
          >
        </div>
        <span class="text-[10px] font-mono text-white/20 italic tracking-widest"
          >Số lượng: {xohiImageStore.secondaryAssets.length}</span
        >
      </div>

      <!-- CNS V74: Persistent container for dndzone to prevent 'parentElement' crashes -->
      <section
        class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 xl:grid-cols-6 gap-3 outline-none max-h-[40vh] md:max-h-[50vh] overflow-y-auto p-4 bg-black/20 rounded-[1.5rem] border border-white/5 shadow-inner custom-scrollbar"
        use:dndzone={{
          items: items,
          flipDurationMs,
          dropTargetStyle: { outline: "none" },
          type: "secondary",
        }}
        onconsider={handleDndConsider}
        onfinalize={handleDndFinalize}
      >
        {#each items as asset, i (asset.id)}
          <div animate:flip={{ duration: flipDurationMs }}>
            <ImageSlot {asset} index={i + 1} {onPurge} />
          </div>
        {/each}

        {#if items.length === 0}
          <div
            class="col-span-full flex flex-col items-center justify-center py-12 opacity-20 pointer-events-none gap-3"
          >
            <LayoutGrid size={32} />
            <p class="text-[10px] font-black uppercase tracking-[0.4em]">
              Danh sách trống
            </p>
          </div>
        {/if}
      </section>
    </div>
  </div>
{:else}
  <!-- Empty State Cyberpunk (Persistent structure) -->
  <div
    class="flex flex-col items-center justify-center py-24 border border-dashed border-white/10 rounded-[3rem] bg-white/[0.01] transition-all hover:bg-white/[0.02] group relative overflow-hidden"
  >
    <div
      class="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
    ></div>
    <div
      class="relative w-24 h-24 bg-blue-500/5 rounded-[2rem] flex items-center justify-center mb-8 border border-blue-500/10 group-hover:scale-110 group-hover:border-blue-500/30 transition-all duration-700 shadow-2xl"
    >
      <Upload
        size={40}
        class="text-blue-500/20 group-hover:text-blue-400 group-hover:drop-shadow-[0_0_15px_rgba(59,130,246,0.5)] transition-all"
      />
    </div>
    <p
      class="text-white/40 font-black text-[11px] uppercase tracking-[0.5em] mb-2 scale-x-110"
    >
      Chưa có hình ảnh
    </p>
    <p
      class="text-[9px] text-white/10 font-mono uppercase tracking-[0.2em] italic"
    >
      Vùi lòng tải ảnh lên hoặc dán link ảnh...
    </p>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }
  .custom-scrollbar:hover::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.2);
  }
</style>
