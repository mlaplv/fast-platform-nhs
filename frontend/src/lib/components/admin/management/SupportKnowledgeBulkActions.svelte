<script lang="ts">
    import { supportKbAdmin as kb } from '$lib/state/admin/supportKnowledge.svelte';
    import Trash2 from "lucide-svelte/icons/trash-2";
    import Power from "lucide-svelte/icons/power";
    import PowerOff from "lucide-svelte/icons/power-off";
    import X from "lucide-svelte/icons/x";
    import { fade, fly } from "svelte/transition";

    let selectedCount = $derived(kb.selectedIds.length);
</script>

{#if selectedCount > 0}
  <div 
    class="fixed bottom-12 left-1/2 -translate-x-1/2 z-[150] pointer-events-none"
    in:fly={{ y: 20, duration: 400 }}
    out:fade
  >
    <div class="pointer-events-auto flex items-center gap-6 px-6 py-4 bg-black/80 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.8)] ring-1 ring-white/10">
      <!-- Info Zone -->
      <div class="flex items-center gap-3 pr-6 border-r border-white/10">
        <div class="w-10 h-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center relative overflow-hidden">
            <div class="absolute inset-0 bg-white/5 animate-pulse"></div>
            <span class="text-sm font-black text-white relative z-10">{selectedCount}</span>
        </div>
        <div class="flex flex-col">
            <span class="text-[10px] font-black text-gray-200 uppercase tracking-tighter">Neuron_Selected</span>
            <span class="text-[8px] font-bold text-gray-500 uppercase tracking-widest leading-none mt-0.5">Batch_Buffer_Active</span>
        </div>
      </div>

      <!-- Action Nexus -->
      <div class="flex items-center gap-3">
        <button
          onclick={() => kb.bulkToggleActive(true)}
          class="flex items-center gap-2 px-4 py-2.5 hover:bg-white/10 text-gray-400 hover:text-white rounded-xl transition-all text-[10px] font-black uppercase tracking-widest group border border-transparent hover:border-white/10"
        >
          <Power size={14} class="opacity-50 group-hover:opacity-100 text-green-500" />
          Neural_On
        </button>

        <button
          onclick={() => kb.bulkToggleActive(false)}
          class="flex items-center gap-2 px-4 py-2.5 hover:bg-white/10 text-gray-400 hover:text-white rounded-xl transition-all text-[10px] font-black uppercase tracking-widest group border border-transparent hover:border-white/10"
        >
          <PowerOff size={14} class="opacity-50 group-hover:opacity-100 text-red-500" />
          Neural_Off
        </button>

        <div class="w-px h-8 bg-white/10 mx-1"></div>

        <button
          onclick={kb.bulkDelete}
          class="flex items-center gap-2 px-5 py-3 bg-red-500/20 hover:bg-red-600 text-red-400 hover:text-white font-black text-[10px] uppercase tracking-widest rounded-xl border border-red-500/20 hover:border-red-600 transition-all shadow-lg group"
        >
          <Trash2 size={14} class="opacity-70 group-hover:opacity-100" />
          PURGE_NEURONS
        </button>
      </div>

      <!-- Close Action -->
      <button 
        onclick={() => kb.selectedIds = []}
        class="ml-2 p-2 hover:bg-white/10 rounded-full text-gray-500 hover:text-white transition-all border border-transparent hover:border-white/5"
        title="Clear Selection"
      >
        <X size={16} />
      </button>
    </div>
  </div>
{/if}

<style>
    /* Premium touch: subtle breathing effect for the container */
    @keyframes subtle-breath {
        0%, 100% { border-color: rgba(255, 255, 255, 0.1); }
        50% { border-color: rgba(255, 255, 255, 0.2); }
    }
    div.pointer-events-auto {
        animation: subtle-breath 4s infinite ease-in-out;
    }
</style>
