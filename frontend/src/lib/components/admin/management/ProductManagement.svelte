<script lang="ts">
  import { fade } from "svelte/transition";
  import Plus from "lucide-svelte/icons/plus";
  import Search from "lucide-svelte/icons/search";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Eye from "lucide-svelte/icons/eye";
  import ChevronUp from "lucide-svelte/icons/chevron-up";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import type { Product, BaseWidgetProps, TierVariation, ProductVariant } from "$lib/types";
  import { formatCurrency, slugify } from "$lib/utils/format";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import ProductStats from "./ProductStats.svelte";
  import ProductToolbar from "./ProductToolbar.svelte";
  import ProductForm from "./ProductForm.svelte";
  import ProductTable from "./ProductTable.svelte";
  import OrderPagination from "./OrderPagination.svelte";

  let { data = {} } = $props<BaseWidgetProps>();

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
  let isSaving = $state(false);

  let formName = $state("");
  let formSku = $state("");
  let formPrice = $state(0);
  let formDiscountPrice = $state(0);
  let formStock = $state(0);
  let formCategory = $state("");
  let formStatus = $state<"active" | "draft">("draft");
  let formShortDescription = $state("");
  let formDescription = $state("");
  let formSlug = $state("");
  let formSeoTitle = $state("");
  let formSeoDescription = $state("");
  let formSeoKeywords = $state("");
  let formImages = $state<string[]>([]);
  let formMobileImages = $state<string[]>([]);
  let formAttributes = $state<Record<string, string | number | boolean | null>>({});
  let formMetadata = $state<Product["metadata"]>({ landing_type: 'standard' });
  let formTierVariations = $state<Product["tierVariations"]>([]);
  let formVariants = $state<Product["variants"]>([]);
  let generateSlug = (n: string) => slugify(n);


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
        categories.length ? Promise.resolve(null) : apiClient.get<{ data: Record<string, unknown>[]; total: number }>("/api/v1/categories"),
      ]);
      products = pRes.data;
      totalProducts = pRes.total;

      if (cData && cData.data) {
        const opts: CategoryOption[] = [];
        for (const c of cData.data) {
          opts.push({ id: c.id as string, name: c.name as string });
          (c.children as Record<string, unknown>[] || []).forEach((ch) => {
            opts.push({ id: ch.id as string, name: `${c.name} / ${ch.name}` });
          });
        }
        categories = opts;
      }
    } catch (err: unknown) {
      const error = err as Error;
      nanobot.showToast(`Lỗi tải sản phẩm: ${error.message}`, "error");
      products = [];
      totalProducts = 0;
    } finally {
      isLoading = false;
    }
  }

  $effect(() => { loadProducts(); });

  // V22: Voice Mutation Injection - Product Management
  $effect(() => {
    const data = nanobot.currentData as Record<string, unknown>;
    const action = nanobot.commandAction;

    if (data?.ui_action === "show_product_management" && data?.intent_type === "MUTATE" && !showForm) {
      editingId = null;
      formName = (data?.name as string) || (data?.title as string) || "";
      formSku = (data?.sku as string) || "";
      formPrice = Number(data?.price) || 0;
      formStock = Number(data?.stock) || 0;
      formCategory = (data?.category as string) || "";
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

  let searchTimer: ReturnType<typeof setTimeout> | undefined;
  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { searchTerm = val; currentPage = 1; }, 400);
  }

  function handleFilterChange(filter: string) {
    if (activeFilter !== filter) { activeFilter = filter; currentPage = 1; }
  }

  function openCreate() {
    editingId = null;
    formName = ""; formSku = ""; formPrice = 0; formDiscountPrice = 0; formStock = 0; formCategory = ""; formStatus = "draft";
    formShortDescription = ""; formDescription = ""; formSlug = ""; formSeoTitle = ""; formSeoDescription = ""; formSeoKeywords = "";
    formImages = []; formMobileImages = []; formAttributes = {};
    formMetadata = { landing_type: 'standard' };
    formTierVariations = []; formVariants = [];
    showForm = true;
  }

  interface RawTierVariation {
    name: string;
    options: string[];
    images: (string | null)[];
  }

  interface RawVariant {
    id: string;
    tierIndex?: number[];
    tier_index?: number[];
    sku?: string;
    price: number | string;
    discountPrice?: number | string;
    discount_price?: number | string;
    stock: number | string;
  }

  interface RawProduct extends Product {
    discount_price?: number;
    category_id?: string;
    categoryId?: string | null;
    short_description?: string;
    shortDescription?: string | null;
    seo_title?: string;
    seoTitle?: string | null;
    seo_description?: string;
    seoDescription?: string | null;
    seo_keywords?: string;
    seoKeywords?: string | null;
    tierVariations?: RawTierVariation[];
    tier_variations?: RawTierVariation[];
    variants?: RawVariant[];
  }

  async function openEdit(productOrId: Product | string) {
    let p: RawProduct;
    const id = typeof productOrId === "string" ? productOrId : productOrId.id;

    if (!id) {
      nanobot.showToast("ID sản phẩm không hợp lệ", "error");
      return;
    }

    isSaving = true; // Show loading state briefly
    try {
      console.log(`[Sync] Fetching product details for ${id}...`);
      // Force cache-busting to ensure we get the latest DB state after an update
      p = await apiClient.get<RawProduct>(`/api/v1/products/${id}`, { params: { _cb: Date.now().toString() } });

      if (!p) throw new Error("Không nhận được phản hồi từ máy chủ");

      console.log(`[Sync] Loaded product ${id} with ${p.variants?.length || 0} variants`);

      editingId = p.id;
      formName = p.name || "";
      formSku = p.sku || "";
      formPrice = Number(p.price || 0);
      formDiscountPrice = Number(p.discountPrice ?? p.discount_price ?? 0);
      formStock = Number(p.stock || 0);
      formCategory = p.categoryId ?? p.category_id ?? "";
      formStatus = (p.status || "draft").toLowerCase() as "active" | "draft";
      if ((formStatus as string) === "archived") formStatus = "draft";

      formShortDescription = p.shortDescription ?? p.short_description ?? "";
      formDescription = p.description || "";
      formSlug = p.slug || "";
      formSeoTitle = p.seoTitle ?? p.seo_title ?? "";
      formSeoDescription = p.seoDescription ?? p.seo_description ?? "";
      formSeoKeywords = p.seoKeywords ?? p.seo_keywords ?? "";
      formImages = p.images || [];
      formMobileImages = p.mobileImages ?? (p as any).mobile_images ?? [];
      formAttributes = p.attributes || {};
      formMetadata = p.metadata || { landing_type: 'standard' };

      // R102 Defense: map potential snake_case to camelCase
      const rawTierVariations = (p.tierVariations ?? p.tier_variations ?? []) as RawTierVariation[];
      formTierVariations = Array.isArray(rawTierVariations) ? rawTierVariations.map((tv: RawTierVariation) => ({
        name: tv.name || "",
        options: Array.isArray(tv.options) ? tv.options : [],
        images: Array.isArray(tv.images) ? tv.images : [],
        mobile_images: Array.isArray(tv.mobile_images) ? tv.mobile_images : (Array.isArray(tv.mobileImages) ? tv.mobileImages : [])
      })) : [];

      const rawVariants = p.variants ?? [];
      formVariants = Array.isArray(rawVariants) ? rawVariants.map((v: ProductVariant) => ({
        ...v,
        id: v.id,
        sku: v.sku || "",
        price: Number(v.price || 0),
        discountPrice: Number(v.discountPrice ?? v.discount_price ?? 0),
        stock: Number(v.stock || 0),
        tierIndex: v.tierIndex ?? v.tier_index ?? []
      })) : [];

      showForm = true;
      console.log(`[Sync] Edit form opened for ${id}`);
    } catch (err) {
      const error = err as Error;
      nanobot.showToast(`Lỗi tải chi tiết sản phẩm: ${error.message}`, "error");
      console.error("[Sync] openEdit Error:", err);
    } finally {
      isSaving = false;
    }
  }

  function toggleSelect(id: string) {
    const updated = new Set(selectedIds);
    updated.has(id) ? updated.delete(id) : updated.add(id);
    selectedIds = updated;
  }

  async function save() {
    if (!formName.trim()) return;

    // Validation: Price > Discount Price
    if (formDiscountPrice && Number(formDiscountPrice) >= Number(formPrice)) {
      nanobot.showToast("Giá khuyến mãi phải nhỏ hơn giá bán bản gốc", "error");
      return;
    }

    for (const v of (formVariants || [])) {
      if (v.discountPrice && Number(v.discountPrice) >= Number(v.price)) {
        nanobot.showToast(`Biến thể có giá KM (${v.discountPrice}) >= giá bán (${v.price})`, "error");
        return;
      }
    }

    isSaving = true;
    const payload = {
      name: formName.trim(), 
      sku: formSku || `SKU-${Date.now()}`,
      price: Number(formPrice), 
      discount_price: formDiscountPrice ? Number(formDiscountPrice) : null,
      stock: Number(formStock), 
      categoryId: formCategory || null, 
      status: (formStatus || "draft").toUpperCase(), // Backend expects ACTIVE/DRAFT
      shortDescription: formShortDescription,
      description: formDescription,
      slug: formSlug || generateSlug(formName),
      seoTitle: formSeoTitle,
      seoDescription: formSeoDescription,
      seoKeywords: formSeoKeywords,
      images: formImages || [],
      mobile_images: formMobileImages || [],
      attributes: formAttributes || {},
      metadata: formMetadata || {},
      tier_variations: (formTierVariations || []).map(tv => ({
        name: tv.name,
        options: tv.options,
        images: tv.images || null,
        mobile_images: tv.mobile_images || null
      })),
      variants: (formVariants || []).map(v => ({
        id: v.id || null, // Ensure id is null if missing
        sku: v.sku || "",
        price: Number(v.price),
        discount_price: v.discountPrice ? Number(v.discountPrice) : null,
        stock: Number(v.stock),
        tier_index: v.tierIndex || []
      }))
    };

    try {
      if (editingId) {
        await apiClient.patch(`/api/v1/products/${editingId}`, payload);
        editingId = null;
        showForm = false;
        // Always reload the entire list to ensure everything (counts, stats, statuses) is perfectly synced
        await loadProducts();
        nanobot.showToast("Dữ liệu sản phẩm đã được đồng bộ chuẩn xác", "success");
      } else {
        await apiClient.post<Product>("/api/v1/products", payload);
        nanobot.showToast("Đã xuất bản sản phẩm mới", "success");
        showForm = false;
        await loadProducts();
      }
    } catch (err: unknown) { 
      const msg = err?.message || "Lưu sản phẩm thất bại";
      nanobot.showToast(msg, "error"); 
    } finally {
      isSaving = false;
    }
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
        <ProductStats {stats} />
      </div>
    {/if}

    <ProductToolbar
      {searchInput}
      {activeFilter}
      bind:pageSize
      {selectedIds}
      {totalProducts}
      {isLoading}
      bind:isHeaderCollapsed
      {STATUS_MAP}
      onSearchInput={handleSearchInput}
      onFilterChange={handleFilterChange}
      onPageSizeChange={() => { currentPage = 1; }}
      onBulkActivate={() => bulk("act")}
      onBulkDelete={() => bulk("del")}
      onOpenCreate={openCreate}
      onLoadProducts={loadProducts}
    />
  </div>

  <!-- ProductForm Modal Layer -->
  <ProductForm
    {editingId}
    isOpen={showForm}
    bind:formName bind:formSku bind:formPrice bind:formDiscountPrice bind:formStock bind:formCategory bind:formStatus
    bind:formShortDescription bind:formDescription bind:formSlug bind:formSeoTitle bind:formSeoDescription bind:formSeoKeywords
    bind:formImages bind:formMobileImages bind:formAttributes bind:formMetadata bind:formTierVariations bind:formVariants
    {categories}
    onSave={save}
    onClose={() => (showForm = false)}
    {generateSlug}
    {isSaving}
  />

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
          onToggleSelect={toggleSelect}
          onEdit={openEdit}
          onDelete={async (id) => {
            try { await apiClient.post("/api/v1/products/bulk-delete", { ids: [id] }); await loadProducts(); }
            catch { nanobot.showToast("Xóa sản phẩm thất bại", "error"); }
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
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 20px; }
</style>
