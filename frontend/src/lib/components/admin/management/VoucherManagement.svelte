<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import Gift from "lucide-svelte/icons/gift";
  import Search from "lucide-svelte/icons/search";
  import Ticket from "lucide-svelte/icons/ticket";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import type { BaseWidgetProps } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import VoucherListItem from "./VoucherListItem.svelte";
  import VoucherDrawer from "./VoucherDrawer.svelte";
  import VoucherFilters from "./VoucherFilters.svelte";
  import OrderPagination from "./OrderPagination.svelte"; // Reusing pagination layout

  export interface Voucher {
    id: string;
    type: "FIXED" | "PERCENT" | "SHIPPING";
    value: number;
    min_spend: number;
    max_discount?: number | null;
    usage_limit?: number | null;
    used_count: number;
    start_date?: string | null;
    end_date?: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }

  let { data = {} } = $props<BaseWidgetProps>();

  let vouchers = $state<Voucher[]>([]);
  let totalVouchers = $state(0);
  let isLoading = $state(true);

  let searchTerm = $state("");
  let searchInput = $state("");
  let activeFilter = $state("all");

  let currentPage = $state(1);
  let pageSize = $state(10);

  let selectedVoucherId = $state<string | null>(null);
  let isDrawerOpen = $state(false);
  let selectedIds = $state<string[]>([]);

  async function loadVouchers() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: offset.toString(),
      });
      if (activeFilter === "active") params.append("is_active", "true");
      if (activeFilter === "inactive") params.append("is_active", "false");
      if (searchTerm) params.append("search", searchTerm);

      const res = await apiClient.get<{ data: Voucher[]; total: number }>(
        `/api/v1/admin/vouchers?${params.toString()}`,
      );
      vouchers = res.data;
      totalVouchers = res.total;
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.addLog(`[SYS] Voucher load failed: ${msg}`, "Nanobot-System");
      vouchers = [];
      totalVouchers = 0;
    } finally {
      isLoading = false;
    }
  }

  // Elite V2.2: Command-Driven UI Orchestration
  $effect(() => {
    if (data?.action === "CREATE") {
      untrack(() => openDrawer(null));
    }
  });

  $effect(() => {
    loadVouchers();
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

  function openDrawer(id: string | null = null) {
    selectedVoucherId = id;
    isDrawerOpen = true;
  }

  async function handleDelete(id: string) {
    const confirm = await nanobot.showConfirm({
      title: "XÁC NHẬN XOÁ VOUCHER",
      message: `Bạn có chắc chắn muốn xoá vĩnh viễn voucher ${id}? Hành động này không thể hoàn tác.`,
      confirmLabel: "XOÁ NGAY",
      cancelLabel: "QUAY LẠI",
    });
    if (confirm) {
      try {
        await apiClient.delete(`/api/v1/admin/vouchers/${id}`);
        nanobot.showToast(`Đã xoá voucher ${id}`, "success");
        loadVouchers();
      } catch (error: unknown) {
        const msg = error instanceof Error ? error.message : String(error);
        nanobot.showToast(msg, "error");
      }
    }
  }

  function toggleSelect(id: string) {
    if (selectedIds.includes(id)) {
      selectedIds = selectedIds.filter(i => i !== id);
    } else {
      selectedIds = [...selectedIds, id];
    }
  }

  function toggleSelectAll() {
    const pageIds = vouchers.map(v => v.id);
    const allSelected = pageIds.every(id => selectedIds.includes(id));
    if (allSelected) {
      selectedIds = selectedIds.filter(id => !pageIds.includes(id));
    } else {
      const newIds = pageIds.filter(id => !selectedIds.includes(id));
      selectedIds = [...selectedIds, ...newIds];
    }
  }

  let totalPages = $derived(Math.max(1, Math.ceil(totalVouchers / pageSize)));
  let isAllSelected = $derived(vouchers.length > 0 && vouchers.every(v => selectedIds.includes(v.id)));
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <VoucherFilters
    bind:searchInput
    bind:activeFilter
    {totalVouchers}
    {isLoading}
    {isAllSelected}
    onRefresh={loadVouchers}
    onSearchInput={handleSearchInput}
    onToggleSelectAll={toggleSelectAll}
    onAddNew={() => openDrawer()}
  />

  <div class="flex-1 overflow-y-scroll custom-scrollbar p-4 sm:p-6">
    {#if isLoading}
      <div class="h-full flex flex-col items-center justify-center gap-4">
        <div class="w-12 h-12 border-2 border-neon-cyan/10 border-t-neon-cyan rounded-full animate-spin"></div>
        <span class="text-[10px] font-mono text-neon-cyan/50 uppercase tracking-[0.4em]">QUERYING_VOUCHERS...</span>
      </div>
    {:else if vouchers.length === 0}
      <div class="h-full flex flex-col items-center justify-center gap-4 text-gray-500">
        <div class="w-16 h-16 rounded-full border border-gray-800 bg-white/[0.02] flex items-center justify-center">
          <Gift size={24} class="opacity-30" />
        </div>
        <span class="text-[10px] font-mono uppercase tracking-[0.2em]">NO_VOUCHERS_FOUND</span>
      </div>
    {:else}
      <div class="grid grid-cols-1 gap-3">
        {#each vouchers as voucher (voucher.id)}
          <VoucherListItem
            {voucher}
            isSelected={selectedIds.includes(voucher.id)}
            onOpenDetail={openDrawer}
            onDelete={handleDelete}
            onToggleSelect={toggleSelect}
          />
        {/each}
      </div>
    {/if}
  </div>

  <OrderPagination
    bind:currentPage
    {totalPages}
    {pageSize}
    totalItems={totalVouchers}
  />
</div>

<VoucherDrawer
  bind:isOpen={isDrawerOpen}
  voucherId={selectedVoucherId || ""}
  onClose={() => (isDrawerOpen = false)}
  onReload={loadVouchers}
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
</style>
