<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Newspaper from "@lucide/svelte/icons/newspaper";
  import type { Article, BaseWidgetProps } from "$lib/types";
  import type { AnalysisCache, CampaignMetrics } from "$lib/state/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { apiClient, ApiError } from "$lib/utils/apiClient";
  import { slugify } from "$lib/utils/format";
  import { onMount, tick } from "svelte";

  import NewsToolbar from "./NewsToolbar.svelte";
  import NewsTable from "./NewsTable.svelte";
  import OrderPagination from "./OrderPagination.svelte";
  import NewsForm from "./NewsForm.svelte";

  let { data = {} } = $props<BaseWidgetProps>();

  let categories = $state<string[]>([]);

  // --- STATE ---
  let articles = $state<Article[]>([]);
  let totalArticles = $state(0);
  let isLoading = $state(true);
  let searchTerm = $state("");
  let searchInput = $state("");
  let activeTab = $state("all");
  let activeCategoryFilter = $state("Bài viết");
  let currentPage = $state(1);
  let editingId = $state<string | null>(null);
  let selectedIds = $state<Set<string>>(new Set());
  let formTitle = $state("");
  let formCategory = $state<string>("");
  let formStatus = $state("DRAFT");
  let formExcerpt = $state("");
  let formContent = $state("");
  let formSlug = $state("");
  let formSeoTitle = $state("");
  let formSeoDescription = $state("");
  let formSeoKeywords = $state("");
  let formSeoOgImage = $state<string | null>(null);
  let formFeaturedImage = $state<string | null>(null);
  let formFaqs = $state<{ question: string; answer: string }[]>([]);
  // CNS V86.5: Neural Analysis cache/metrics — đồng nhất với ProductForm & DraftStep
  let formAnalysisCache = $state<AnalysisCache>({});
  let formAnalysisMetrics = $state<CampaignMetrics>({});
  let formAnalysisReport = $state<Record<string, any>>({});
  let showDraftForm = $state(false);
  let isHeaderCollapsed = $state(false);

  let pageSize = $state(10);
  let showPurgeConfirm = $state(false);
  let purgeTargetId = $state<string | null>(null);
  let isBulkPurge = $state(false);
  let isSaving = $state(false);
  let errors = $state<Record<string, string>>({});
  const totalPages = $derived(Math.max(1, Math.ceil(totalArticles / pageSize)));

  // --- SERVER-SIDE FETCH ---
  async function loadArticles() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({ limit: pageSize.toString(), offset: offset.toString() });
      if (activeTab !== "all") params.append("status", activeTab);
      if (activeCategoryFilter !== "all") params.append("category", activeCategoryFilter);
      if (searchTerm) params.append("search", searchTerm);

      const res = await apiClient.get<{ data: Article[]; total: number }>(`/api/v1/articles?${params.toString()}`);
      articles = res.data;
      totalArticles = res.total;
    } catch {
      articles = [];
      totalArticles = 0;
    } finally {
      isLoading = false;
    }
  }

  async function loadCategories() {
    try {
      const res = await apiClient.get<string[]>("/api/v1/articles/categories");
      categories = res;
      if (!formCategory && categories.length > 0) {
        formCategory = categories[0];
      }
    } catch (err) {
      console.error("Failed to load news categories:", err);
      // Fallback
      categories = ["Bài viết", "Chính sách"];
      if (!formCategory) formCategory = categories[0];
    }
  }

  onMount(() => { 
    loadArticles(); 
    loadCategories();
  });

  // V22: Voice Mutation Injection - News Management
  $effect(() => {
    const data = nanobot.currentData;
    const action = nanobot.commandAction;

    if (
      data?.ui_action === "show_news_management" &&
      data?.intent_type === "MUTATE" &&
      !showDraftForm
    ) {
      editingId = null;
      formTitle =
        (data?.title as string) ||
        (data?.name as string) ||
        (String((data?.entities as Record<string, unknown>)?.name || "")) ||
        "";
      formCategory = (data?.category as string) || (categories[0] || "");
      formExcerpt = (data?.excerpt as string) || "";
      showDraftForm = true;
      nanobot.clearCurrentData();
      return;
    }

    if (action?.entity === "news" || action?.entity === "article") {
      if (action.verb === "create") {
        if (nanobot.consumeCommand("create", action.entity)) {
          openCreate();
          if (action.args) formTitle = action.args;
        }
      } else if (action.verb === "search" && action.args) {
        if (nanobot.consumeCommand("search", action.entity)) {
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
    searchTimer = setTimeout(() => { searchTerm = val; currentPage = 1; loadArticles(); }, 400);
  }

  function handleTabChange(tab: string) {
    if (activeTab !== tab) { activeTab = tab; currentPage = 1; loadArticles(); }
  }

  function handleCategoryChange(cat: string) {
    if (activeCategoryFilter !== cat) { activeCategoryFilter = cat; currentPage = 1; loadArticles(); }
  }

  function generateSlug(title: string) {
    return slugify(title);
  }

  function openCreate() {
    editingId = null;
    formTitle = ""; formCategory = categories[0] || ""; formExcerpt = "";
    formContent = ""; formSlug = ""; formSeoTitle = "";
    formSeoDescription = ""; formSeoKeywords = ""; formSeoOgImage = null; formFeaturedImage = null;
    formFaqs = [];
    formStatus = "DRAFT";
    formAnalysisCache = {};
    formAnalysisMetrics = {};
    formAnalysisReport = {};
    showDraftForm = true;
  }

  async function openEdit(a: Article) {
    try {
      nanobot.showToast("Đang tải dữ liệu...", "info");
      const fullArticle = await apiClient.get<Article>(`/api/v1/articles/${a.id}`);
      editingId = fullArticle.id;
      formTitle = fullArticle.title; formCategory = fullArticle.category;
      formExcerpt = fullArticle.excerpt || "";
      formContent = fullArticle.content || "";
      formSlug = fullArticle.slug;
      formSeoTitle = fullArticle.seoTitle || "";
      formSeoDescription = fullArticle.seoDescription || "";
      formSeoKeywords = fullArticle.seoKeywords || "";
      formSeoOgImage = fullArticle.seoOgImage || null;
      formFeaturedImage = fullArticle.featuredImage || null;
      const meta = fullArticle.metadata || {};
      formFaqs = meta.faqs || [];
      // CNS V86.5: Hydrate analysis cache để khôi phục highlights sau F5
      formAnalysisCache = meta.analysis_cache || {};
      formAnalysisMetrics = meta.analysis_metrics || {};
      formAnalysisReport = fullArticle.analysis_report || {};
      formStatus = fullArticle.status;
      showDraftForm = true;
    } catch {
      nanobot.showToast("Dạ sếp, không lấy được chi tiết bài viết.", "error");
    }
  }

  async function saveArticle() {
    errors = {};
    if (!formTitle.trim()) errors.title = "Tiêu đề không thể để trống sếp ơi";
    if (!formSlug.trim() && editingId) errors.slug = "Đường dẫn không hợp lệ";
    if (Object.keys(errors).length > 0) {
      nanobot.showToast("Thông tin chưa đầy đủ!", "error");
      return;
    }

    isSaving = true;
    try {
      const payload = {
        title: formTitle, category: formCategory, excerpt: formExcerpt,
        content: formContent, slug: formSlug || generateSlug(formTitle),
        status: formStatus, seo_title: formSeoTitle,
        seo_description: formSeoDescription,
        seo_keywords: formSeoKeywords,
        seo_og_image: formSeoOgImage,
        featured_image: formFeaturedImage,
        analysis_report: formAnalysisReport || {},
        // CNS V86.5: Persist analysis cache để highlights không bị mất sau F5
        metadata: { 
          faqs: formFaqs,
          analysis_cache: formAnalysisCache,
          analysis_metrics: formAnalysisMetrics
        },
      };

      if (editingId) {
        await apiClient.patch(`/api/v1/articles/${editingId}`, payload);
        nanobot.showToast("Đã đồng bộ Neural. Cập nhật bài viết thành công!", "success");
      } else {
        await apiClient.post("/api/v1/articles", payload);
        nanobot.showToast("Khởi tạo hoàn tất. Bài viết đã được đăng tải!", "success");
      }
      showDraftForm = false;
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError
        ? String((err.data as Record<string, unknown>)?.detail ?? "Lỗi giao thức Neural Link")
        : "Lỗi giao thức Neural Link";
      nanobot.showToast(`Neural link failed. ${detail}`, "error");
    } finally {
      isSaving = false;
    }
  }

  function toggleSelect(id: string) {
    if (id === "__all_on") { selectAll(); return; }
    if (id === "__all_off") { deselectAll(); return; }
    const n = new Set(selectedIds);
    n.has(id) ? n.delete(id) : n.add(id);
    selectedIds = n;
  }

  function selectAll() { selectedIds = new Set(articles.map(a => a.id)); }
  function deselectAll() { selectedIds = new Set(); }

  function toggleSelectAll() {
    const allOnPage = articles.map(a => a.id);
    const isAllSelected = allOnPage.length > 0 && allOnPage.every(id => selectedIds.has(id));
    const updated = new Set(selectedIds);
    if (isAllSelected) { allOnPage.forEach(id => updated.delete(id)); }
    else { allOnPage.forEach(id => updated.add(id)); }
    selectedIds = updated;
  }
  function invertSelection() {
    const current = new Set(selectedIds);
    selectedIds = new Set(articles.filter(a => !current.has(a.id)).map(a => a.id));
  }

  async function bulkUpdate(fields: { status?: string; category?: string }) {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    isSaving = true;
    try {
      await apiClient.patch("/api/v1/articles/bulk-update", { ids, ...fields });
      selectedIds = new Set();
      nanobot.showToast(`Cập nhật thành công ${ids.length} bài viết.`, "success");
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError ? (err.data as Record<string, unknown>)?.detail : "Cập nhật hàng loạt thất bại";
      nanobot.showToast(`Neural sync failed. ${detail}`, "error");
    } finally { isSaving = false; }
  }

  async function bulkDelete() {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    isSaving = true;
    try {
      await apiClient.post("/api/v1/articles/bulk-delete", { ids });
      selectedIds = new Set();
      nanobot.showToast("Đã tiêu hủy dữ liệu thành công.", "success");
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError ? (err.data as Record<string, unknown>)?.detail : "Tiêu hủy thất bại";
      nanobot.showToast(`Neural link failed. ${detail}`, "error");
    } finally { isSaving = false; }
  }

  function confirmDelete(id: string) { purgeTargetId = id; isBulkPurge = false; showPurgeConfirm = true; }
  function confirmBulkDelete() { isBulkPurge = true; showPurgeConfirm = true; }

  async function executePurge() {
    isSaving = true;
    try {
      if (isBulkPurge) {
        await bulkDelete();
      } else if (purgeTargetId) {
        await apiClient.post("/api/v1/articles/bulk-delete", { ids: [purgeTargetId] });
        nanobot.showToast("Purge complete.", "success");
        await loadArticles();
      }
    } catch {
      nanobot.showToast("Purge sequence failed.", "error");
    } finally {
      isSaving = false;
      showPurgeConfirm = false;
      purgeTargetId = null;
    }
  }
</script>

<!-- NewsForm Modal Layer -->
<NewsForm
  {editingId}
  bind:isOpen={showDraftForm}
  bind:formTitle
  bind:formCategory
  bind:formStatus
  bind:formExcerpt
  bind:formContent
  bind:formSlug
  bind:formSeoTitle
  bind:formSeoDescription
  bind:formSeoKeywords
  bind:formSeoOgImage
  bind:formFeaturedImage
  bind:formFaqs
  bind:formAnalysisCache
  bind:formAnalysisMetrics
  bind:formAnalysisReport
  onSave={saveArticle}
  onClose={() => { showDraftForm = false; nanobot.toggleExpand(false); }}
  {generateSlug}
  dbCategories={categories}
  {isSaving}
  {errors}
/>

<div class="w-full h-full flex flex-col relative bg-[#050505] isolation-auto">
  <!-- Fixed Background Layer -->
  <div class="absolute inset-0 bg-[#050505] pointer-events-none -z-10"></div>
  
  <div class="flex flex-col gap-6 p-6 border-b border-white/[0.05] relative z-10 bg-[#050505]">
    {#if !isHeaderCollapsed}
      <div transition:fade={{ duration: 200 }} class="flex flex-col gap-4">
        <div class="flex items-center gap-3">
          <Newspaper size={20} class="text-cyan-500" />
          <h2 class="text-lg font-black uppercase tracking-[0.3em] text-white/90">QUẢN_LÝ_TIN_TỨC</h2>
          <span class="px-3 py-1 bg-cyan-400/10 border border-cyan-400/20 rounded-full text-[10px] font-black text-cyan-400 uppercase tracking-widest">{totalArticles} bài</span>
        </div>
      </div>
    {/if}

    <NewsToolbar
      {searchInput}
      {activeTab}
      {activeCategoryFilter}
      {categories}
      bind:pageSize
      {selectedIds}
      {totalArticles}
      {isLoading}
      bind:isHeaderCollapsed
      onSearchInput={handleSearchInput}
      onTabChange={handleTabChange}
      onCategoryChange={handleCategoryChange}
      onPageSizeChange={() => { currentPage = 1; loadArticles(); }}
      onOpenCreate={openCreate}
      onLoadArticles={loadArticles}
    />
  </div>

  <div class="flex-1 overflow-y-auto custom-scrollbar relative bg-[#050505]/50">
    {#if isLoading}
      <div class="h-full flex items-center justify-center animate-pulse">
        <span class="text-[9px] font-mono text-cyan-500/40 uppercase tracking-[0.3em]">Đang đồng bộ dữ liệu Neural...</span>
      </div>
    {:else}
      <div class="pl-6 border-l border-white/5 ml-4 my-2 mb-[80px]">
        <NewsTable
          {articles}
          {selectedIds}
          onToggleSelect={toggleSelect}
          onToggleSelectAll={toggleSelectAll}
          onEdit={openEdit}
          onDelete={confirmDelete}
        />
      </div>
    {/if}
  </div>

  <div class="absolute bottom-0 left-0 right-0 z-20">
    <OrderPagination
      bind:currentPage
      {totalPages}
      {pageSize}
      totalItems={totalArticles}
      onPageChange={() => loadArticles()}
    />
  </div>


  <!-- NEURAL COMMAND BAR (Floating Bulk Actions) -->
  {#if selectedIds.size > 0}
      <div
        class="absolute bottom-10 left-1/2 -translate-x-1/2 z-50 flex items-center gap-6 p-2 pl-6 bg-[#0a0a0a]/80 backdrop-blur-2xl border border-white/10 rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.5),0_0_20px_rgba(6,182,212,0.1)]"
        transition:fly={{ y: 50, duration: 400 }}
      >
        <div class="flex items-center gap-3 border-r border-white/10 pr-6">
          <div class="w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 text-xs font-bold">{selectedIds.size}</div>
          <span class="text-[10px] font-black uppercase tracking-widest text-white/60">Đã chọn</span>
        </div>

        <div class="flex items-center gap-2">
          <button onclick={selectAll} class="cmd-btn">Tất cả</button>
          <button onclick={invertSelection} class="cmd-btn">Đảo ngược</button>
          <button onclick={deselectAll} class="cmd-btn">Bỏ chọn</button>
        </div>

        <div class="w-px h-6 bg-white/5 ml-2"></div>

        <div class="flex items-center gap-2 pr-2">
          <div class="relative group/drop">
            <button class="action-btn text-cyan-400 hover:bg-cyan-500/10">Trạng thái</button>
            <!-- Hover Bridge & Popup -->
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 hidden group-hover/drop:flex flex-col pb-2 min-w-[160px]">
              <div class="flex flex-col bg-[#111]/95 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
                <button onclick={() => bulkUpdate({ status: 'PUBLISHED' })} class="drop-item hover:text-[#39FF14] hover:bg-white/5 transition-colors">Đăng bài (Live)</button>
                <button onclick={() => bulkUpdate({ status: 'DRAFT' })} class="drop-item hover:text-cyan-400 hover:bg-white/5 transition-colors">Chuyển về Nháp</button>
              </div>
            </div>
          </div>

          <div class="relative group/drop-cat">
            <button class="action-btn text-amber-400 hover:bg-amber-500/10">Chuyên mục</button>
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 hidden group-hover/drop-cat:flex flex-col pb-2 min-w-[160px]">
              <div class="flex flex-col bg-[#111]/95 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)] max-h-[200px] overflow-y-auto custom-scrollbar">
                {#each categories as cat}
                  <button onclick={() => bulkUpdate({ category: cat })} class="drop-item hover:text-amber-400 hover:bg-white/5 transition-colors">{cat}</button>
                {/each}
              </div>
            </div>
          </div>

          <button onclick={confirmBulkDelete} class="action-btn text-red-500 hover:bg-red-500/10">Xóa vĩnh viễn</button>
        </div>
      </div>
    {/if}

  <!-- PURGE CONFIRMATION MODAL -->
  {#if showPurgeConfirm}
    <div class="fixed inset-0 z-[var(--z-modal-overlay)] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" transition:fade>
      <div class="w-full max-w-md bg-[#0a0a0a] border border-red-500/20 rounded-3xl p-8 shadow-[0_0_50px_rgba(239,68,68,0.1)]" transition:fly={{ y: 20, duration: 400 }}>
        <div class="flex flex-col items-center text-center gap-6">
          <div class="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 animate-pulse">
            <Trash2 size={32} />
          </div>
          <div class="flex flex-col gap-2">
            <h3 class="text-xl font-black uppercase tracking-widest text-white">Xác nhận xóa</h3>
            <p class="text-sm text-gray-500 font-mono italic">Dữ liệu sẽ bị xóa vĩnh viễn. Sếp có chắc chắn không?</p>
          </div>
          <div class="flex items-center gap-4 w-full">
            <button
              onclick={() => (showPurgeConfirm = false)}
              class="flex-1 px-6 py-3 rounded-xl border border-white/5 text-[10px] uppercase font-black tracking-widest text-gray-400 hover:bg-white/5 transition-all"
            >Hủy lệnh</button>
            <button
              onclick={executePurge}
              class="flex-1 px-6 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-[10px] uppercase font-black tracking-widest text-red-500 hover:bg-red-500/20 transition-all"
            >Kích hoạt xóa</button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  @reference "tailwindcss";

  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(6, 182, 212, 0.2); }

  .cmd-btn {
    @apply px-3 py-1.5 text-[9px] font-black uppercase tracking-tighter text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-all;
  }
  .action-btn {
    @apply px-4 py-1.5 text-[9px] font-black uppercase tracking-widest border border-white/5 rounded-full transition-all;
  }
  .drop-item {
    @apply px-4 py-2.5 text-[9px] font-black uppercase tracking-widest text-white/40 border-b border-white/5 last:border-0 text-left transition-all;
  }
</style>
