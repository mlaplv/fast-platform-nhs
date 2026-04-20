<script lang="ts">
  import Search from "lucide-svelte/icons/search";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Plus from "lucide-svelte/icons/plus";
  import ChevronUp from "lucide-svelte/icons/chevron-up";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import Newspaper from "lucide-svelte/icons/newspaper";

  let {
    searchInput,
    activeTab,
    activeCategoryFilter,
    categories = [],
    pageSize = $bindable(),
    selectedIds,
    totalArticles,
    isLoading,
    isHeaderCollapsed = $bindable(),
    onSearchInput,
    onTabChange,
    onCategoryChange,
    onPageSizeChange,
    onOpenCreate,
    onLoadArticles,
  } = $props<{
    searchInput: string;
    activeTab: string;
    activeCategoryFilter: string;
    categories: string[];
    pageSize: number;
    selectedIds: Set<string>;
    totalArticles: number;
    isLoading: boolean;
    isHeaderCollapsed: boolean;
    onSearchInput: (e: Event) => void;
    onTabChange: (t: string) => void;
    onCategoryChange: (c: string) => void;
    onPageSizeChange: () => void;
    onOpenCreate: () => void;
    onLoadArticles: () => void;
  }>();
</script>

<div class="flex flex-col xl:flex-row xl:items-center gap-4 bg-white/[0.02] border border-white/10 p-3 sm:p-2.5 rounded-2xl relative z-20">
  <!-- Search Input -->
  <div class="flex-1 relative group w-full xl:min-w-[250px]">
    <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
      <Search size={16} class="text-gray-500 group-focus-within:text-cyan-400 group-focus-within:scale-110 transition-all" />
    </div>
    <input
      value={searchInput}
      oninput={onSearchInput}
      type="text"
      placeholder="TÌM_KIẾM_TIN_TỨC..."
      class="w-full bg-black/50 border border-white/5 rounded-xl py-3 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all uppercase tracking-widest shadow-inner shadow-black/50"
    />
  </div>

  <!-- Category Selection -->
  <div class="xl:border-l xl:border-white/10 xl:pl-4">
    <div class="relative group">
      <select
        value={activeCategoryFilter}
        onchange={(e) => onCategoryChange(e.currentTarget.value)}
        class="appearance-none bg-black/50 border border-white/5 rounded-xl py-3 pl-4 pr-10 text-[10px] font-mono text-cyan-400 uppercase tracking-wider focus:outline-none focus:border-cyan-500/50 transition-all cursor-pointer min-w-[160px]"
      >
        <option value="all" class="bg-[#050505]">TẤT CẢ CHUYÊN MỤC</option>
        {#each categories as cat}
          <option value={cat} class="bg-[#050505]">{cat.toUpperCase()}</option>
        {/each}
      </select>
      <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500 group-hover:text-cyan-400 transition-colors">
        <ChevronDown size={14} />
      </div>
    </div>
  </div>

  <div class="flex flex-col sm:flex-row xl:items-center gap-4 xl:gap-0 mt-2 xl:mt-0">
    <!-- Filters -->
    <div class="flex items-center gap-2 sm:gap-1 px-1 sm:px-2 xl:border-l xl:border-white/10 xl:pl-4 overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
      {#each ["all", "published", "draft"] as t}
        <button
          onclick={() => onTabChange(t)}
          class="px-4 py-2.5 text-[10px] font-mono uppercase tracking-[0.2em] rounded-xl transition-all duration-300 relative overflow-hidden group/btn font-bold flex-shrink-0
              {activeTab === t
            ? 'text-cyan-400 bg-white/[0.05] ring-1 ring-cyan-400/30 shadow-sm'
            : 'text-gray-500 hover:text-white hover:bg-white/[0.05]'}"
        >
          {t === "all" ? "KHO_TỔNG" : t === "published" ? "BÀI_LIVE" : "BẢN_NHÁP"}
        </button>
      {/each}
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2 sm:gap-3 xl:border-l xl:border-white/10 xl:pl-4 pr-1 sm:pr-2 flex-wrap sm:flex-nowrap justify-between sm:justify-start w-full sm:w-auto mt-2 sm:mt-0">
      <div class="flex items-center gap-2 sm:gap-3 ml-auto sm:ml-0">
        <div class="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 uppercase tracking-widest bg-black/40 sm:bg-transparent px-2 sm:px-0 py-1.5 sm:py-0 rounded-lg sm:rounded-none">
          <span class="hidden sm:inline">Hiện</span>
          <select
            value={pageSize}
            onchange={(e) => { pageSize = Number(e.currentTarget.value); onPageSizeChange(); }}
            class="bg-transparent sm:bg-black/60 border-none sm:border sm:border-white/10 rounded-md px-1 sm:px-1.5 py-1 text-cyan-400 text-[10px] sm:text-[9px] font-mono font-bold focus:outline-none cursor-pointer appearance-none text-center"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
          <span class="opacity-50 sm:opacity-100">/ {totalArticles}</span>
        </div>

        <button onclick={onOpenCreate}
          class="flex items-center justify-center gap-2 p-2.5 sm:px-4 sm:py-2 text-[10px] font-bold tracking-widest font-mono uppercase bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20 hover:text-white rounded-xl transition-all duration-300 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
          title="Thêm bài viết"
        >
          <Plus size={14} /> <span class="hidden sm:inline">Tạo bài mới</span>
        </button>
        <button onclick={onLoadArticles} title="Làm mới dữ liệu"
          class="p-2.5 text-gray-500 hover:text-cyan-400 border border-white/5 hover:border-cyan-500/30 rounded-xl bg-black/40 hover:bg-cyan-500/10 transition-all hidden sm:block"
        >
          <RefreshCw size={14} class={isLoading ? "animate-spin text-cyan-400" : ""} />
        </button>
        <button
          onclick={() => (isHeaderCollapsed = !isHeaderCollapsed)}
          class="p-2.5 border border-white/10 text-gray-500 hover:text-cyan-400 hover:border-cyan-500/30 bg-black/40 hover:bg-cyan-400/10 rounded-xl transition-all"
          title={isHeaderCollapsed ? "Phóng to thống kê" : "Thu gọn thống kê"}
        >
          {#if isHeaderCollapsed}<ChevronDown size={14} />{:else}<ChevronUp size={14} />{/if}
        </button>
      </div>
    </div>
  </div>
</div>

<style>
  @reference "tailwindcss";
  .custom-scrollbar::-webkit-scrollbar { height: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 20px; }
</style>
