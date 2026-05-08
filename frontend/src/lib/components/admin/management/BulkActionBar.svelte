<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Archive from "@lucide/svelte/icons/archive";
  import X from "@lucide/svelte/icons/x";
  import StatusDropdown from "./StatusDropdown.svelte";
  import { fade, fly } from "svelte/transition";
  import { CAMPAIGN_STATUS_MAP } from "$lib/constants/campaign";

  interface Props {
    selectedCount: number;
    onClear: () => void;
    onDeleteBulk: () => void;
    onArchiveBulk: () => void;
    onSetDefaultBulk: () => void;
    onStatusBulk: (status: string) => void;
    statusMap?: Record<string, { label: string; color: string; border: string }>;
    placeholder?: string;
  }

  let props = $props<Props>();

  // Default values handling for optional props
  const statusMap = $derived(props.statusMap || CAMPAIGN_STATUS_MAP);
  const placeholder = $derived(props.placeholder || "BULK_UPDATE...");
</script>

{#if props.selectedCount > 0}
  <div 
    class="fixed bottom-28 left-1/2 -translate-x-1/2 z-50 pointer-events-none"
    in:fly={{ y: 20, duration: 400 }}
    out:fade
  >
    <div class="pointer-events-auto flex items-center gap-6 px-6 py-4 bg-black/80 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] ring-1 ring-white/5">
      <!-- Info Zone -->
      <div class="flex items-center gap-3 pr-6 border-r border-white/10">
        <div class="w-8 h-8 rounded-full bg-neon-cyan/20 border border-neon-cyan/30 flex items-center justify-center">
            <span class="text-xs font-mono font-black text-neon-cyan">{props.selectedCount}</span>
        </div>
        <div class="flex flex-col">
            <span class="text-[10px] font-mono font-bold text-gray-200 uppercase tracking-tighter">Entities_Selected</span>
            <span class="text-[8px] font-mono text-gray-500 uppercase tracking-widest">Global_Buffer_Active</span>
        </div>
      </div>

      <!-- Action Nexus -->
      <div class="flex items-center gap-2">
        <button
          onclick={() => props.onArchiveBulk?.()}
          class="flex items-center gap-2 px-4 py-2 hover:bg-white/5 text-gray-400 hover:text-white rounded-lg transition-all text-[10px] font-bold uppercase tracking-wider group"
        >
          <Archive size={14} class="opacity-50 group-hover:opacity-100" />
          Archive
        </button>

        <button
          onclick={() => props.onSetDefaultBulk?.()}
          class="flex items-center gap-2 px-4 py-2 hover:bg-white/5 text-gray-400 hover:text-emerald-400 rounded-lg transition-all text-[10px] font-bold uppercase tracking-wider group"
        >
          <div class="w-2 h-2 rounded-full bg-emerald-500/20 border border-emerald-500/50 group-hover:bg-emerald-500 group-hover:shadow-[0_0_8px_rgba(16,185,129,0.5)] transition-all"></div>
          Set_Default
        </button>

        <button
          onclick={() => props.onDeleteBulk?.()}
          class="flex items-center gap-2 px-5 py-2.5 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white font-black text-[10px] uppercase tracking-widest rounded-xl border border-red-500/20 hover:border-red-500 transition-all shadow-lg shadow-red-500/10 group"
        >
          <Trash2 size={14} class="opacity-70 group-hover:opacity-100" />
          Purge_Batch
        </button>

        <div class="w-px h-8 bg-white/10 mx-2"></div>

        <div class="w-[200px]">
          <StatusDropdown 
            options={Object.keys(statusMap)}
            onSelect={props.onStatusBulk}
            {statusMap}
            placeholder={placeholder}
            variant="bulk"
          />
        </div>
      </div>

      <!-- Close Action -->
      <button 
        onclick={() => props.onClear?.()}
        class="ml-2 p-1.5 hover:bg-white/5 rounded-lg text-gray-500 hover:text-white transition-all"
        title="Clear Selection"
      >
        <X size={16} />
      </button>
    </div>
  </div>
{/if}

<style>
  @keyframes pulse-cyan {
    0%, 100% { box-shadow: 0 0 5px rgba(0, 255, 255, 0.2); }
    50% { box-shadow: 0 0 15px rgba(0, 255, 255, 0.4); }
  }
</style>
