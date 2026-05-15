<script lang="ts">
  import Search from "@lucide/svelte/icons/search";
  import Filter from "@lucide/svelte/icons/filter";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Plus from "@lucide/svelte/icons/plus";
  import Check from "@lucide/svelte/icons/check";

  let { 
    searchInput = $bindable(), 
    activeFilter = $bindable(), 
    categoryFilter = $bindable(),
    totalVouchers, 
    isLoading, 
    isAllSelected,
    onRefresh,
    onSearchInput,
    onToggleSelectAll,
    onAddNew
  } = $props<{
    searchInput: string;
    activeFilter: string;
    categoryFilter: string;
    totalVouchers: number;
    isLoading: boolean;
    isAllSelected: boolean;
    onRefresh: () => void;
    onSearchInput: (e: Event) => void;
    onToggleSelectAll: () => void;
    onAddNew: () => void;
  }>();
</script>

<div class="px-6 py-4 border-b border-white/5 bg-[#080808] flex flex-wrap items-center justify-between gap-4">
  <div class="flex items-center gap-4 flex-1 min-w-[300px]">
    <!-- Search Bar -->
    <div class="relative flex-1 max-w-md">
      <div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
        <Search size={16} />
      </div>
      <input
        type="text"
        placeholder="Tìm kiếm mã voucher..."
        bind:value={searchInput}
        oninput={onSearchInput}
        class="w-full bg-white/[0.03] border border-white/10 rounded-full pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-neon-cyan/50 transition-all"
      />
    </div>

    <!-- Filter Toggle -->
    <div class="flex items-center bg-white/[0.03] border border-white/10 rounded-full p-1">
      <button
        onclick={() => activeFilter = "all"}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono tracking-widest transition-all {activeFilter === 'all' ? 'bg-neon-cyan text-black font-bold' : 'text-gray-500 hover:text-white'}"
      >
        Tất cả
      </button>
      <button
        onclick={() => activeFilter = "active"}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono tracking-widest transition-all {activeFilter === 'active' ? 'bg-neon-cyan text-black font-bold' : 'text-gray-500 hover:text-white'}"
      >
        Đang chạy
      </button>
      <button
        onclick={() => activeFilter = "inactive"}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono tracking-widest transition-all {activeFilter === 'inactive' ? 'bg-neon-cyan text-black font-bold' : 'text-gray-500 hover:text-white'}"
      >
        Đã tắt
      </button>
    </div>

    <!-- Category Filter (Elite V2.2) -->
    <div class="flex items-center bg-white/[0.03] border border-white/10 rounded-full p-1">
      <button
        onclick={() => categoryFilter = "ALL"}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono tracking-widest transition-all {categoryFilter === 'ALL' ? 'bg-amber-400 text-black font-bold' : 'text-gray-500 hover:text-white'}"
      >
        Tất cả mục
      </button>
      <button
        onclick={() => categoryFilter = "SHIPPING"}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono tracking-widest transition-all {categoryFilter === 'SHIPPING' ? 'bg-amber-400 text-black font-bold' : 'text-gray-500 hover:text-white'}"
      >
        Vận chuyển
      </button>
      <button
        onclick={() => categoryFilter = "DISCOUNT"}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono tracking-widest transition-all {categoryFilter === 'DISCOUNT' ? 'bg-amber-400 text-black font-bold' : 'text-gray-500 hover:text-white'}"
      >
        Giảm giá
      </button>
      <button
        onclick={() => categoryFilter = "GIFT"}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono tracking-widest transition-all {categoryFilter === 'GIFT' ? 'bg-amber-400 text-black font-bold' : 'text-gray-500 hover:text-white'}"
      >
        Quà tặng
      </button>
    </div>
  </div>

  <div class="flex items-center gap-3">
    <!-- Selection Tool -->
    <button
      onclick={onToggleSelectAll}
      class="flex items-center gap-2 px-3 py-2 rounded-lg border border-white/10 text-[10px] font-mono tracking-widest hover:bg-white/5 transition-all {isAllSelected ? 'text-neon-cyan border-neon-cyan/40 bg-neon-cyan/5' : 'text-gray-400'}"
    >
      <div class="w-3.5 h-3.5 rounded border border-current flex items-center justify-center">
        {#if isAllSelected}
          <div class="w-1.5 h-1.5 bg-neon-cyan rounded-sm"></div>
        {/if}
      </div>
      <span>Chọn tất cả</span>
    </button>
    
    <!-- Refresh -->
    <button
      onclick={onRefresh}
      disabled={isLoading}
      class="p-2.5 rounded-lg border border-white/10 text-gray-400 hover:text-neon-cyan hover:bg-white/5 transition-all {isLoading ? 'animate-spin' : ''}"
      title="Làm mới"
    >
      <RefreshCw size={18} />
    </button>

    <!-- Create New (TikTok Viral Color) -->
    <button
      onclick={onAddNew}
      class="flex items-center gap-2 bg-neon-cyan text-black px-5 py-2.5 rounded-xl font-black text-[11px] tracking-widest hover:brightness-110 active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(0,243,255,0.2)]"
    >
      <Plus size={18} strokeWidth={3} />
      <span>Tạo Voucher</span>
    </button>
  </div>
</div>
