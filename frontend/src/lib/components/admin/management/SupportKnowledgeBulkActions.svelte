<script lang="ts">
    import { supportKbAdmin as kb } from '$lib/state/admin/supportKnowledge.svelte';
    import Trash2 from "@lucide/svelte/icons/trash-2";
    import Power from "@lucide/svelte/icons/power";
    import PowerOff from "@lucide/svelte/icons/power-off";
    import X from "@lucide/svelte/icons/x";
    import { fade, fly } from "svelte/transition";

    let selectedCount = $derived(kb.selectedIds.length);
</script>

{#if selectedCount > 0}
  <div 
    class="fixed bottom-12 left-1/2 -translate-x-1/2 z-[var(--z-admin-bulk-actions)] pointer-events-none"
    in:fly={{ y: 20, duration: 400 }}
    out:fade
  >
    <div class="pointer-events-auto flex items-center gap-6 px-6 py-4 bg-[#050505]/90 backdrop-blur-2xl border border-cyan-500/20 rounded-2xl shadow-[0_25px_60px_rgba(0,0,0,0.9)] ring-1 ring-cyan-500/10">
      <!-- Info Zone -->
      <div class="flex items-center gap-3 pr-6 border-r border-cyan-500/10">
        <div class="w-10 h-10 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center relative overflow-hidden">
            <div class="absolute inset-0 bg-cyan-400/5 animate-pulse"></div>
            <span class="text-xs font-black text-cyan-400 relative z-10">{selectedCount}</span>
        </div>
        <div class="flex flex-col">
            <span class="text-[10px] font-black text-white tracking-tighter">Neuron_Selected</span>
            <span class="text-[8px] font-bold text-cyan-500/50 tracking-widest leading-none mt-0.5">Batch_Buffer_Active</span>
        </div>
      </div>

      <!-- Action Nexus -->
      <div class="flex items-center gap-3">
        <button
          onclick={() => kb.bulkToggleActive(true)}
          class="flex items-center gap-2 px-4 py-2.5 hover:bg-cyan-500/10 text-gray-400 hover:text-cyan-400 rounded-xl transition-all text-[10px] font-black tracking-widest group border border-transparent hover:border-cyan-500/20"
        >
          <Power size={14} class="opacity-50 group-hover:opacity-100 text-cyan-400" />
          Neural_On
        </button>

        <button
          onclick={() => kb.bulkToggleActive(false)}
          class="flex items-center gap-2 px-4 py-2.5 hover:bg-red-500/10 text-gray-400 hover:text-red-400 rounded-xl transition-all text-[10px] font-black tracking-widest group border border-transparent hover:border-red-500/20"
        >
          <PowerOff size={14} class="opacity-50 group-hover:opacity-100 text-red-500" />
          Neural_Off
        </button>

        <div class="w-px h-8 bg-white/10 mx-1"></div>

        <button
          onclick={kb.bulkDelete}
          class="flex items-center gap-2 px-5 py-3 bg-red-600/10 hover:bg-red-600 text-red-500 hover:text-white font-black text-[10px] tracking-widest rounded-xl border border-red-600/30 hover:border-red-600 transition-all shadow-[0_0_20px_rgba(220,38,38,0.2)] group"
        >
          <Trash2 size={14} class="opacity-70 group-hover:opacity-100" />
          PURGE_NEURONS
        </button>
      </div>

      <!-- Close Action -->
      <button 
        onclick={() => kb.selectedIds = []}
        class="ml-2 p-2 hover:bg-white/5 rounded-full text-gray-600 hover:text-white transition-all border border-transparent hover:border-white/5"
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
        0%, 100% { border-color: rgba(6, 182, 212, 0.2); box-shadow: 0 25px 60px rgba(0,0,0,0.9); }
        50% { border-color: rgba(6, 182, 212, 0.4); box-shadow: 0 25px 60px rgba(6, 182, 212, 0.05); }
    }
    div.pointer-events-auto {
        animation: subtle-breath 4s infinite ease-in-out;
    }
</style>
