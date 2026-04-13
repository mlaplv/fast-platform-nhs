<script lang="ts">
  import Search from "lucide-svelte/icons/search";
  import Eye from "lucide-svelte/icons/eye";
  import EyeOff from "lucide-svelte/icons/eye-off";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Plus from "lucide-svelte/icons/plus";
  import ChevronUp from "lucide-svelte/icons/chevron-up";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Tag from "lucide-svelte/icons/tag";

  let {
    searchInput,
    activeFilter,
    activeCategory,
    categories = [],
    pageSize = $bindable(),
    selectedIds,
    totalProducts,
    isLoading,
    isHeaderCollapsed = $bindable(),
    STATUS_MAP,
    onSearchInput,
    onFilterChange,
    onCategoryChange,
    onPageSizeChange,
    onBulkActivate,
    onBulkDeactivate,
    onBulkDelete,
    onBulkAiFeatured,
    onBulkDiscount,
    onOpenCreate,
    onLoadProducts,
  } = $props<{
    searchInput: string;
    activeFilter: string;
    activeCategory: string;
    categories: { id: string; name: string }[];
    pageSize: number;
    selectedIds: Set<string>;
    totalProducts: number;
    isLoading: boolean;
    isHeaderCollapsed: boolean;
    STATUS_MAP: Record<string, { label: string; color: string }>;
    onSearchInput: (e: Event) => void;
    onFilterChange: (f: string) => void;
    onCategoryChange: (c: string) => void;
    onPageSizeChange: () => void;
    onBulkActivate: () => void;
    onBulkDeactivate: () => void;
    onBulkDelete: () => void;
    onBulkAiFeatured: (enabled: boolean) => void;
    onBulkDiscount: () => void;
    onOpenCreate: () => void;
    onLoadProducts: () => void;
  }>();
</script>

<div class="flex flex-col xl:flex-row xl:items-center gap-4 bg-white/[0.02] border border-white/10 p-3 sm:p-2.5 rounded-2xl">
  <!-- Search Input (Debounced) -->
  <div class="flex-1 relative group w-full xl:min-w-[250px]">
    <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
      <Search size={16} class="text-gray-500 group-focus-within:text-[#FFB800] group-focus-within:scale-110 transition-all" />
    </div>
    <input
      value={searchInput}
      oninput={onSearchInput}
      type="text"
      placeholder="QUERY_CATALOG..."
      class="w-full bg-black/50 border border-white/5 rounded-xl py-3 left-0 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-[#FFB800]/50 focus:ring-2 focus:ring-[#FFB800]/20 transition-all uppercase tracking-widest shadow-inner shadow-black/50"
    />
  </div>

  <!-- Category Selection -->
  <div class="xl:border-l xl:border-white/10 xl:pl-4">
    <div class="relative group">
      <select
        value={activeCategory}
        onchange={(e) => onCategoryChange(e.currentTarget.value)}
        class="appearance-none bg-black/50 border border-white/5 rounded-xl py-3 pl-4 pr-10 text-[10px] font-mono text-[#FFB800] uppercase tracking-wider focus:outline-none focus:border-[#FFB800]/50 transition-all cursor-pointer min-w-[160px]"
      >
        <option value="" class="bg-[#050505]">ALL_CATEGORIES</option>
        {#each categories as cat}
          <option value={cat.id} class="bg-[#050505]">{cat.name.toUpperCase()}</option>
        {/each}
      </select>
      <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500 group-hover:text-[#FFB800] transition-colors">
        <ChevronDown size={14} />
      </div>
    </div>
  </div>

  <div class="flex flex-col sm:flex-row xl:items-center gap-4 xl:gap-0 mt-2 xl:mt-0">
    <!-- Filters (Scrollable on small screens) -->
    <div class="flex items-center gap-2 sm:gap-1 px-1 sm:px-2 xl:border-l xl:border-white/10 xl:pl-4 overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
      {#each ["all", "active", "draft", "archived"] as f}
        <button
          onclick={() => onFilterChange(f)}
          class="px-4 py-2.5 text-[10px] font-mono uppercase tracking-[0.2em] rounded-xl transition-all duration-300 relative overflow-hidden group/btn font-bold flex-shrink-0
              {activeFilter === f
            ? 'text-[#FFB800] bg-white/[0.05] ring-1 ring-[#FFB800]/30 shadow-sm'
            : 'text-gray-500 hover:text-white hover:bg-white/[0.05]'}"
        >
          {f === "all" ? "Full_Grid" : STATUS_MAP[f]?.label || f}
        </button>
      {/each}
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2 sm:gap-3 xl:border-l xl:border-white/10 xl:pl-4 pr-1 sm:pr-2 flex-wrap sm:flex-nowrap justify-between sm:justify-start w-full sm:w-auto mt-2 sm:mt-0">
      <div class="flex items-center gap-2">
        {#if selectedIds.size > 0}
          <div class="flex items-center gap-1.5 border-r border-white/10 pr-2 mr-1">
            <button onclick={() => onBulkAiFeatured(true)}
              class="px-3 py-2 text-[10px] font-mono uppercase bg-[#00FFFF]/10 border border-[#00FFFF]/30 text-[#00FFFF] rounded-xl hover:bg-[#00FFFF]/20 transition-all hidden sm:inline-block"
              title="Bật AI Featured">
              <Sparkles size={12} class="inline mr-1" /> AI_ON
            </button>
            <button onclick={() => onBulkAiFeatured(true)}
              class="p-2.5 text-[#00FFFF] bg-[#00FFFF]/10 border border-[#00FFFF]/30 rounded-xl sm:hidden" title="Bật AI Featured"><Sparkles size={14}/></button>

            <button onclick={() => onBulkAiFeatured(false)}
              class="px-3 py-2 text-[10px] font-mono uppercase bg-gray-500/10 border border-white/10 text-gray-400 rounded-xl hover:bg-white/5 transition-all hidden sm:inline-block"
              title="Tắt AI Featured">
              AI_OFF
            </button>

            <button onclick={onBulkDiscount}
              class="px-3 py-2 text-[10px] font-mono uppercase bg-[#FFB800]/10 border border-[#FFB800]/30 text-[#FFB800] rounded-xl hover:bg-[#FFB800]/20 transition-all hidden sm:inline-block"
              title="Cập nhật giá khuyến mãi">
              <Tag size={12} class="inline mr-1" /> DISCOUNT
            </button>
            <button onclick={onBulkDiscount}
              class="p-2.5 text-[#FFB800] bg-[#FFB800]/10 border border-[#FFB800]/30 rounded-xl sm:hidden" title="Cập nhật giá khuyến mãi"><Tag size={14}/></button>
          </div>

          <button onclick={onBulkActivate}
            class="px-3 py-2 text-[10px] font-mono uppercase bg-[#39FF14]/10 border border-[#39FF14]/30 text-[#39FF14] rounded-xl hover:bg-[#39FF14]/20 transition-all hidden sm:inline-block"
            ><Eye size={12} class="inline mr-1" /> Kích hoạt</button>
          <button onclick={onBulkActivate}
            class="p-2.5 text-[#39FF14] bg-[#39FF14]/10 border border-[#39FF14]/30 rounded-xl sm:hidden" title="Kích hoạt"><Eye size={14}/></button>

          <button onclick={onBulkDeactivate}
            class="px-3 py-2 text-[10px] font-mono uppercase bg-[#FFB800]/10 border border-[#FFB800]/30 text-[#FFB800] rounded-xl hover:bg-[#FFB800]/20 transition-all hidden sm:inline-block"
            ><EyeOff size={12} class="inline mr-1" /> Huỷ K.Hoạt</button>
          <button onclick={onBulkDeactivate}
            class="p-2.5 text-[#FFB800] bg-[#FFB800]/10 border border-[#FFB800]/30 rounded-xl sm:hidden" title="Huỷ K.Hoạt"><EyeOff size={14}/></button>

          <button onclick={onBulkDelete}
            class="px-3 py-2 text-[10px] font-mono uppercase bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl hover:bg-red-500/20 transition-all hidden sm:inline-block"
            ><Trash2 size={12} class="inline mr-1" /> Xoá ({selectedIds.size})</button>
          <button onclick={onBulkDelete}
            class="p-2.5 text-red-400 bg-red-500/10 border border-red-500/30 rounded-xl sm:hidden" title="Xoá ({selectedIds.size})"><Trash2 size={14}/></button>
        {/if}
      </div>

      <div class="flex items-center gap-2 sm:gap-3 ml-auto sm:ml-0">
        <div class="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 uppercase tracking-widest bg-black/40 sm:bg-transparent px-2 sm:px-0 py-1.5 sm:py-0 rounded-lg sm:rounded-none">
          <span class="hidden sm:inline">Show</span>
          <select
            value={pageSize}
            onchange={(e) => { pageSize = Number(e.currentTarget.value); onPageSizeChange(); }}
            class="bg-transparent sm:bg-black/60 border-none sm:border sm:border-white/10 rounded-md px-1 sm:px-1.5 py-1 text-[#FFB800] text-[10px] sm:text-[9px] font-mono font-bold focus:outline-none cursor-pointer appearance-none text-center"
          >
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span class="opacity-50 sm:opacity-100">/ {totalProducts}</span>
        </div>

        <button onclick={onOpenCreate}
          class="flex items-center justify-center gap-2 p-2.5 sm:px-4 sm:py-2 text-[10px] font-bold tracking-widest font-mono uppercase bg-[#FFB800]/10 border border-[#FFB800]/30 text-[#FFB800] hover:bg-[#FFB800]/20 hover:text-white rounded-xl transition-all duration-300"
          title="Add Product"
        >
          <Plus size={14} /> <span class="hidden sm:inline">Add_Product</span>
        </button>
        <button onclick={onLoadProducts} title="Force Resync"
          class="p-2.5 text-gray-500 hover:text-[#FFB800] border border-white/5 hover:border-[#FFB800]/30 rounded-xl bg-black/40 hover:bg-[#FFB800]/10 transition-all hidden sm:block"
        >
          <RefreshCw size={14} class={isLoading ? "animate-spin text-[#FFB800]" : ""} />
        </button>
        <button
          onclick={() => (isHeaderCollapsed = !isHeaderCollapsed)}
          class="p-2.5 border border-white/10 text-gray-500 hover:text-[#FFB800] hover:border-[#FFB800]/30 bg-black/40 hover:bg-[#FFB800]/10 rounded-xl transition-all"
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
</style>
