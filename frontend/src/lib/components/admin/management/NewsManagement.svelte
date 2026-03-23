<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import Plus from "lucide-svelte/icons/plus";
  import Search from "lucide-svelte/icons/search";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Newspaper from "lucide-svelte/icons/newspaper";
  import ChevronLeft from "lucide-svelte/icons/chevron-left";
  import type { Article, BaseWidgetProps } from "$lib/types";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient, ApiError } from "$lib/utils/apiClient";

  import NewsList from "./NewsList.svelte";
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
  let activeCategoryFilter = $state("all");
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
  let showDraftForm = $state(false);

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
      categories = ["Tin tức", "Chính sách"];
      if (!formCategory) formCategory = categories[0];
    }
  }

  $effect(() => { 
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
    searchTimer = setTimeout(() => { searchTerm = val; currentPage = 1; }, 400);
  }

  function handleTabChange(tab: string) {
    if (activeTab !== tab) { activeTab = tab; currentPage = 1; }
  }

  function handleCategoryChange(cat: string) {
    if (activeCategoryFilter !== cat) { activeCategoryFilter = cat; currentPage = 1; }
  }

  function generateSlug(title: string) {
    return title.toLowerCase()
      .trim()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[đĐ]/g, 'd')
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/[\s-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function openCreate() {
    editingId = null;
    formTitle = ""; formCategory = categories[0] || ""; formExcerpt = "";
    formContent = ""; formSlug = ""; formSeoTitle = "";
    formSeoDescription = ""; formSeoKeywords = ""; formSeoOgImage = null; formFeaturedImage = null;
    showDraftForm = true;
  }

  async function openEdit(a: Article) {
    try {
      nanobot.showToast("Loading intelligence...", "info");
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
        featured_image: formFeaturedImage
      };

      if (editingId) {
        await apiClient.patch(`/api/v1/articles/${editingId}`, payload);
        nanobot.showToast("Neural sync complete. Đã cập nhật bài viết thành công!", "success");
      } else {
        await apiClient.post("/api/v1/articles", payload);
        nanobot.showToast("Intelligence deployed. Bài viết đã được đăng tải!", "success");
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
      nanobot.showToast(`Neural override complete. Đã cập nhật ${ids.length} bài viết.`, "success");
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError ? (err.data as any)?.detail : "Cập nhật hàng loạt thất bại";
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
      nanobot.showToast("Neural purge complete.", "success");
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError ? (err.data as any)?.detail : "Tiêu hủy thất bại";
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

<div class="w-full h-full flex flex-col overflow-hidden relative bg-[#050505]">

  {#if showDraftForm}
    <!-- ======================== FULL-SCREEN EDIT MODE ======================== -->
    <div class="w-full h-full flex flex-col overflow-y-auto custom-scrollbar" transition:fade={{ duration: 250 }}>
      <!-- Back navigation bar -->
      <div class="flex items-center gap-4 px-6 py-4 border-b border-white/5 shrink-0">
        <button
          onclick={() => { showDraftForm = false; }}
          class="flex items-center gap-2.5 px-5 py-2.5 bg-white/[0.03] border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] text-white/40 hover:text-white hover:bg-white/[0.06] hover:border-white/20 active:scale-95 transition-all duration-300"
        >
          <ChevronLeft size={14} />
          <span>Intelligence_Archive</span>
        </button>

        <div class="w-px h-5 bg-white/10"></div>

        <div class="flex items-center gap-2">
          <Newspaper size={12} class="text-cyan-400/50" />
          <span class="text-[9px] font-black uppercase tracking-[0.3em] text-white/20">
            {editingId ? `EDIT // ID_${editingId.slice(0, 8)}` : "NEW_ENTRY"}
          </span>
        </div>
      </div>

      <!-- NewsForm fills remaining space -->
      <div class="flex-1 px-6 py-4">
        <NewsForm
          {editingId}
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
          onSave={saveArticle}
          onClose={() => (showDraftForm = false)}
          {generateSlug}
          dbCategories={categories}
          {isSaving}
          {errors}
        />
      </div>
    </div>

  {:else}
    <!-- ======================== LIST VIEW MODE ======================== -->
    <div class="w-full h-full flex flex-col overflow-hidden" transition:fade={{ duration: 250 }}>
      <!-- Toolbar -->
      <div class="flex flex-col gap-4 px-4 sm:px-6 py-5 border-b border-white/5 shrink-0">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2.5">
            <Newspaper size={16} class="text-cyan-500" />
            <h2 class="text-sm font-black uppercase tracking-[0.2em] text-white/80">Intelligence_Archive</h2>
            <span class="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-[9px] font-black text-cyan-400 uppercase tracking-widest">{totalArticles}</span>
          </div>

          <div class="flex items-center gap-2">
            <div class="hidden sm:flex items-center gap-1.5 text-[9px] font-mono text-gray-500 uppercase tracking-widest">
              <span>Show</span>
              <select
                value={pageSize}
                onchange={(e) => { pageSize = Number(e.currentTarget.value); currentPage = 1; }}
                class="bg-black/60 border border-white/10 rounded-md px-1.5 py-1 text-cyan-500 text-[9px] font-mono font-bold focus:outline-none focus:border-cyan-500/50 cursor-pointer appearance-none text-center w-12"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
              <span>of {totalArticles}</span>
            </div>

            <button onclick={loadArticles} title="Force Resync"
              class="p-2.5 text-gray-500 hover:text-cyan-400 border border-white/5 hover:border-cyan-500/30 rounded-xl bg-black/40 hover:bg-cyan-500/10 transition-all"
            >
              <RefreshCw size={14} class={isLoading ? "animate-spin text-cyan-400" : ""} />
            </button>

            <button onclick={openCreate}
              class="flex items-center gap-2 px-5 py-2.5 text-[10px] font-black uppercase tracking-[0.2em] bg-cyan-500 text-black rounded-2xl hover:bg-cyan-400 active:scale-95 transition-all duration-300 shadow-[0_8px_30px_rgba(6,182,212,0.3)]"
            >
              <Plus size={14} />
              <span class="hidden sm:inline">New_Intel</span>
            </button>
          </div>
        </div>

        <!-- Filters -->
        <div class="flex flex-col xl:flex-row xl:items-center gap-3 bg-white/[0.01] border border-white/5 p-3 rounded-2xl w-full">
          <div class="flex-1 relative group">
            <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <Search size={14} class="text-gray-600 group-focus-within:text-cyan-400 transition-colors" />
            </div>
            <input
              value={searchInput}
              oninput={handleSearchInput}
              type="text"
              placeholder="SEARCH_CONTENT_STREAM..."
              class="w-full bg-black/40 border border-white/5 rounded-xl py-3 pl-11 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-cyan-500/40 focus:ring-1 focus:ring-cyan-500/10 transition-all uppercase tracking-widest"
            />
          </div>

          <div class="flex flex-col sm:flex-row xl:items-center gap-3 sm:gap-4 xl:gap-0">
            <div class="flex gap-1 p-1 bg-black/40 border border-white/5 rounded-xl overflow-x-auto custom-scrollbar">
              <span class="px-3 text-[7px] font-mono text-white/20 uppercase tracking-[0.3em] flex-shrink-0 self-center">Category_</span>
              {#each ["all", ...categories] as c}
                <button
                  onclick={() => handleCategoryChange(c)}
                  class="px-4 py-2 text-[8px] font-mono uppercase tracking-[0.2em] rounded-lg transition-all flex-shrink-0 {activeCategoryFilter === c ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30' : 'text-gray-500 hover:text-white hover:bg-white/5'}"
                >{c === "all" ? "Tất cả" : c}</button>
              {/each}
            </div>

            <div class="hidden xl:block w-[1px] h-6 bg-white/10 mx-2"></div>

            <div class="flex gap-1 p-1 bg-black/40 border border-white/5 rounded-xl overflow-x-auto custom-scrollbar">
              {#each ["all", "published", "draft"] as t}
                <button
                  onclick={() => handleTabChange(t)}
                  class="px-4 py-2 text-[8px] font-mono uppercase tracking-[0.2em] rounded-lg transition-all flex-shrink-0 {activeTab === t ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30' : 'text-gray-500 hover:text-white hover:bg-white/5'}"
                >{t === "all" ? "KHO_TỔNG" : t === "published" ? "BÀI_LIVE" : "BẢN_NHÁP"}</button>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <!-- Article List -->
      <div class="flex-1 overflow-y-auto custom-scrollbar px-4 sm:px-6">
        {#if isLoading}
          <div class="h-full flex items-center justify-center animate-pulse">
            <span class="text-[9px] font-mono text-cyan-500/40 uppercase tracking-[0.3em]">Loading Content...</span>
          </div>
        {:else}
          <NewsList
            {articles}
            {selectedIds}
            onToggleSelect={toggleSelect}
            onEdit={openEdit}
            onDelete={confirmDelete}
          />
        {/if}
      </div>

      <div class="px-4 sm:px-6 shrink-0">
        <OrderPagination bind:currentPage {totalPages} {pageSize} totalItems={totalArticles} />
      </div>
    </div>

    <!-- NEURAL COMMAND BAR (Floating Bulk Actions) -->
    {#if selectedIds.size > 0}
      <div
        class="absolute bottom-10 left-1/2 -translate-x-1/2 z-50 flex items-center gap-6 p-2 pl-6 bg-[#0a0a0a]/80 backdrop-blur-2xl border border-white/10 rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.5),0_0_20px_rgba(6,182,212,0.1)]"
        transition:fly={{ y: 50, duration: 400 }}
      >
        <div class="flex items-center gap-3 border-r border-white/10 pr-6">
          <div class="w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 text-xs font-bold">{selectedIds.size}</div>
          <span class="text-[10px] font-black uppercase tracking-widest text-white/60">Selected</span>
        </div>

        <div class="flex items-center gap-2">
          <button onclick={selectAll} class="cmd-btn">All</button>
          <button onclick={invertSelection} class="cmd-btn">Invert</button>
          <button onclick={deselectAll} class="cmd-btn">Clear</button>
        </div>

        <div class="w-px h-6 bg-white/5 ml-2"></div>

        <div class="flex items-center gap-2 pr-2">
          <div class="relative group/drop">
            <button class="action-btn text-cyan-400 hover:bg-cyan-500/10">Status</button>
            <div class="absolute bottom-full mb-2 left-0 hidden group-hover/drop:flex flex-col bg-[#111] border border-white/10 rounded-xl overflow-hidden min-w-[120px]">
              <button onclick={() => bulkUpdate({ status: 'PUBLISHED' })} class="drop-item hover:text-[#39FF14]">Deploy_Live</button>
              <button onclick={() => bulkUpdate({ status: 'DRAFT' })} class="drop-item hover:text-cyan-400">Move_Staging</button>
            </div>
          </div>
          <button onclick={confirmBulkDelete} class="action-btn text-red-400 hover:bg-red-500/10">Purge</button>
        </div>
      </div>
    {/if}
  {/if}

  <!-- PURGE CONFIRMATION MODAL -->
  {#if showPurgeConfirm}
    <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" transition:fade>
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
