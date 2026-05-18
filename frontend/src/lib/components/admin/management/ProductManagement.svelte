<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import type { Product, BaseWidgetProps, ProductVariant, TierVariation } from "$lib/types";
  import { formatCurrency, slugify } from "$lib/utils/format";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient } from "$lib/utils/apiClient";
  import ProductStats from "./ProductStats.svelte";
  import ProductToolbar from "./ProductToolbar.svelte";
  import ProductForm from "./ProductForm.svelte";
  import ProductTable from "./ProductTable.svelte";
  import OrderPagination from "./OrderPagination.svelte";
  import ReviewSeedingModal from "./ReviewSeedingModal.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  let { data = {} } = $props<{ data?: Record<string, unknown> }>();

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
  let isAiFeaturedOnly = $state(false);

  // Review Lab state
  let showReviewModal = $state(false);
  let reviewProduct = $state<{ id: string; name: string } | null>(null);

  function openReviewLab(product: { id: string; name: string }) {
    reviewProduct = { id: product.id, name: product.name };
    showReviewModal = true;
  }

  import type { ProductFormState } from "$lib/types";

  let formState = $state<ProductFormState>({
    name: "",
    sku: "",
    price: 0,
    discountPrice: 0,
    stock: 0,
    category: "",
    status: "draft",
    shortDescription: "",
    description: "",
    slug: "",
    seoTitle: "",
    seoDescription: "",
    seoKeywords: "",
    images: [],
    mobileImages: [],
    attributes: {},
    metadata: { landing_type: 'standard', analysis_cache: {}, analysis_metrics: {} },
    tierVariations: [],
    variants: [],
    isAiFeatured: false,
    analysisReport: {},
    marketData: { ads: [], organic_results: [], analysis: "" },
    lastMarketSync: undefined
  });

  let generateSlug = (n: string) => slugify(n);

  let pageSize = $state(50);
  const STATUS_MAP: Record<string, { label: string; color: string }> = {
    active: { label: "Đang bán", color: "#39FF14" },
    draft: { label: "Nháp", color: "#FFB800" },
    archived: { label: "Lưu trữ", color: "#666" },
  };

  const totalPages = $derived(Math.max(1, Math.ceil(totalProducts / pageSize)));
  const isAllSelected = $derived(products.length > 0 && products.every(p => selectedIds.has(p.id)));
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
      if (isAiFeaturedOnly) params.append("featured_only", "true");

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

  $effect(() => { 
    // Trigger reload only on these primary state changes
    currentPage; pageSize; activeFilter; activeCategory; searchTerm; isAiFeaturedOnly;

    untrack(() => {
      loadProducts(); 
    });
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
  
  function handleCategoryChange(catId: string) {
    if (activeCategory !== catId) { activeCategory = catId; currentPage = 1; }
  }

  function openCreate() {
    editingId = null;
    formState.name = ""; formState.sku = ""; formState.price = 0; formState.discountPrice = 0; formState.stock = 0; formState.category = ""; formState.status = "draft";
    formState.shortDescription = ""; formState.description = ""; formState.slug = ""; formState.seoTitle = ""; formState.seoDescription = ""; formState.seoKeywords = "";
    formState.images = []; formState.mobileImages = []; formState.attributes = {};
    formState.metadata = { landing_type: 'standard', analysis_cache: {}, analysis_metrics: {} };
    formState.tierVariations = []; formState.variants = [];
    formState.isAiFeatured = false;
    formState.analysisReport = {};
    formState.marketData = { ads: [], organic_results: [], analysis: "" };
    formState.lastMarketSync = undefined;
    showForm = true;
  }


  async function openEdit(productOrId: Product | string) {
    const id = typeof productOrId === "string" ? productOrId : productOrId.id;
    if (!id) { nanobot.showToast("ID sản phẩm không hợp lệ", "error"); return; }
    isSaving = true;
    try {
      const p = await apiClient.get<Product>(`/api/v1/products/${id}`, { params: { _cb: Date.now().toString() } });
      if (!p) throw new Error("Không nhận được phản hồi từ máy chủ");
      console.log(`[ProductManagement] Fresh description for ${id}. Len: ${p.description?.length}`);
      editingId = p.id;
      formState.name = p.name || "";
      formState.sku = p.sku || "";
      formState.price = Number(p.price || 0);
      formState.discountPrice = Number(p.discountPrice ?? p.discount_price ?? 0);
      formState.stock = Number(p.stock || 0);
      formState.category = p.categoryId ?? p.category_id ?? "";
      let status = (p.status || "draft").toLowerCase() as "active" | "draft" | "archived";
      if (status === "archived") status = "draft";
      formState.status = status;
      formState.shortDescription = p.shortDescription ?? p.short_description ?? "";
      formState.description = p.description || "";
      formState.slug = p.slug || "";
      formState.seoTitle = p.seoTitle ?? p.seo_title ?? "";
      formState.seoDescription = p.seoDescription ?? p.seo_description ?? "";
      formState.seoKeywords = p.seoKeywords ?? p.seo_keywords ?? "";
      formState.images = p.images || [];
      formState.mobileImages = p.mobileImages ?? p.mobile_images ?? [];
      formState.attributes = p.attributes || {};
      formState.metadata = p.metadata || { landing_type: 'standard', analysis_cache: {}, analysis_metrics: {} };
      if (!formState.metadata.analysis_cache) formState.metadata.analysis_cache = {};
      if (!formState.metadata.analysis_metrics) formState.metadata.analysis_metrics = {};
      formState.isAiFeatured = p.isAiFeatured ?? p.is_ai_featured ?? false;
      formState.analysisReport = p.analysis_report || {};
      formState.marketData = p.marketData ?? p.market_data ?? { ads: [], organic_results: [], analysis: "" };
      formState.lastMarketSync = p.lastMarketSync ?? p.last_market_sync;
      const rawTierVariations = p.tierVariations ?? p.tier_variations ?? [];
      formState.tierVariations = Array.isArray(rawTierVariations) ? rawTierVariations.map(tv => ({
        name: tv.name || "",
        options: Array.isArray(tv.options) ? tv.options : [],
        images: Array.isArray(tv.images) ? tv.images : [],
        mobile_images: Array.isArray(tv.mobile_images) ? tv.mobile_images : (Array.isArray(tv.mobileImages) ? tv.mobileImages : [])
      })) : [];
      const rawVariants = p.variants ?? [];
      formState.variants = Array.isArray(rawVariants) ? rawVariants.map((v: ProductVariant) => ({
        ...v,
        id: v.id,
        sku: v.sku || "",
        price: Number(v.price || 0),
        discountPrice: Number(v.discountPrice ?? v.discount_price ?? 0),
        discountPercent: Number(v.discountPercent ?? v.discount_percent ?? 0),
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

    const title = ids.length === 1
      ? "Cập nhật giá khuyến mãi"
      : `Cập nhật giá khuyến mãi hàng loạt (${ids.length} sản phẩm)`;

    // Build context message hiển thị thông tin sản phẩm được chọn
    let contextLines: string[] = [];
    if (ids.length === 1) {
      const p = products.find(x => x.id === ids[0]);
      if (p) {
        const currentDiscount = p.discountPrice ?? p.discount_price ?? 0;
        contextLines.push(`📦 ${p.name}`);
        contextLines.push(`💰 Giá gốc: ${formatCurrency(p.price)}`);
        if (currentDiscount > 0) contextLines.push(`🏷️ Giá KM hiện tại: ${formatCurrency(currentDiscount)}`);
      }
    } else {
      // Hiển thị preview vài sản phẩm đầu
      const previews = ids.slice(0, 3).map(id => {
        const p = products.find(x => x.id === id);
        return p ? `• ${p.name} — ${formatCurrency(p.price)}` : "";
      }).filter(Boolean);
      contextLines.push(...previews);
      if (ids.length > 3) contextLines.push(`... và ${ids.length - 3} sản phẩm khác`);
    }
    const message = contextLines.join("\n");

    const result = await nanobot.showConfirm({
      title,
      message,
      fields: [
        {
          key: "discountType",
          label: "HÌNH THỨC GIẢM GIÁ",
          type: "select",
          required: true,
          defaultValue: "percent",
          options: [
            { value: "percent", label: "🔥 Giảm theo phần trăm (%)" },
            { value: "fixed",   label: "💰 Nhập giá khuyến mãi trực tiếp" },
            { value: "clear",   label: "🗑️ Xoá giá khuyến mãi hiện tại" }
          ]
        },
        {
          key: "discountValue",
          label: "MỨC GIẢM (%) HOẶC GIÁ KM MỚI",
          type: "text",
          required: false,
          placeholder: "VD: 10 (giảm 10%) hoặc 250000 (giá KM trực tiếp)",
          defaultValue: ""
        }
      ]
    });

    if (result === null) return;
    const formResult = result as Record<string, string>;
    const discountType = formResult["discountType"] ?? "percent";
    const discountValue = (formResult["discountValue"] ?? "").trim();

    isSaving = true;
    try {
      if (discountType === "clear") {
        // Hình thức 1: Xoá giá khuyến mãi - 1 request bulk đơn giản
        await apiClient.post("/api/v1/products/bulk-update", {
          ids,
          data: { discount_price: null }
        });
        nanobot.showToast(`Đã xoá giá khuyến mãi cho ${ids.length} sản phẩm`, "success");

      } else if (discountType === "fixed") {
        // Hình thức 2: Nhập giá khuyến mãi trực tiếp - 1 request bulk
        if (!discountValue) throw new Error("Vui lòng nhập giá khuyến mãi");
        const fixedPrice = Number(discountValue);
        if (isNaN(fixedPrice) || fixedPrice < 0) throw new Error("Giá không hợp lệ");

        // Kiểm tra bảo vệ: giá KM phải nhỏ hơn giá gốc của TẤT CẢ sản phẩm được chọn
        const violators = ids
          .map(id => products.find(p => p.id === id))
          .filter(p => p && fixedPrice >= p.price);
        if (violators.length > 0) {
          throw new Error(`Giá KM phải nhỏ hơn giá gốc. ${violators.length} sản phẩm vi phạm điều kiện.`);
        }

        await apiClient.post("/api/v1/products/bulk-update", {
          ids,
          data: { discount_price: fixedPrice }
        });
        nanobot.showToast(`Đã cập nhật giá KM ${formatCurrency(fixedPrice)} cho ${ids.length} sản phẩm`, "success");

      } else {
        // Hình thức 3: Giảm theo % — tính toán riêng cho từng sản phẩm rồi gửi song song
        if (!discountValue) throw new Error("Vui lòng nhập mức phần trăm giảm");
        const rawPercent = parseFloat(discountValue.replace("%", "").trim());
        if (isNaN(rawPercent) || rawPercent <= 0 || rawPercent >= 100) {
          throw new Error("Phần trăm giảm phải từ 1% đến 99%");
        }

        // Tính toán giá KM riêng cho từng sản phẩm và gửi song song (HTTP/2 multiplexing)
        const patchTasks = ids.map(id => {
          const p = products.find(x => x.id === id);
          if (!p) return Promise.resolve();
          const newDiscountPrice = Math.round(p.price * (1 - rawPercent / 100));
          const discountPercent = rawPercent;
          return apiClient.patch(`/api/v1/products/${id}`, {
            discount_price: newDiscountPrice,
            discount_percent: discountPercent
          });
        });

        await Promise.all(patchTasks);
        nanobot.showToast(`Đã áp dụng giảm giá ${rawPercent}% cho ${ids.length} sản phẩm`, "success");
      }

      await loadProducts();
    } catch (err) {
      nanobot.showToast("Cập nhật thất bại: " + (err as Error).message, "error");
    } finally {
      isSaving = false;
    }
  }

  async function save() {
    if (!formState.name.trim()) return;
    if (formState.discountPrice && Number(formState.discountPrice) >= Number(formState.price)) {
      nanobot.showToast("Giá khuyến mãi phải nhỏ hơn giá bán gốc", "error"); return;
    }
    isSaving = true;
    console.log(`[ProductManagement] Saving product ${editingId}. Description len: ${formState.description?.length}`);
    const payload = {
      name: formState.name.trim(),
      sku: formState.sku || `SKU-${Date.now()}`,
      price: Number(formState.price),
      discount_price: formState.discountPrice ? Number(formState.discountPrice) : null,
      discount_percent: (formState.variants.length === 0 && formState.price > 0 && formState.discountPrice && formState.discountPrice > 0) 
        ? Math.round(((formState.price - formState.discountPrice) / formState.price) * 10000) / 100 
        : null,
      stock: Number(formState.stock),
      categoryId: formState.category || null,
      status: (formState.status || "draft").toUpperCase(),
      is_ai_featured: formState.isAiFeatured,
      shortDescription: formState.shortDescription,
      description: formState.description,
      slug: formState.slug || generateSlug(formState.name),
      seoTitle: formState.seoTitle,
      seoDescription: formState.seoDescription,
      seoKeywords: formState.seoKeywords,
      images: formState.images || [],
      mobile_images: formState.mobileImages || [],
      attributes: formState.attributes || {},
      metadata: formState.metadata || {},
      analysis_report: formState.analysisReport || {},
      tier_variations: (formState.tierVariations || []).map(tv => ({
        name: tv.name, options: tv.options, images: tv.images || null, mobile_images: tv.mobile_images || null
      })),
      variants: (formState.variants || []).map(v => ({
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
      nanobot.showToast((err as Error)?.message || "Lưu thất bại", "error");
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

  async function syncMarket(id: string) {
    try {
      const res = await apiClient.post<{ message: string; data: Product["market_data"] }>(`/api/v1/products/${id}/sync-market`);
      const newData = res.data;
      if (!newData) throw new Error("Không nhận được dữ liệu từ máy chủ");

      // Update local products array with new market data
      products = products.map(p => p.id === id ? { 
        ...p, 
        market_data: newData,
        marketData: newData, // sync both variations for safety
        last_market_sync: new Date().toISOString(),
        lastMarketSync: new Date().toISOString()
      } : p);
      nanobot.showToast("Đã cập nhật tình báo thị trường", "success");
    } catch (err) {
      nanobot.showToast("Đồng bộ giá thất bại", "error");
      throw err;
    }
  }
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505] isolation-auto">
  <!-- Fixed Background Layer (Rule R03: Ultra-Fast UX) -->
  <div class="absolute inset-0 bg-[#050505] pointer-events-none -z-10"></div>
  
  <div class="flex-1 overflow-y-auto custom-scrollbar relative">
    {#if !isHeaderCollapsed}
      <div transition:fade={{ duration: 200 }} class="flex flex-col gap-6 p-6 border-b border-white/[0.05] bg-[#050505]">
        <ProductStats {stats} />
      </div>
    {/if}

    <div class="sticky top-0 p-6 pb-4 bg-[#050505]/95 backdrop-blur-xl border-b border-white/5" style="z-index: {Z_INDEX_ADMIN.TOOLBAR_SUB};">
      <ProductToolbar
        {searchInput}
        {activeFilter}
        {activeCategory}
        {categories}
        bind:pageSize
        {selectedIds}
        {isAllSelected}
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
        onToggleSelectAll={toggleSelectAll}
        onOpenCreate={openCreate}
        onLoadProducts={loadProducts}
        isAiFeaturedOnly={isAiFeaturedOnly}
        onAiFeaturedOnlyChange={(val) => { isAiFeaturedOnly = val; currentPage = 1; }}
      />
    </div>

    {#if isLoading}
      <div class="h-[400px] flex items-center justify-center animate-pulse">
        <span class="text-[9px] font-mono text-[#FFB800]/40 tracking-[0.3em]">Loading Catalog...</span>
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
          onOpenReviewLab={openReviewLab}
          onDelete={async (id) => {
            try { await apiClient.post("/api/v1/products/bulk-delete", { ids: [id] }); await loadProducts(); }
            catch { nanobot.showToast("Xóa sản phẩm thất bại", "error"); }
          }}
          onSyncMarket={syncMarket}
        />
      </div>
    {/if}
  </div>

  <div class="relative z-10 shrink-0 bg-[#050505] border-t border-white/5">
    <OrderPagination
      bind:currentPage
      {totalPages}
      {pageSize}
      totalItems={totalProducts}
    />
  </div>

  <!-- Render Form outside scroll to ensure fixed/absolute positioning works without clipping -->
  <ProductForm
    {editingId}
    isOpen={showForm}
    bind:formState={formState}
    {categories}
    onSave={save}
    onClose={() => { showForm = false; nanobot.toggleExpand(false); }}
    {generateSlug}
    {isSaving}
  />

  <!-- Review Seeding Lab Modal -->
  {#if reviewProduct}
    <ReviewSeedingModal
      productId={reviewProduct.id}
      productName={reviewProduct.name}
      isOpen={showReviewModal}
      onClose={() => { showReviewModal = false; reviewProduct = null; }}
    />
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 20px; }
</style>
