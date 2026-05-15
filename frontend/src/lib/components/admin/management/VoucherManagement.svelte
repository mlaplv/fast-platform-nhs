<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import Gift from "@lucide/svelte/icons/gift";
  import Search from "@lucide/svelte/icons/search";
  import Ticket from "@lucide/svelte/icons/ticket";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import type { BaseWidgetProps, Voucher } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import VoucherListItem from "./VoucherListItem.svelte";
  import VoucherDrawer from "./VoucherDrawer.svelte";
  import VoucherFilters from "./VoucherFilters.svelte";
  import OrderPagination from "./OrderPagination.svelte"; // Reusing pagination layout
  import BulkActionBar from "./BulkActionBar.svelte";

  let { data = {} } = $props<BaseWidgetProps>();

  let vouchers = $state<Voucher[]>([]);
  let totalVouchers = $state(0);
  let isLoading = $state(true);

  let searchTerm = $state("");
  let searchInput = $state("");
  let activeFilter = $state("all");
  let categoryFilter = $state("ALL");

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
      if (categoryFilter !== "ALL") params.append("category", categoryFilter);
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
    if (activeFilter || searchTerm || categoryFilter) {
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
      cancelLabel: "Quay lại",
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

  const VOUCHER_STATUS_MAP = {
    ACTIVE: { label: "BẬT HOẠT ĐỘNG", color: "text-[#00FFFF]", border: "border-[#00FFFF]" },
    INACTIVE: { label: "TẮT HOẠT ĐỘNG", color: "text-gray-500", border: "border-gray-500" }
  };

  const handleDeleteBulk = async () => {
    const confirm = await nanobot.showConfirm({
      title: "XÁC NHẬN XOÁ HÀNG LOẠT",
      message: `Bạn có chắc chắn muốn xoá ${selectedIds.length} voucher đã chọn? Hành động này không thể hoàn tác.`,
      confirmLabel: "XOÁ HẾT NGAY",
      cancelLabel: "Hủy bỏ",
    });
    if (confirm) {
      try {
        await apiClient.post(`/api/v1/admin/vouchers/bulk-delete`, { ids: selectedIds });
        nanobot.showToast(`Đã xoá ${selectedIds.length} voucher`, "success");
        selectedIds = [];
        loadVouchers();
      } catch (error: unknown) {
        const msg = error instanceof Error ? error.message : String(error);
        nanobot.showToast(msg, "error");
      }
    }
  };

  const handleStatusBulk = async (status: string) => {
    const is_active = status === "ACTIVE";
    try {
      await apiClient.post(`/api/v1/admin/vouchers/bulk-status`, { ids: selectedIds, is_active });
      nanobot.showToast(`Đã cập nhật trạng thái cho ${selectedIds.length} voucher`, "success");
      selectedIds = [];
      loadVouchers();
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.showToast(msg, "error");
    }
  };

  const handleToggleDefault = async (id: string) => {
    try {
      const voucher = vouchers.find(v => v.id === id);
      if (!voucher) return;
      const newVal = !voucher.is_default;
      await apiClient.patch(`/api/v1/admin/vouchers/${id}`, { is_default: newVal });
      nanobot.showToast(`Đã cập nhật mặc định cho ${id}`, "success");
      loadVouchers();
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.showToast(msg, "error");
    }
  };

  const handleSetDefaultBulk = async () => {
    try {
      await apiClient.post(`/api/v1/admin/vouchers/bulk-status`, { ids: selectedIds, is_default: true });
      nanobot.showToast(`Đã đặt ${selectedIds.length} voucher làm mặc định`, "success");
      selectedIds = [];
      loadVouchers();
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : String(error);
      nanobot.showToast(msg, "error");
    }
  };

  let totalPages = $derived(Math.max(1, Math.ceil(totalVouchers / pageSize)));
  let isAllSelected = $derived(vouchers.length > 0 && vouchers.every(v => selectedIds.includes(v.id)));
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <VoucherFilters
    bind:searchInput
    bind:activeFilter
    bind:categoryFilter
    {totalVouchers}
    {isLoading}
    {isAllSelected}
    onRefresh={loadVouchers}
    onSearchInput={handleSearchInput}
    onToggleSelectAll={toggleSelectAll}
    onAddNew={() => openDrawer()}
  />

  <div class="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 flex flex-col">
    {#if isLoading}
      <div class="flex-1 flex flex-col items-center justify-center gap-4">
        <div class="w-12 h-12 border-2 border-neon-cyan/10 border-t-neon-cyan rounded-full animate-spin"></div>
        <span class="text-[10px] font-mono text-neon-cyan/50 tracking-[0.4em]">QUERYING_VOUCHERS...</span>
      </div>
    {:else if vouchers.length === 0}
      <div class="flex-1 flex flex-col items-center justify-center gap-4 text-gray-500">
        <div class="w-16 h-16 rounded-full border border-gray-800 bg-white/[0.02] flex items-center justify-center">
          <Gift size={24} class="opacity-30" />
        </div>
        <span class="text-[10px] font-mono tracking-[0.2em]">NO_VOUCHERS_FOUND</span>
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
            onSetDefault={handleToggleDefault}
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

  <BulkActionBar
    selectedCount={selectedIds.length}
    onClear={() => selectedIds = []}
    onDeleteBulk={handleDeleteBulk}
    onArchiveBulk={() => handleStatusBulk("INACTIVE")}
    onSetDefaultBulk={handleSetDefaultBulk}
    onStatusBulk={handleStatusBulk}
    statusMap={VOUCHER_STATUS_MAP}
  />
</div>

<VoucherDrawer
  bind:isOpen={isDrawerOpen}
  voucherId={selectedVoucherId}
  onSaved={loadVouchers}
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
