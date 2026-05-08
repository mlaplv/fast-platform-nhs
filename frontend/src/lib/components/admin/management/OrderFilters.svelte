<script lang="ts">
  import Search from "@lucide/svelte/icons/search";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Check from "@lucide/svelte/icons/check";
  import { ORDER_STATUS_MAP } from "$lib/constants/order";

  let {
    searchInput = $bindable(),
    activeFilter = $bindable(),
    pageSize = $bindable(),
    totalOrders,
    isLoading,
    isAllSelected,
    onRefresh,
    onSearchInput,
    onToggleSelectAll,
  }: {
    searchInput: string;
    activeFilter: string;
    pageSize: number;
    totalOrders: number;
    isLoading: boolean;
    isAllSelected: boolean;
    onRefresh: () => void;
    onSearchInput: (e: Event) => void;
    onToggleSelectAll: () => void;
  } = $props();

  const filters = [
    "all",
    "pending",
    "packed",
    "shipping",
    "delivered",
    "cancelled",
  ];
</script>

<!-- FINAL ATOMIC CONSOLIDATION (Elite V2.2) -->
<div
  class="sticky top-0 bg-[#050505]/95 backdrop-blur-2xl border-t border-white/5 border-b border-neon-cyan/10 px-2 h-8 flex flex-row flex-nowrap items-center gap-2 shrink-0 shadow-[0_4px_30px_rgba(0,0,0,0.5)] overflow-hidden"
  style="z-index: var(--z-sticky_header);"
>
  <!-- 1. Master Selector -->
  <div 
    class="shrink-0 flex items-center justify-center w-6 h-6 cursor-pointer group/master ml-1 sm:ml-2"
    onclick={onToggleSelectAll}
    onkeydown={(e) => { if (e.key === ' ') onToggleSelectAll(); }}
    role="checkbox"
    aria-checked={isAllSelected}
    tabindex="0"
  >
    <div class="w-4 h-4 rounded border-2 transition-all flex items-center justify-center
      {isAllSelected ? 'bg-neon-cyan border-neon-cyan shadow-[0_0_10px_rgba(0,243,255,0.4)]' : 'bg-white/5 border-white/10 group-hover/master:border-white/30'}">
      {#if isAllSelected}
        <Check size={12} strokeWidth={4} class="text-black" />
      {/if}
    </div>
  </div>

  <!-- 2. Integrated Search -->
  <div class="relative group w-[100px] sm:w-[160px] shrink-0">
    <div class="absolute inset-y-0 left-2 flex items-center pointer-events-none">
      <Search size={11} class="text-gray-600 group-focus-within:text-neon-cyan transition-all" />
    </div>
    <input
      bind:value={searchInput}
      oninput={onSearchInput}
      type="text"
      placeholder="ID..."
      class="w-full h-6 bg-white/[0.02] border border-white/5 rounded-md pl-7 pr-2 text-[9px] font-mono text-gray-300 placeholder:text-gray-700 focus:outline-none focus:border-neon-cyan/40 focus:bg-white/[0.04] transition-all uppercase tracking-widest leading-none"
    />
  </div>

  <!-- 3. Atomic Filter Strip -->
  <div class="flex-1 flex items-center gap-0.5 overflow-x-auto no-scrollbar scroll-smooth">
    {#each filters as filter}
      {@const isActive = activeFilter === filter}
      {@const statusConfig = filter !== "all" ? ORDER_STATUS_MAP[filter] : null}
      <button
        onclick={() => (activeFilter = filter)}
        class="px-2 py-1 text-[8.5px] font-mono font-black uppercase tracking-tighter rounded transition-all relative flex-shrink-0
          {isActive
          ? 'text-neon-cyan'
          : 'text-gray-600 hover:text-gray-300'}"
      >
        {filter === "all" ? "TOTAL" : statusConfig?.label || filter}
        {#if isActive}
          <div class="absolute -bottom-1.5 left-1 right-1 h-[2px] bg-neon-cyan shadow-[0_0_10px_neon-cyan] rounded-full"></div>
        {/if}
      </button>
    {/each}
  </div>

  <div class="w-px h-3.5 bg-white/10 shrink-0"></div>

  <!-- 4. Global Metrics -->
  <div class="flex items-center gap-2 shrink-0 pr-1">
    <div class="hidden sm:flex items-center gap-1.5 px-2 py-0.5 bg-neon-cyan/5 border border-neon-cyan/10 rounded">
      <span class="text-[7px] font-mono text-neon-cyan/40 uppercase">P</span>
      <span class="text-[9px] font-mono text-neon-cyan font-black">{totalOrders}</span>
    </div>

    <div class="bg-white/[0.03] border border-white/10 px-1 py-0.5 rounded flex items-center hover:border-neon-cyan/30 transition-all group/select">
      <select
        bind:value={pageSize}
        class="bg-transparent border-none text-gray-400 text-[8.5px] font-mono focus:outline-none cursor-pointer appearance-none text-center hover:text-neon-cyan transition-colors"
      >
        <option value={10} class="bg-[#0a0a0a] text-gray-300">10</option>
        <option value={20} class="bg-[#0a0a0a] text-gray-300">20</option>
        <option value={50} class="bg-[#0a0a0a] text-gray-300">50</option>
      </select>
    </div>

    <button
      onclick={onRefresh}
      class="p-1 text-gray-600 hover:text-neon-cyan transition-all"
    >
      <RefreshCw size={12} class={isLoading ? "animate-spin text-neon-cyan" : ""} />
    </button>
  </div>
</div>
