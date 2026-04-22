<script lang="ts">
  import { fade } from "svelte/transition";
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
  let activeCategory = $state("");
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
  let formIsAiFeatured = $state(false);
  let generateSlug = (n: string) => slugify(n);

  let pageSize = $state(50);
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

  async function loadProducts() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({ limit: pageSize.toString(), offset: offset.toString() });
      if (activeFilter !== "all") params.append("status", activeFilter);
      if (activeCategory) params.append("category_id", activeCategory);
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
  
  function handleCategoryChange(catId: string) {
    if (activeCategory !== catId) { activeCategory = catId; currentPage = 1; }
  }

  function openCreate() {
    editingId = null;
    formName = ""; formSku = ""; formPrice = 0; formDiscountPrice = 0; formStock = 0; formCategory = ""; formStatus = "draft";
    formShortDescription = ""; formDescription = ""; formSlug = ""; formSeoTitle = ""; formSeoDescription = ""; formSeoKeywords = "";
    formImages = []; formMobileImages = []; formAttributes = {};
    formMetadata = { landing_type: 'standard' };
    formTierVariations = []; formVariants = [];
    formIsAiFeatured = false;
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
    if (!id) { nanobot.showToast("ID sản phẩm không hợp lệ", "error"); return; }
    isSaving = true;
    try {
      p = await apiClient.get<RawProduct>(`/api/v1/products/${id}`, { params: { _cb: Date.now().toString() } });
      if (!p) throw new Error("Không nhận được phản hồi từ máy chủ");
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
      formIsAiFeatured = p.isAiFeatured ?? (p as any).is_ai_featured ?? false;
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
        discountPercent: Number((v as any).discountPercent ?? (v as any).discount_percent ?? 0),
        stock: Number(v.stock || 0),
        tierIndex: v.tierIndex ?? v.tier_index ?? [],
        is_default: v.is_default || false
      })) : [];
      showForm = true;
    } catch (err) {
      nanobot.showToast(`Lỗi tải chi tiết sản phẩm: ${(err as Error).message}`, "error");
    } finally {
      isSaving = false;
    }
  }

  function toggleSelect(id: string) {
    const updated = new Set(selectedIds);
    updated.has(id) ? updated.delete(id) : updated.add(id);
    selectedIds = updated;
  }

  function toggleSelectAll() {
    const allOnPage = products.map(p => p.id);
    const isAllSelected = allOnPage.length > 0 && allOnPage.every(id => selectedIds.has(id));
    const updated = new Set(selectedIds);
    if (isAllSelected) { allOnPage.forEach(id => updated.delete(id)); }
    else { allOnPage.forEach(id => updated.add(id)); }
    selectedIds = updated;
  }

  async function bulkAiFeatured(enabled: boolean) {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    isSaving = true;
    try {
      await apiClient.post("/api/v1/products/bulk-update", { ids, data: { is_ai_featured: enabled } });
      nanobot.showToast(`Đã ${enabled ? 'bật' : 'tắt'} AI Featured`, "success");
      await loadProducts();
    } catch (err) { nanobot.showToast("Cập nhật hàng loạt thất bại", "error"); }
    finally { isSaving = false; }
  }

  async function bulkDiscount() {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;

    let title = "Cập nhật giá khuyến mãi hàng loạt";
    let message = `Bạn muốn thiết lập giá khuyến mãi cho ${ids.length} sản phẩm? (Để trống để xóa)`;

    if (ids.length === 1) {
      const p = products.find(x => x.id === ids[0]) as any;
      if (p) {
        title = "Cập nhật giá khuyến mãi";
        const currentDiscount = p.discountPrice ?? p.discount_price ?? 0;
        message = `Sản phẩm: ${p.name}\nGiá gốc: ${formatCurrency(p.price)}`;
        if (currentDiscount > 0) {
          message += `\nGiá KM hiện tại: ${formatCurrency(currentDiscount)}`;
        }
        message += `\n\n(Để trống để xóa giá KM hiện tại)`;
      }
    }

    const result = await nanobot.showConfirm({
      title,
      message,
      isPrompt: true,
      promptPlaceholder: "Nhập giá khuyến mãi...",
    });
    if (result === null) return;
    isSaving = true;
    try {
      const discount_price = result.trim() === "" ? null : Number(result);
      if (discount_price !== null && isNaN(discount_price)) throw new Error("Giá không hợp lệ");
      await apiClient.post("/api/v1/products/bulk-update", { ids, data: { discount_price } });
      nanobot.showToast(`Đã cập nhật giá khuyến mãi`, "success");
      await loadProducts();
    } catch (err) { nanobot.showToast("Cập nhật thất bại: " + (err as Error).message, "error"); }
    finally { isSaving = false; }
  }

  async function save() {
    if (!formName.trim()) return;
    if (formDiscountPrice && Number(formDiscountPrice) >= Number(formPrice)) {
      nanobot.showToast("Giá khuyến mãi phải nhỏ hơn giá bán gốc", "error"); return;
    }
    isSaving = true;
    const payload = {
      name: formName.trim(),
      sku: formSku || `SKU-${Date.now()}`,
      price: Number(formPrice),
      discount_price: formDiscountPrice ? Number(formDiscountPrice) : null,
      discount_percent: (formVariants.length === 0 && formPrice > 0 && formDiscountPrice > 0) 
        ? Math.round(((formPrice - formDiscountPrice) / formPrice) * 10000) / 100 
        : null,
      stock: Number(formStock),
      categoryId: formCategory || null,
      status: (formStatus || "draft").toUpperCase(),
      is_ai_featured: formIsAiFeatured,
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
        name: tv.name, options: tv.options, images: tv.images || null, mobile_images: tv.mobile_images || null
      })),
      variants: (formVariants || []).map(v => ({
        id: v.id || null, 
        sku: v.sku || "", 
        price: Number(v.price), 
        discount_price: v.discountPrice ? Number(v.discountPrice) : null,
        discount_percent: v.discountPercent || null,
        stock: Number(v.stock), 
        tier_index: v.tierIndex || [],
        is_default: v.is_default || false,
        attributes: v.attributes || { combo_qty: null, gifts: [] }
      }))
    };
    try {
      if (editingId) {
        await apiClient.patch(`/api/v1/products/${editingId}`, payload);
        editingId = null; showForm = false; await loadProducts();
        nanobot.showToast("Đã đồng bộ thay đổi", "success");
      } else {
        await apiClient.post<Product>("/api/v1/products", payload);
        nanobot.showToast("Đã xuất bản sản phẩm mới", "success");
        showForm = false; await loadProducts();
      }
    } catch (err: unknown) {
      nanobot.showToast((err as any)?.message || "Lưu thất bại", "error");
    } finally { isSaving = false; }
  }

  async function bulk(type: "del" | "act" | "deact") {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    try {
      if (type === "del") await apiClient.post("/api/v1/products/bulk-delete", { ids });
      else if (type === "act") await apiClient.post("/api/v1/products/bulk-activate", { ids });
      else await apiClient.post("/api/v1/products/bulk-update", { ids, data: { status: 'DRAFT' } });
      selectedIds = new Set();
      await loadProducts();
      nanobot.showToast(`Đã thực hiện thao tác hàng loạt`, "success");
    } catch (err) { nanobot.showToast("Thao tác hàng loạt thất bại", "error"); }
  }
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505] isolation-auto">
  <!-- Fixed Background Layer (Rule R03: Ultra-Fast UX) -->
  <div class="absolute inset-0 bg-[#050505] pointer-events-none -z-10"></div>
  
  <div class="flex flex-col gap-6 p-6 border-b border-white/[0.05] relative z-10 bg-[#050505]">
    {#if !isHeaderCollapsed}
      <div transition:fade={{ duration: 200 }} class="flex flex-col gap-6">
        <ProductStats {stats} />
      </div>
    {/if}

    <ProductToolbar
      {searchInput}
      {activeFilter}
      {activeCategory}
      {categories}
      bind:pageSize
      {selectedIds}
      {totalProducts}
      {isLoading}
      bind:isHeaderCollapsed
      {STATUS_MAP}
      onSearchInput={handleSearchInput}
      onFilterChange={handleFilterChange}
      onCategoryChange={handleCategoryChange}
      onPageSizeChange={() => { currentPage = 1; }}
      onBulkActivate={() => bulk("act")}
      onBulkDeactivate={() => bulk("deact")}
      onBulkDelete={() => bulk("del")}
      onBulkAiFeatured={bulkAiFeatured}
      onBulkDiscount={bulkDiscount}
      onOpenCreate={openCreate}
      onLoadProducts={loadProducts}
    />
  </div>

  <ProductForm
    {editingId}
    isOpen={showForm}
    bind:formName bind:formSku bind:formPrice bind:formDiscountPrice bind:formStock bind:formCategory bind:formStatus
    bind:formShortDescription bind:formDescription bind:formSlug bind:formSeoTitle bind:formSeoDescription bind:formSeoKeywords
    bind:formImages bind:formMobileImages bind:formAttributes bind:formMetadata bind:formTierVariations bind:formVariants
    bind:formIsAiFeatured
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
          onToggleSelectAll={toggleSelectAll}
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
