<script lang="ts">
  import Search from "lucide-svelte/icons/search";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import { onMount } from "svelte";
  import { ORDER_STATUS_MAP } from "$lib/constants/order";

  let {
    searchInput = $bindable(),
    activeFilter = $bindable(),
    pageSize = $bindable(),
    totalOrders,
    isLoading,
    onRefresh,
    onSearchInput,
  } = $props<{
    searchInput: string;
    activeFilter: string;
    pageSize: number;
    totalOrders: number;
    isLoading: boolean;
    onRefresh: () => void;
    onSearchInput: (e: Event) => void;
  }>();

  onMount(() => {
    if (searchInput === undefined) searchInput = "";
    if (activeFilter === undefined) activeFilter = "all";
    if (pageSize === undefined) pageSize = 10;
  });

  const filters = [
    "all",
    "pending",
    "paid",
    "processing",
    "shipped",
    "delivered",
    "completed",
    "cancelled",
  ];
</script>

<div
  class="sticky top-0 z-20 bg-[#050505] border-b border-white/5 p-4 flex flex-col gap-3 shrink-0"
>
  <div
    class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 justify-between"
  >
    <div class="relative group w-full sm:w-[350px]">
      <div
        class="absolute inset-y-0 left-4 flex items-center pointer-events-none"
      >
        <Search
          size={16}
          class="text-gray-500 group-focus-within:text-neon-cyan group-focus-within:scale-110 transition-all"
        />
      </div>
      <input
        bind:value={searchInput}
        oninput={onSearchInput}
        type="text"
        placeholder="SEARCH ID OR CUSTOMER..."
        class="w-full bg-white/[0.02] hover:bg-white/[0.05] border border-white/10 rounded-xl py-3 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-neon-cyan/50 focus:bg-black/50 transition-all uppercase tracking-widest"
      />
    </div>

    <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
      <div
        class="flex items-center gap-2 bg-white/[0.02] border border-white/5 px-3 py-2.5 rounded-xl flex-1 justify-center sm:flex-none"
      >
        <span
          class="text-[9px] font-mono text-gray-500 uppercase tracking-widest hidden sm:inline"
          >Show</span
        >
        <select
          bind:value={pageSize}
          class="bg-transparent border-none text-neon-cyan text-[10px] font-mono font-bold focus:outline-none cursor-pointer appearance-none text-center"
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
        <span
          class="text-[9px] font-mono text-gray-400 uppercase tracking-widest whitespace-nowrap hidden sm:inline"
          >of {totalOrders}</span
        >
      </div>

      <button
        onclick={onRefresh}
        title="Force Resync"
        class="p-2.5 shrink-0 text-gray-500 hover:text-neon-cyan border border-white/5 hover:border-neon-cyan/30 rounded-xl bg-white/[0.02] hover:bg-neon-cyan/10 transition-all"
      >
        <RefreshCw
          size={16}
          class={isLoading ? "animate-spin text-neon-cyan" : ""}
        />
      </button>
    </div>
  </div>

  <div class="flex items-center gap-2 overflow-x-auto custom-scrollbar pb-1">
    {#each filters as filter}
      {@const isActive = activeFilter === filter}
      {@const statusConfig = filter !== "all" ? ORDER_STATUS_MAP[filter] : null}
      <button
        onclick={() => (activeFilter = filter)}
        class="px-5 py-2.5 text-[10px] font-mono font-bold uppercase tracking-widest rounded-lg transition-all relative overflow-hidden flex-shrink-0 border
          {isActive
          ? 'bg-white/10 text-white border-white/20 shadow-sm'
          : 'text-gray-500 border-white/5 hover:text-gray-200 hover:bg-white/[0.05] hover:border-white/10'}"
      >
        {filter === "all" ? "TOTAL_LINK" : statusConfig?.label || filter}
      </button>
    {/each}
  </div>
</div>
