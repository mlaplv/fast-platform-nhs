<script lang="ts">
  import { fade } from "svelte/transition";
  import Plus from "lucide-svelte/icons/plus";
  import Search from "lucide-svelte/icons/search";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Eye from "lucide-svelte/icons/eye";
  import ChevronUp from "lucide-svelte/icons/chevron-up";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import ProductStats from "./ProductStats.svelte";
  import ProductForm from "./ProductForm.svelte";
  import ProductTable from "./ProductTable.svelte";
  import OrderPagination from "./OrderPagination.svelte";

  interface Product {
    id: string;
    name: string;
    sku: string;
    price: number;
    stock: number;
    category: string;
    categoryId: string | null;
    status: "active" | "draft" | "archived";
  }

  interface CategoryOption {
    id: string;
    name: string;
  }

  // --- STATE (Server-Side Pagination) ---
  let products = $state<Product[]>([]);
  let totalProducts = $state(0);
  let categories = $state<CategoryOption[]>([]);
  let isLoading = $state(true);
  let searchTerm = $state("");
  let searchInput = $state("");
  let activeFilter = $state("all");
  let currentPage = $state(1);
  let showForm = $state(false);
  let isHeaderCollapsed = $state(false);
  let editingId = $state<string | null>(null);
  let selectedIds = $state<Set<string>>(new Set());

  let formName = $state("");
  let formSku = $state("");
  let formPrice = $state(0);
  let formStock = $state(0);
  let formCategory = $state("");
  let formStatus = $state<"active" | "draft">("draft");

  let pageSize = $state(50); // Default to 50 to prevent DOM/RAM crash on 5000+ items
  const STATUS_MAP: Record<string, { label: string; color: string }> = {
    active: { label: "Đang bán", color: "#39FF14" },
    draft: { label: "Nháp", color: "#FFB800" },
    archived: { label: "Lưu trữ", color: "#666" },
  };

  const totalPages = $derived(Math.max(1, Math.ceil(totalProducts / pageSize)));
  const stats = $derived.by(() => ({
    total: totalProducts,
    active: products.filter(p => p.status === "active").length,
    draft: products.filter(p => p.status === "draft").length,
    totalValue: products.reduce((sum, p) => sum + (p.price * p.stock), 0)
  }));

  // --- SERVER-SIDE FETCH ---
  async function loadProducts() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({ limit: pageSize.toString(), offset: offset.toString() });
      if (activeFilter !== "all") params.append("status", activeFilter);
      if (searchTerm) params.append("search", searchTerm);

      const [pRes, cData] = await Promise.all([
        apiClient.get<{ data: Product[]; total: number }>(`/api/v1/products?${params.toString()}`),
        categories.length ? Promise.resolve(null) : apiClient.get<any[]>("/api/v1/categories"),
      ]);
      products = pRes.data;
      totalProducts = pRes.total;

      if (cData) {
        const opts: CategoryOption[] = [];
        for (const c of cData) {
          opts.push({ id: c.id, name: c.name });
          (c.children || []).forEach((ch: any) => {
            opts.push({ id: ch.id, name: `${c.name} / ${ch.name}` });
          });
        }
        categories = opts;
      }
    } catch (err) {
      nanobot.showToast("Lỗi tải sản phẩm", "error");
      products = [];
      totalProducts = 0;
    } finally {
      isLoading = false;
    }
  }

  $effect(() => { loadProducts(); });

  // V22: Voice Mutation Injection - Product Management
  $effect(() => {
    const data = nanobot.currentData as any;
    const action = nanobot.commandAction;

    if (data?.ui_action === "show_product_management" && data?.intent_type === "MUTATE" && !showForm) {
      editingId = null;
      formName = data?.name || data?.title || "";
      formSku = data?.sku || "";
      formPrice = Number(data?.price) || 0;
      formStock = Number(data?.stock) || 0;
      formCategory = data?.category || "";
      formStatus = "draft";
      showForm = true;
      nanobot.clearCurrentData();
      return;
    }

    if (action?.entity === "product") {
      if (action.verb === "create") {
        if (nanobot.consumeCommand("create", "product")) {
          openCreate();
          if (action.args) formName = action.args;
        }
      }
      else if (action.verb === "search" && action.args) {
        if (nanobot.consumeCommand("search", "product")) {
          searchInput = action.args;
          searchTerm = action.args;
          currentPage = 1;
        }
      }
    }
  });

  let searchTimer: any;
  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { searchTerm = val; currentPage = 1; }, 400);
  }

  function handleFilterChange(filter: string) {
    if (activeFilter !== filter) { activeFilter = filter; currentPage = 1; }
  }

  const formatCurrency = (n: number) => new Intl.NumberFormat("vi-VN").format(n) + "đ";

  function openCreate() {
    editingId = null;
    formName = ""; formSku = ""; formPrice = 0; formStock = 0; formCategory = ""; formStatus = "draft";
    showForm = true;
  }

  function openEdit(p: Product) {
    editingId = p.id;
    formName = p.name; formSku = p.sku; formPrice = p.price; formStock = p.stock;
    formCategory = p.categoryId || "";
    formStatus = p.status === "archived" ? "draft" : p.status;
    showForm = true;
  }

  function toggleSelect(id: string) {
    const updated = new Set(selectedIds);
    updated.has(id) ? updated.delete(id) : updated.add(id);
    selectedIds = updated;
  }

  async function save() {
    if (!formName.trim()) return;
    const payload = {
      name: formName.trim(), sku: formSku || `SKU-${Date.now()}`,
      price: formPrice, stock: formStock, categoryId: formCategory || null, status: formStatus,
    };
    try {
      if (editingId) await apiClient.patch(`/api/v1/products/${editingId}`, payload);
      else await apiClient.post<Product>("/api/v1/products", payload);
      showForm = false;
      await loadProducts();
    } catch (err) { nanobot.showToast("Lưu sản phẩm thất bại", "error"); }
  }

  async function bulk(type: "del" | "act") {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    try {
      if (type === "del") await apiClient.post("/api/v1/products/bulk-delete", { ids });
      else await apiClient.post("/api/v1/products/bulk-activate", { ids });
      selectedIds = new Set();
      await loadProducts();
    } catch (err) { nanobot.showToast("Thao tác hàng loạt thất bại", "error"); }
  }
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <div class="flex flex-col gap-6 p-6 border-b border-white/[0.05]">
    {#if !isHeaderCollapsed}
      <div transition:fade={{ duration: 200 }} class="flex flex-col gap-6">
        <ProductStats {stats} {formatCurrency} />
      </div>
    {/if}

    <div class="flex flex-col xl:flex-row xl:items-center gap-4 bg-white/[0.02] border border-white/10 p-3 sm:p-2.5 rounded-2xl">
      <!-- Search Input (Debounced) -->
      <div class="flex-1 relative group w-full xl:min-w-[250px]">
        <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search size={16} class="text-gray-500 group-focus-within:text-[#FFB800] group-focus-within:scale-110 transition-all" />
        </div>
        <input
          value={searchInput}
          oninput={handleSearchInput}
          type="text"
          placeholder="QUERY_CATALOG..."
          class="w-full bg-black/50 border border-white/5 rounded-xl py-3 left-0 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-[#FFB800]/50 focus:ring-2 focus:ring-[#FFB800]/20 transition-all uppercase tracking-widest shadow-inner shadow-black/50"
        />
      </div>

      <div class="flex flex-col sm:flex-row xl:items-center gap-4 xl:gap-0 mt-2 xl:mt-0">
        <!-- Filters (Scrollable on small screens) -->
        <div class="flex items-center gap-2 sm:gap-1 px-1 sm:px-2 xl:border-l xl:border-white/10 xl:pl-4 overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
          {#each ["all", "active", "draft", "archived"] as f}
            <button
              onclick={() => handleFilterChange(f)}
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
              <button onclick={() => bulk("act")}
                class="px-3 py-2 text-[10px] font-mono uppercase bg-[#39FF14]/10 border border-[#39FF14]/30 text-[#39FF14] rounded-xl hover:bg-[#39FF14]/20 transition-all hidden sm:inline-block"
                ><Eye size={12} class="inline mr-1" /> Kích hoạt ({selectedIds.size})</button>
              <button onclick={() => bulk("act")}
                class="p-2.5 text-[#39FF14] bg-[#39FF14]/10 border border-[#39FF14]/30 rounded-xl sm:hidden" title="Kích hoạt ({selectedIds.size})"><Eye size={14}/></button>

              <button onclick={() => bulk("del")}
                class="px-3 py-2 text-[10px] font-mono uppercase bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl hover:bg-red-500/20 transition-all hidden sm:inline-block"
                ><Trash2 size={12} class="inline mr-1" /> Xoá ({selectedIds.size})</button>
              <button onclick={() => bulk("del")}
                class="p-2.5 text-red-400 bg-red-500/10 border border-red-500/30 rounded-xl sm:hidden" title="Xoá ({selectedIds.size})"><Trash2 size={14}/></button>
            {/if}
          </div>

          <div class="flex items-center gap-2 sm:gap-3 ml-auto sm:ml-0">
            <div class="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 uppercase tracking-widest bg-black/40 sm:bg-transparent px-2 sm:px-0 py-1.5 sm:py-0 rounded-lg sm:rounded-none">
              <span class="hidden sm:inline">Show</span>
              <select
                value={pageSize}
                onchange={(e) => { pageSize = Number((e.target as HTMLSelectElement).value); currentPage = 1; }}
                class="bg-transparent sm:bg-black/60 border-none sm:border sm:border-white/10 rounded-md px-1 sm:px-1.5 py-1 text-[#FFB800] text-[10px] sm:text-[9px] font-mono font-bold focus:outline-none cursor-pointer appearance-none text-center"
              >
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <span class="opacity-50 sm:opacity-100">/ {totalProducts}</span>
            </div>

            <button onclick={openCreate}
              class="flex items-center justify-center gap-2 p-2.5 sm:px-4 sm:py-2 text-[10px] font-bold tracking-widest font-mono uppercase bg-[#FFB800]/10 border border-[#FFB800]/30 text-[#FFB800] hover:bg-[#FFB800]/20 hover:text-white rounded-xl transition-all duration-300"
              title="Add Product"
            >
              <Plus size={14} /> <span class="hidden sm:inline">Add_Product</span>
            </button>
            <button onclick={loadProducts} title="Force Resync"
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
  </div>

  {#if showForm}
    <ProductForm
      {editingId}
      bind:formName bind:formSku bind:formPrice bind:formStock bind:formCategory bind:formStatus
      {categories}
      onSave={save}
      onClose={() => (showForm = false)}
    />
  {/if}

  <div class="flex-1 overflow-y-auto custom-scrollbar relative">
    {#if isLoading}
      <div class="h-full flex items-center justify-center animate-pulse">
        <span class="text-[9px] font-mono text-[#FFB800]/40 uppercase tracking-[0.3em]">Loading Catalog...</span>
      </div>
    {:else}
      <div class="pl-6 border-l border-white/5 ml-4 my-2 mb-[80px]">
        <ProductTable
          {products}
          {selectedIds}
          statusMap={STATUS_MAP}
          {formatCurrency}
          onToggleSelect={toggleSelect}
          onEdit={openEdit}
          onDelete={async (id) => {
            try {
              await apiClient.post("/api/v1/products/bulk-delete", { ids: [id] });
              await loadProducts();
            } catch (err) { nanobot.showToast("Xóa sản phẩm thất bại", "error"); }
          }}
        />
      </div>
    {/if}
  </div>

  <div class="absolute bottom-0 left-0 right-0">
    <OrderPagination
      bind:currentPage
      {totalPages}
      {pageSize}
      totalItems={totalProducts}
    />
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
  }
</style>
