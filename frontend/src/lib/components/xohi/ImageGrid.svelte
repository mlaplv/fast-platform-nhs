<script lang="ts">
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import ImageSlot from "./ImageSlot.svelte";
  import { dndzone } from "svelte-dnd-action";
  import { flip } from "svelte/animate";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import Upload from "@lucide/svelte/icons/upload";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import { untrack } from "svelte";

  let {
    items = $bindable(),
    isProcessing = false,
    isExpanded = false,
    campaign_id,
    onSelect,
    handleImageError,
    onRemove,
    handleRetry
  }: {
    items: (MediaAsset | string)[];
    isProcessing?: boolean;
    isExpanded?: boolean;
    campaign_id: string;
    onSelect?: (url: string) => void;
    handleImageError?: (url: string) => void;
    onRemove?: (asset: MediaAsset) => void;
    handleRetry?: () => void;
  } = $props();

  const flipDurationMs = 300;
  let localItems = $state<(MediaAsset | string)[]>([]);

  // CNS V90: Primary asset is always the one with is_primary=true, or the first one if none set
  let primaryAsset = $derived(
    localItems.find(a => typeof a !== 'string' && a.is_primary) || 
    (localItems.length > 0 ? localItems[0] : null)
  );
  
  // CNS V91: Secondary items are everything EXCEPT the primary asset
  let secondaryItems = $derived(
    localItems.filter(item => item !== primaryAsset)
  );

  // CNS V75.1: Sync store to local items
  $effect(() => {
    if (items === undefined) {
      items = [];
      return;
    }
    // CNS V92: Track all critical reactive properties for deep synchronization
    const propItems = items;
    propItems.forEach(item => {
      if (typeof item === 'object' && item !== null) {
        item.is_primary;
        item.id;
        item.file_path;
      }
    });

    untrack(() => {
      const isDifferent = localItems.length !== propItems.length ||
        localItems.some((item, i) => {
          const id = typeof item === 'string' ? item : item.id;
          const propItem = propItems[i];
          const propId = typeof propItem === 'string' ? propItem : propItem?.id;
          const primaryChanged = typeof item !== 'string' && typeof propItem !== 'string' && 
                               item.is_primary !== propItem?.is_primary;
          return id !== propId || primaryChanged;
        });

      if (isDifferent) {
        localItems = [...propItems];
      }
    });
  });

  function handleDndConsider(e: CustomEvent<{ items: (MediaAsset | string)[] }>) {
    // Preserve primary at its current position, update others
    const newItems = [...localItems];
    const secondaryIdxs = localItems.map((item, i) => item !== primaryAsset ? i : -1).filter(i => i !== -1);
    
    e.detail.items.forEach((item, i) => {
      newItems[secondaryIdxs[i]] = item;
    });
    localItems = newItems;
  }

  function handleDndFinalize(e: CustomEvent<{ items: (MediaAsset | string)[] }>) {
    handleDndConsider(e);
    items = localItems;
  }
</script>

<!-- Main Asset Highlight (Master Section) -->
{#if xohiImageStore.assets.length > 0}
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
    <!-- Master Slot -->
    <div class="lg:col-span-3 xl:col-span-3 space-y-3">
      <div class="flex items-center justify-between px-2">
        <div class="flex items-center gap-2">
          <span
            class="text-[10px] font-black text-blue-400 tracking-[0.3em]"
            >Ảnh đại diện chính</span
          >
          <div class="w-1 h-1 rounded-full bg-blue-500/50"></div>
        </div>
        <Sparkles size={14} class="text-blue-500/30" />
      </div>
      <div
        class="p-0.5 rounded-[1.8rem] bg-gradient-to-b from-blue-500/10 to-transparent border border-blue-500/20 shadow-2xl overflow-hidden"
      >
        {#if primaryAsset}
          <ImageSlot asset={primaryAsset} index={localItems.indexOf(primaryAsset)} {onSelect} />
        {/if}
      </div>
      <p
        class="text-[7.5px] text-white/40 font-bold tracking-[0.2em] px-3 italic leading-relaxed"
      >
        Primary focal point // Thumbnail selection
      </p>
    </div>

    <!-- Secondary Assets Grid (Slaves) -->
    <div class="lg:col-span-9 xl:col-span-9 space-y-3">
      <div class="flex items-center justify-between px-2">
        <div class="flex items-center gap-2">
          <span
            class="text-[10px] font-black text-white/40 tracking-[0.3em]"
            >Hình ảnh bổ sung</span
          >
          <span
            class="text-[8px] font-black text-white/10 bg-white/5 px-2 py-0.5 rounded-full"
            >Kéo để sắp xếp</span
          >
        </div>
        <span class="text-[10px] font-mono text-white/20 italic tracking-widest"
          >Số lượng: {secondaryItems.length}</span
        >
      </div>

      <!-- CNS V74: Persistent container for dndzone -->
      <section
        class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 xl:grid-cols-6 gap-3 outline-none max-h-[40vh] md:max-h-[50vh] overflow-y-auto p-4 bg-black/20 rounded-[1.5rem] border border-white/5 shadow-inner custom-scrollbar"
        use:dndzone={{
          items: secondaryItems,
          flipDurationMs,
          dropTargetStyle: { outline: "none" },
          type: "secondary",
        }}
        onconsider={handleDndConsider}
        onfinalize={handleDndFinalize}
      >
        {#each secondaryItems as asset (typeof asset === 'string' ? asset : asset.id)}
          <div animate:flip={{ duration: 300 }} class="relative group">
            <ImageSlot
              {asset}
              index={localItems.indexOf(asset)}
              onSelect={onSelect}
              onRemove={onRemove}
              {handleImageError}
            />
          </div>
        {/each}

        {#if secondaryItems.length === 0}
          <div
            class="col-span-full flex flex-col items-center justify-center py-12 opacity-20 pointer-events-none gap-3"
          >
            <LayoutGrid size={32} />
            <p class="text-[10px] font-black tracking-[0.4em]">
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
      class="text-white/40 font-black text-[11px] tracking-[0.5em] mb-2 scale-x-110"
    >
      Chưa có hình ảnh
    </p>
    <p
      class="text-[9px] text-white/10 font-mono tracking-[0.2em] italic mb-6"
    >
      Vùi lòng tải ảnh lên hoặc dán link ảnh...
    </p>

    {#if handleRetry}
      <div class="flex flex-col items-center gap-4 bg-white/[0.02] p-6 rounded-[2rem] border border-white/5 backdrop-blur-sm shadow-inner">
        <div class="text-center">
            <p class="text-[10px] font-black text-white/40 tracking-[0.2em]">Không tìm thấy ảnh phù hợp</p>
            <p class="text-[8px] text-white/20 tracking-widest mt-1">Quota Google Search có thể đã hết, hoặc từ khóa quá ít phổ biến.</p>
        </div>
        <button onclick={handleRetry} class="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 text-[9px] font-black tracking-widest transition-all active:scale-95 shadow-lg group/retry">
            <RotateCcw size={12} class="group-hover/retry:rotate-[-45deg] transition-transform" /> 
            Tìm lại ảnh
        </button>
      </div>
    {/if}
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
