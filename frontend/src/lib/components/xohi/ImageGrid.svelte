<script lang="ts">
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import ImageSlot from "./ImageSlot.svelte";
  import { dndzone } from "svelte-dnd-action";
  import { flip } from "svelte/animate";
  import { Upload, LayoutGrid, Sparkles } from "lucide-svelte";

  import { untrack } from "svelte";

  const flipDurationMs = 300;

  // CNS V75: Local state for DND to prevent 'parentElement' crashes caused by rapid reactivity
  let items = $state([...xohiImageStore.secondaryAssets]);

  // CNS V75.1: Sync store to local items with untrack to prevent reactive loops
  $effect(() => {
    const storeAssets = xohiImageStore.secondaryAssets;
    untrack(() => {
        if (JSON.stringify(items) !== JSON.stringify(storeAssets)) {
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
    xohiImageStore.reorderAssets(items.map(i => String(i.id)));
  }
</script>

<div class="space-y-10">
  <!-- Header Control (Liquid Refinement) -->
  <div class="flex items-center justify-between px-2">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-[1.25rem] bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shadow-lg shadow-indigo-500/5">
        <LayoutGrid size={24} class="text-indigo-400" />
      </div>
      <div>
        <h3 class="text-base font-black text-white uppercase tracking-[0.25em] drop-shadow-md">Neural Gallery</h3>
        <p class="text-[10px] text-white/20 font-black uppercase tracking-widest mt-0.5">Liquid Architecture // OS-26.V1</p>
      </div>
    </div>

    <label class="cursor-pointer group relative">
      <div class="absolute -inset-1 bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600 rounded-2xl blur-lg opacity-20 group-hover:opacity-60 transition duration-700"></div>
      <div class="relative bg-white/[0.03] hover:bg-white/[0.08] backdrop-blur-xl border border-white/10 px-6 py-3 rounded-2xl text-[11px] font-black text-white uppercase tracking-[0.2em] transition-all flex items-center gap-3 shadow-2xl">
        <Upload size={16} class="text-blue-400" />
        Upload Assets
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

  <!-- Main Asset Highlight (Liquid Compartment) -->
  {#if xohiImageStore.primaryAsset}
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Master Slot with Tight Wrapper -->
      <div class="lg:col-span-4 xl:col-span-3 space-y-4">
        <div class="flex items-center justify-between px-3">
          <span class="text-[9px] font-black text-blue-400 uppercase tracking-[0.4em]">Neural Master</span>
          <div class="w-1.5 h-1.5 rounded-full bg-blue-500/40 animate-ping"></div>
        </div>
        
        <!-- Tight Liquid Wrapper: p-1 for maximum image scale -->
        <div class="relative p-1 rounded-[2.2rem] bg-gradient-to-b from-blue-500/10 to-transparent border border-white/5 shadow-2xl group/master">
             <div class="absolute inset-0 bg-blue-500/5 rounded-[2.2rem] blur-2xl opacity-0 group-hover/master:opacity-100 transition-opacity duration-1000"></div>
             <ImageSlot asset={xohiImageStore.primaryAsset} index={0} />
        </div>
        
        <div class="px-5 py-3 rounded-2xl bg-white/[0.015] border border-white/5 backdrop-blur-sm">
            <p class="text-[8px] text-white/30 font-bold uppercase tracking-widest leading-relaxed">
                Primary neural endpoint. Dominates visual hierarchy.
            </p>
        </div>
      </div>

      <!-- Secondary Assets (Fluid Slave Container) -->
      <div class="lg:col-span-8 xl:col-span-9 space-y-4">
        <div class="flex items-center justify-between px-5">
          <span class="text-[9px] font-black text-white/30 uppercase tracking-[0.4em]">Secondary Clusters</span>
          <span class="text-[9px] font-mono text-white/10 italic tracking-tighter">VOL_SYNC: {xohiImageStore.secondaryAssets.length}</span>
        </div>

        <!-- Fluid Grid Container: Tight p-4 and gap-4 for maximum density -->
        <section
          class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 outline-none min-h-[200px] p-4 bg-white/[0.01] rounded-[2.5rem] border border-white/5 shadow-inner backdrop-blur-[12px]"
          use:dndzone={{
            items: items,
            flipDurationMs,
            dropTargetStyle: { outline: 'none' },
            type: 'secondary'
          }}
          onconsider={handleDndConsider}
          onfinalize={handleDndFinalize}
        >
          {#each items as asset, i (asset.id)}
            <div animate:flip={{ duration: flipDurationMs }}>
              <ImageSlot {asset} index={i + 1} />
            </div>
          {/each}

          {#if items.length === 0}
            <div class="col-span-full flex flex-col items-center justify-center py-12 opacity-5 grayscale scale-90">
               <LayoutGrid size={32} strokeWidth={1} />
               <p class="text-[9px] font-black uppercase tracking-[0.3em] mt-3">Buffer Empty</p>
            </div>
          {/if}
        </section>
      </div>
    </div>
  {:else}
    <!-- Empty State Liquid (Symmetry & Flow) -->
    <div class="flex flex-col items-center justify-center py-28 rounded-[3rem] bg-white/[0.01] border-2 border-dashed border-white/5 relative overflow-hidden group">
      <div class="absolute inset-0 bg-gradient-to-tr from-blue-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
      
      <div class="relative w-20 h-20 rounded-[2rem] bg-indigo-500/5 flex items-center justify-center mb-6 border border-white/5 transition-all duration-700 group-hover:scale-110">
        <Upload size={32} class="text-indigo-400 opacity-20 group-hover:opacity-60 transition-all" />
      </div>
      
      <div class="text-center relative z-10">
          <p class="text-white/40 font-black text-xs uppercase tracking-[0.4em] mb-2">Neural Link Inactive</p>
          <p class="text-[9px] text-white/10 font-mono tracking-[0.2em] uppercase">Ready for multiple asset injection...</p>
      </div>
    </div>
  {/if}
</div>
