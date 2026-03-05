<script lang="ts">
  import { fade } from "svelte/transition";
  import ShoppingCart from "lucide-svelte/icons/shopping-cart";
  import Search from "lucide-svelte/icons/search";
  import Package from "lucide-svelte/icons/package";
  import TrendingUp from "lucide-svelte/icons/trending-up";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import type { Order } from "$lib/types";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import OrderDetailDrawer from "./OrderDetailDrawer.svelte";
  import OrderListItem from "./OrderListItem.svelte";
  import OrderPagination from "./OrderPagination.svelte";
  import { ORDER_STATUS_MAP } from "$lib/constants/order";

  let orders = $state<Order[]>([]);
  let totalOrders = $state(0);
  let isLoading = $state(true);

  let searchTerm = $state("");
  let searchInput = $state(""); // For debouncing or explicit search
  let activeFilter = $state("all");

  let currentPage = $state(1);
  let pageSize = $state(10);

  // Drawer State
  let selectedOrderId = $state<string | null>(null);
  let isDrawerOpen = $state(false);

  // Fetch Logic
  async function loadOrders() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: offset.toString(),
      });
      if (activeFilter !== "all") params.append("status", activeFilter);
      if (searchTerm) params.append("search", searchTerm);

      const res = await apiClient.get<{ data: Order[]; total: number }>(
        `/api/v1/orders?${params.toString()}`,
      );
      orders = res.data;
      totalOrders = res.total;
    } catch (error: any) {
      nanobot.addLog(
        `[SYS] Order load failed: ${error.message}`,
        "Nanobot-System",
      );
      orders = [];
      totalOrders = 0;
    } finally {
      isLoading = false;
    }
  }

  // React to filter/page/search changes
  $effect(() => {
    loadOrders();
  });

  // When filter or search changes, reset page to 1.
  function handleFilterChange(filter: string) {
    if (activeFilter !== filter) {
      activeFilter = filter;
      currentPage = 1;
    }
  }

  let searchTimer: any;
  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchTerm = val;
      currentPage = 1;
    }, 500);
  }

  // Voice/Text Command Action Handler
  $effect(() => {
    const action = nanobot.commandAction;
    if (!action || action.entity !== "order") return;

    if ((action.verb === "search" || action.verb === "view") && action.args) {
      const filterMap: Record<string, string> = {
        cho: "pending",
        "cho xu ly": "pending",
        pending: "pending",
        "dang giao": "shipped",
        giao: "shipped",
        shipped: "shipped",
        "hoan thanh": "delivered",
        delivered: "delivered",
        "da giao": "delivered",
        "da huy": "cancelled",
        huy: "cancelled",
        cancelled: "cancelled",
        "dang xu ly": "processing",
        processing: "processing",
      };
      const normalizedArg = action.args
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d");
      const matchedFilter = filterMap[normalizedArg];
      if (matchedFilter) {
        handleFilterChange(matchedFilter);
        nanobot.addLog(
          `[ACTION] Voice: Lọc đơn hàng "${action.args}"`,
          "Nanobot-Voice",
        );
      } else {
        searchInput = action.args;
        searchTerm = action.args;
        currentPage = 1;
        nanobot.addLog(
          `[ACTION] Voice: Tìm đơn hàng "${action.args}"`,
          "Nanobot-Voice",
        );
      }
    }
    nanobot.clearCommandAction();
  });

  function openDrawer(id: string) {
    selectedOrderId = id;
    isDrawerOpen = true;
  }

  async function handleOrderAction(orderId: string, actionType: string) {
    if (actionType === 'CANCELLED') {
      const reason = await nanobot.showConfirm({
        isPrompt: true,
        title: "XÁC NHẬN HUỶ ĐƠN",
        message: "Vui lòng nhập lý do huỷ đơn hàng:",
        defaultValue: "Hết hàng",
        promptPlaceholder: "Lý do huỷ...",
        confirmLabel: "HUỶ ĐƠN",
        cancelLabel: "QUAY LẠI"
      });
      
      if (reason !== null) {
        try {
          await apiClient.patch(`/api/v1/orders/${orderId}/cancel`, { reason });
          nanobot.addLog("Đã huỷ đơn hàng " + orderId.split('-')[0], "Nanobot-System");
          loadOrders();
        } catch (e: any) {
          nanobot.showToast(e.message || "Lỗi khi huỷ đơn", "error");
        }
      }
    } else {
      const label = ORDER_STATUS_MAP[actionType.toLowerCase()]?.label || actionType;

      const confirm = await nanobot.showConfirm({
        title: "XÁC NHẬN CHUYỂN TRẠNG THÁI",
        message: `Đổi trạng thái đơn hàng sang "${label.toUpperCase()}"?\nHành động này sẽ được lưu vào lịch sử hệ thống.`,
        confirmLabel: "XÁC NHẬN",
        cancelLabel: "QUAY LẠI"
      });

      if (confirm) {
        try {
          await apiClient.patch(`/api/v1/orders/${orderId}/status`, { status: actionType });
          nanobot.addLog("Cập nhật trạng thái " + actionType, "Nanobot-System");
          loadOrders();
        } catch (e: any) {
          nanobot.showToast(e.message || "Lỗi cập nhật trạng thái", "error");
        }
      }
    }
  }

  let totalPages = $derived(Math.max(1, Math.ceil(totalOrders / pageSize)));
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <!-- Top Priority Control Bar (Sticky) -->
  <div class="sticky top-0 z-20 bg-[#050505] border-b border-white/5 p-4 flex flex-col gap-3 shrink-0">
    
    <!-- Row 1: Search, Stats, Actions -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 justify-between">
      <!-- Search Input -->
      <div class="relative group w-full sm:w-[350px]">
        <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search size={16} class="text-gray-500 group-focus-within:text-neon-cyan group-focus-within:scale-110 transition-all" />
        </div>
        <input
          value={searchInput}
          oninput={handleSearchInput}
          type="text"
          placeholder="SEARCH ID OR CUSTOMER..."
          class="w-full bg-white/[0.02] hover:bg-white/[0.05] border border-white/10 rounded-xl py-3 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-neon-cyan/50 focus:bg-black/50 transition-all uppercase tracking-widest"
        />
      </div>

      <!-- Stats & Quick Refresh -->
      <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
        <div class="flex items-center gap-2 bg-white/[0.02] border border-white/5 px-3 py-2.5 rounded-xl flex-1 justify-center sm:flex-none">
          <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest hidden sm:inline">Show</span>
          <select
            value={pageSize}
            onchange={(e) => { pageSize = Number((e.target as HTMLSelectElement).value); currentPage = 1; }}
            class="bg-transparent border-none text-neon-cyan text-[10px] font-mono font-bold focus:outline-none cursor-pointer appearance-none text-center"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
          <span class="text-[9px] font-mono text-gray-400 uppercase tracking-widest whitespace-nowrap hidden sm:inline">of {totalOrders}</span>
        </div>

        <button
          onclick={loadOrders}
          title="Force Resync"
          class="p-2.5 shrink-0 text-gray-500 hover:text-neon-cyan border border-white/5 hover:border-neon-cyan/30 rounded-xl bg-white/[0.02] hover:bg-neon-cyan/10 transition-all"
        >
          <RefreshCw size={16} class={isLoading ? "animate-spin text-neon-cyan" : ""} />
        </button>
      </div>
    </div>

    <!-- Row 2: Status Funnel (Scrollable) -->
    <div class="flex items-center gap-2 overflow-x-auto custom-scrollbar pb-1">
      {#each ["all", "pending", "paid", "processing", "shipped", "delivered", "completed", "cancelled"] as filter}
        {@const isActive = activeFilter === filter}
        {@const statusConfig = filter !== "all" ? ORDER_STATUS_MAP[filter] : null}
        <button
          onclick={() => handleFilterChange(filter)}
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

  <!-- Main Order Grid (Data Modules) -->
  <div class="flex-1 overflow-y-scroll custom-scrollbar p-4 sm:p-6">
    {#if isLoading}
      <div class="h-full flex flex-col items-center justify-center gap-4">
        <div
          class="w-12 h-12 border-2 border-neon-cyan/10 border-t-neon-cyan rounded-full animate-spin"
        ></div>
        <span
          class="text-[10px] font-mono text-neon-cyan/50 uppercase tracking-[0.4em]"
          >QUERYING_NEXUS...</span
        >
      </div>
    {:else if orders.length === 0}
      <div
        class="h-full flex flex-col items-center justify-center gap-4 text-gray-500"
      >
        <div
          class="w-16 h-16 rounded-full border border-gray-800 bg-white/[0.02] flex items-center justify-center"
        >
          <Package size={24} class="opacity-30" />
        </div>
        <span class="text-[10px] font-mono uppercase tracking-[0.2em]"
          >NO_DATA_FOUND</span
        >
      </div>
    {:else}
      <div class="grid grid-cols-1 gap-3">
        {#each orders as order (order.id)}
          {@const status = ORDER_STATUS_MAP[order.status.toLowerCase()] || {
            label: order.status,
            color: "text-gray-500",
            border: "border-gray-500",
          }}
          <OrderListItem {order} {status} onClick={openDrawer} onAction={handleOrderAction} />
        {/each}
      </div>
    {/if}
  </div>

  <!-- Pagination Controller -->
  <OrderPagination
    bind:currentPage
    {totalPages}
    {pageSize}
    totalItems={totalOrders}
  />
</div>

<!-- Drawer Implementation -->
<OrderDetailDrawer
  bind:isOpen={isDrawerOpen}
  orderId={selectedOrderId || ""}
  onClose={() => (isDrawerOpen = false)}
  onReload={loadOrders}
/>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
    height: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 255, 0.2);
  }
</style>
