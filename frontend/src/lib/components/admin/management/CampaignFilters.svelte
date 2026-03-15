<script lang="ts">
  import Search from "lucide-svelte/icons/search";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import PlusCircle from "lucide-svelte/icons/plus-circle";
  import BarChart3 from "lucide-svelte/icons/bar-chart-3";
  import Sparkles from "lucide-svelte/icons/sparkles";

  let {
    searchInput = $bindable(),
    activeStatus = $bindable(),
    activeCategory = $bindable(),
    activeStep = $bindable(),
    isLoading,
    totalItems,
    onRefresh,
    onSearchInput,
    onCreateNew
  } = $props<{
    searchInput: string;
    activeStatus: string;
    activeCategory: string;
    activeStep: number | "all";
    isLoading: boolean;
    totalItems: number;
    onRefresh: () => void;
    onSearchInput: (e: Event) => void;
    onCreateNew: () => void;
  }>();

  const statusFilters = [
    { id: "all", label: "TOTAL_SCOPE" },
    { id: "PROCESSING", label: "PROCESSING" },
    { id: "WAITING_FOR_REVIEW", label: "REVIEW_GATE" },
    { id: "COMPLETED", label: "STABILIZED" },
    { id: "REJECTED", label: "REJECTED" }
  ];

  const categoryFilters = [
    { id: "all", label: "ALL_GENRES", icon: BarChart3 },
    { id: "CREATIVE_CONTENT", label: "CREATIVE", icon: Sparkles },
    { id: "AD_MANAGEMENT", label: "AD_OPS", icon: BarChart3 }
  ];

  const stepFilters = [
    { id: "all", label: "ALL" },
    { id: 1, label: "P1: Keyword" },
    { id: 2, label: "P2: Assets" },
    { id: 3, label: "P3: Outline" },
    { id: 4, label: "P4: Draft" },
    { id: 5, label: "P5: Safety" },
    { id: 6, label: "P6: Publish" }
  ];
</script>

<div class="sticky top-0 z-20 bg-[#050505] border-b border-white/5 p-4 flex flex-col gap-4 shrink-0">
  <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 justify-between">
    <!-- Search Nexus -->
    <div class="relative group w-full sm:w-[400px]">
      <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
        <Search
          size={16}
          class="text-gray-500 group-focus-within:text-neon-cyan group-focus-within:scale-110 transition-all"
        />
      </div>
      <input
        bind:value={searchInput}
        oninput={onSearchInput}
        type="text"
        placeholder="SEARCH CAMPAIGNS, TOPICS OR INTENTS..."
        class="w-full bg-white/[0.02] hover:bg-white/[0.05] border border-white/10 rounded-xl py-3.5 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-neon-cyan/50 focus:bg-black/50 transition-all uppercase tracking-widest shadow-inner shadow-black/50"
      />
    </div>

    <!-- Action Matrix -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-1 bg-white/[0.02] border border-white/5 p-1 rounded-xl">
        {#each categoryFilters as cat}
          <button
            onclick={() => activeCategory = cat.id}
            class="flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-mono font-bold uppercase tracking-widest transition-all
              {activeCategory === cat.id 
                ? 'bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30' 
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5 border border-transparent'}"
          >
            <cat.icon size={12} />
            <span class="hidden lg:inline">{cat.label}</span>
          </button>
        {/each}
      </div>

      <div class="h-8 w-px bg-white/5"></div>

      <button
        onclick={onRefresh}
        class="p-2.5 text-gray-500 hover:text-neon-cyan border border-white/5 hover:border-neon-cyan/30 rounded-xl bg-white/[0.02] hover:bg-neon-cyan/10 transition-all active:scale-95"
      >
        <RefreshCw size={16} class={isLoading ? "animate-spin text-neon-cyan" : ""} />
      </button>

      <button
        onclick={onCreateNew}
        class="flex items-center gap-2 px-5 py-2.5 bg-neon-cyan text-black hover:bg-[#00E5FF] font-black text-[10px] uppercase tracking-[0.2em] rounded-xl transition-all active:scale-95 shadow-[0_0_20px_rgba(0,255,255,0.2)]"
      >
        <PlusCircle size={14} strokeWidth={3} />
        Initialize
      </button>
    </div>
  </div>

  <!-- Phase Pulse Synchronizer -->
  <div class="flex items-center gap-2 overflow-x-auto scrollbar-hide pb-1 border-b border-white/[0.03]">
    <div class="px-3 shrink-0">
       <span class="text-[9px] font-mono font-black text-neon-cyan/40 uppercase tracking-tighter">PHASE_GATE:</span>
    </div>
    {#each stepFilters as phase}
      {@const isActive = activeStep === phase.id}
      <button
        onclick={() => activeStep = phase.id}
        class="px-4 py-2 text-[9px] font-mono font-bold uppercase tracking-widest rounded-lg transition-all relative border shrink-0
          {isActive
            ? 'bg-neon-cyan/10 text-neon-cyan border-neon-cyan/20'
            : 'text-gray-600 border-transparent hover:text-gray-400 hover:bg-white/[0.02]'}"
      >
        {phase.label}
      </button>
    {/each}
  </div>

  <!-- Status Pulse Synchronizer -->
  <div class="flex items-center gap-2 overflow-x-auto scrollbar-hide pb-1">
    <div class="px-3 shrink-0">
       <span class="text-[9px] font-mono font-black text-gray-500 uppercase tracking-tighter">STATUS_GATE:</span>
    </div>
    {#each statusFilters as status}
      {@const isActive = activeStatus === status.id}
      <button
        onclick={() => activeStatus = status.id}
        class="px-5 py-2.5 text-[10px] font-mono font-bold uppercase tracking-widest rounded-lg transition-all relative border shrink-0
          {isActive
            ? 'bg-white/10 text-white border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.05)]'
            : 'text-gray-600 border-transparent hover:text-gray-300 hover:bg-white/[0.03]'}"
      >
        {status.label}
        {#if isActive}
           <div class="absolute bottom-1 left-1.2 right-1.2 h-0.5 bg-neon-cyan rounded-full opacity-50"></div>
        {/if}
      </button>
    {/each}
    <div class="ml-auto flex items-center gap-2 px-3 font-mono text-[9px] text-gray-600 uppercase tracking-tighter shrink-0">
       <span class="text-neon-cyan/40">Entities:</span>
       <span class="text-gray-400 font-bold">{totalItems}</span>
    </div>
  </div>
</div>

<style>
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
