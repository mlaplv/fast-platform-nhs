<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import ShoppingCart from "lucide-svelte/icons/shopping-cart";
  import Search from "lucide-svelte/icons/search";
  import Package from "lucide-svelte/icons/package";
  import TrendingUp from "lucide-svelte/icons/trending-up";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import type { Order, BaseWidgetProps } from "$lib/types";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import OrderDetailDrawer from "./OrderDetailDrawer.svelte";
  import OrderListItem from "./OrderListItem.svelte";
  import OrderPagination from "./OrderPagination.svelte";
  import { ORDER_STATUS_MAP } from "$lib/constants/order";

  import OrderFilters from "./OrderFilters.svelte";

  let { data = {} } = $props<BaseWidgetProps>();

  let orders = $state<Order[]>([]);
  let totalOrders = $state(0);
  let isLoading = $state(true);

  let searchTerm = $state("");
  let searchInput = $state("");
  let activeFilter = $state("all");

  let currentPage = $state(1);
  let pageSize = $state(10);

  let selectedOrderId = $state<string | null>(null);
  let isDrawerOpen = $state(false);

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
    } catch (error: unknown) {
      const err = error as Error;
      nanobot.addLog(
        `[SYS] Order load failed: ${err.message}`,
        "Nanobot-System",
      );
      orders = [];
      totalOrders = 0;
    } finally {
      isLoading = false;
    }
  }

  $effect(() => {
    loadOrders();
  });

  // Reset page when filter or search changes
  $effect(() => {
    if (activeFilter || searchTerm) {
      untrack(() => {
        currentPage = 1;
      });
    }
  });

  let searchTimer: ReturnType<typeof setTimeout> | undefined;
  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchTerm = val;
      currentPage = 1;
    }, 500);
  }

  $effect(() => {
    const action = nanobot.commandAction;
    if (!action || action.entity !== "order") return;

    if ((action.verb === "search" || action.verb === "view") && action.args) {
      if (nanobot.consumeCommand(action.verb, "order")) {
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
          activeFilter = matchedFilter;
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
    }
  });

  function openDrawer(id: string) {
    if (!id) return;
    selectedOrderId = id;
    isDrawerOpen = true;
    nanobot.addLog(`[ACTION] Mở chi tiết đơn: ${id.split("-")[0]}`, "Nanobot-System");
  }

  async function handleOrderAction(orderId: string, actionType: string) {
    if (actionType === "CANCELLED") {
      const reason = await nanobot.showConfirm({
        isPrompt: true,
        title: "XÁC NHẬN HUỶ ĐƠN",
        message: "Vui lòng nhập lý do huỷ đơn hàng:",
        defaultValue: "Hết hàng",
        promptPlaceholder: "Lý do huỷ...",
        confirmLabel: "HUỶ ĐƠN",
        cancelLabel: "QUAY LẠI",
      });
      if (reason !== null && typeof reason === "string") {
        try {
          await apiClient.patch(`/api/v1/orders/${orderId}/cancel`, { reason });
          nanobot.addLog(
            "Đã huỷ đơn hàng " + orderId.split("-")[0],
            "Nanobot-System",
          );
          loadOrders();
        } catch (e: unknown) {
          const err = e as Error;
          nanobot.showToast(err.message || "Lỗi khi huỷ đơn", "error");
        }
      }
    } else if (actionType === "TOGGLE_SPAM") {
      const order = orders.find((o) => o.id === orderId);
      const isMarking = !order?.isSpam;
      const confirm = await nanobot.showConfirm({
        title: isMarking ? "XÁC NHẬN ĐÁNH DẤU SPAM" : "XÁC NHẬN GỠ BỎ SPAM",
        message: isMarking
          ? "Đánh dấu đơn hàng này là SPAM và chuyển vào khu vực cách ly?"
          : "Gỡ bỏ nhãn SPAM và cho phép xử lý đơn hàng này như bình thường?",
        confirmLabel: "XÁC NHẬN",
        cancelLabel: "QUAY LẠI",
      });
      if (confirm) {
        try {
          await apiClient.patch(`/api/v1/orders/${orderId}/spam`);
          nanobot.addLog(
            isMarking ? "Đã đánh dấu SPAM" : "Đã gỡ bỏ SPAM",
            "Nanobot-System",
          );
          loadOrders();
        } catch (e: unknown) {
          const err = e as Error;
          nanobot.showToast(
            err.message || "Lỗi cập nhật trạng thái SPAM",
            "error",
          );
        }
      }
    } else {
      const label =
        ORDER_STATUS_MAP[actionType.toLowerCase()]?.label || actionType;
      const confirm = await nanobot.showConfirm({
        title: "XÁC NHẬN CHUYỂN TRẠNG THÁI",
        message: `Đổi trạng thái đơn hàng sang "${label.toUpperCase()}"?\nHành động này sẽ được lưu vào lịch sử hệ thống.`,
        confirmLabel: "XÁC NHẬN",
        cancelLabel: "QUAY LẠI",
      });
      if (confirm) {
        try {
          await apiClient.patch(`/api/v1/orders/${orderId}/status`, {
            status: actionType,
          });
          nanobot.addLog("Cập nhật trạng thái " + actionType, "Nanobot-System");
          loadOrders();
        } catch (e: unknown) {
          const err = e as Error;
          nanobot.showToast(err.message || "Lỗi cập nhật trạng thái", "error");
        }
      }
    }
  }

  let totalPages = $derived(Math.max(1, Math.ceil(totalOrders / pageSize)));
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <OrderFilters
    bind:searchInput
    bind:activeFilter
    bind:pageSize
    {totalOrders}
    {isLoading}
    onRefresh={loadOrders}
    onSearchInput={handleSearchInput}
  />

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
          <OrderListItem
            {order}
            {status}
            onOpenDetail={openDrawer}
            onAction={handleOrderAction}
          />
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
