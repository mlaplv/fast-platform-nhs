<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import { 
    Newspaper, 
    Plus, 
    Search, 
    Trash2, 
    Send, 
    RefreshCw 
  } from "lucide-svelte";
  import type { Article, BaseWidgetProps } from "$lib/types";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient, ApiError } from "$lib/utils/apiClient";

  import NewsList from "./NewsList.svelte";
  import OrderPagination from "./OrderPagination.svelte";
  import NewsForm from "./NewsForm.svelte";

  let { data = {} } = $props<BaseWidgetProps>();

  const CATEGORIES = ["Tin tức", "Chính sách"] as const;

  // --- STATE (Server-Side Pagination) ---
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
  let formCategory = $state<string>(CATEGORIES[0]);
  let formStatus = $state("DRAFT");
  let formExcerpt = $state("");
  let formContent = $state("");
  let formSlug = $state("");
  let formSeoTitle = $state("");
  let formSeoDescription = $state("");
  let formFeaturedImage = $state<string | null>(null);
  let showDraftForm = $state(false);

  let pageSize = $state(10);
  let showPurgeConfirm = $state(false);
  let purgeTargetId = $state<string | null>(null);
  let isBulkPurge = $state(false);
  let isSaving = $state(false);
  let errors = $state<Record<string, string>>({});
  const totalPages = $derived(Math.max(1, Math.ceil(totalArticles / pageSize)));
  const allSelected = $derived(articles.length > 0 && selectedIds.size === articles.length);

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

  $effect(() => { loadArticles(); });

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
      formCategory = (data?.category as string) || CATEGORIES[0];
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
    formTitle = ""; 
    formCategory = CATEGORIES[0]; 
    formExcerpt = "";
    formContent = "";
    formSlug = "";
    formSeoTitle = "";
    formSeoDescription = "";
    formFeaturedImage = null;
    showDraftForm = true;
  }

  async function openEdit(a: Article) {
    try {
      nanobot.showToast("Loading intelligence...", "info");
      const fullArticle = await apiClient.get<Article>(`/api/v1/articles/${a.id}`);
      
      editingId = fullArticle.id; 
      formTitle = fullArticle.title; 
      formCategory = fullArticle.category; 
      formExcerpt = fullArticle.excerpt || "";
      formContent = fullArticle.content || "";
      formSlug = fullArticle.slug;
      formSeoTitle = fullArticle.seoTitle || "";
      formSeoDescription = fullArticle.seoDescription || "";
      formFeaturedImage = fullArticle.featuredImage || null;
      showDraftForm = true;
    } catch (err) {
      nanobot.showToast("Dạ sếp, không lấy được chi tiết bài viết. Neural Link bị lỗi rồi!", "error");
    }
  }

  async function saveArticle() {
    errors = {};
    if (!formTitle.trim()) {
      errors.title = "Tiêu đề không thể để trống sếp ơi";
    }
    if (!formSlug.trim() && editingId) {
      errors.slug = "Đường dẫn không hợp lệ";
    }

    if (Object.keys(errors).length > 0) {
      nanobot.showToast("Dạ sếp, thông tin chưa đầy đủ, sếp kiểm tra lại giúp em nhé!", "error");
      return;
    }

    isSaving = true;
    try {
      const payload = {
        title: formTitle,
        category: formCategory,
        excerpt: formExcerpt,
        content: formContent,
        slug: formSlug || generateSlug(formTitle),
        status: formStatus, // Use formStatus instead of activeTab logic
        seo_title: formSeoTitle,
        seo_description: formSeoDescription,
        featured_image: formFeaturedImage
      };

      if (editingId) {
        await apiClient.patch(`/api/v1/articles/${editingId}`, payload);
        nanobot.showToast("Neural sync complete. Hệ thống đã cập nhật bài viết thành công!", "success");
      } else {
        await apiClient.post("/api/v1/articles", payload);
        nanobot.showToast("Intelligence deployed. Bài viết đã được đăng tải hoàn tất!", "success");
      }
      showDraftForm = false;
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError ? (err.data as any)?.detail : "Lỗi giao thức Neural Link";
      nanobot.showToast(`Neural link failed. ${detail}. Sếp thử lại nhé!`, "error");
    } finally {
      isSaving = false;
    }
  }
  function toggleSelect(id: string) {
    if (id === "__all_on") {
      selectAll();
      return;
    }
    if (id === "__all_off") {
      deselectAll();
      return;
    }
    const n = new Set(selectedIds);
    n.has(id) ? n.delete(id) : n.add(id);
    selectedIds = n;
  }

  function selectAll() {
    selectedIds = new Set(articles.map(a => a.id));
  }

  function deselectAll() {
    selectedIds = new Set();
  }

  function invertSelection() {
    const current = new Set(selectedIds);
    const inverted = new Set(articles.filter(a => !current.has(a.id)).map(a => a.id));
    selectedIds = inverted;
  }

  async function bulkUpdate(fields: { status?: string, category?: string }) {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    
    isSaving = true;
    nanobot.showToast(`Đang ghi đè dữ liệu cho ${ids.length} bài viết...`, "info");
    
    try {
      await apiClient.patch("/api/v1/articles/bulk-update", { ids, ...fields });
      selectedIds = new Set();
      nanobot.showToast(`Neural override complete. Đã cập nhật ${ids.length} bài viết thành công.`, "success");
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError ? (err.data as any)?.detail : "Cập nhật hàng loạt thất bại";
      nanobot.showToast(`Neural sync failed. ${detail}`, "error");
    } finally {
      isSaving = false;
    }
  }

  async function bulkDelete() {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    
    isSaving = true;
    nanobot.showToast(`Đang tiêu hủy ${ids.length} bài viết...`, "info");
    
    try {
      await apiClient.post("/api/v1/articles/bulk-delete", { ids });
      selectedIds = new Set();
      nanobot.showToast("Neural purge complete. Dữ liệu đã được dọn dẹp!", "success");
      await loadArticles();
    } catch (err: unknown) {
      const detail = err instanceof ApiError ? (err.data as any)?.detail : "Tiêu hủy thất bại";
      nanobot.showToast(`Neural link failed. ${detail}`, "error");
    } finally {
      isSaving = false;
    }
  }

  function confirmDelete(id: string) {
    purgeTargetId = id;
    isBulkPurge = false;
    showPurgeConfirm = true;
  }

  function confirmBulkDelete() {
    isBulkPurge = true;
    showPurgeConfirm = true;
  }

  async function executePurge() {
    isSaving = true;
    try {
      if (isBulkPurge) {
        await bulkDelete();
      } else if (purgeTargetId) {
        await apiClient.post("/api/v1/articles/bulk-delete", { ids: [purgeTargetId] });
        nanobot.showToast("Purge complete. Neural sync verified.", "success");
        await loadArticles();
      }
    } catch (err: unknown) {
      nanobot.showToast("Purge sequence failed. Neural link interrupted.", "error");
    } finally {
      isSaving = false;
      showPurgeConfirm = false;
      purgeTargetId = null;
    }
  }
</script>

<!-- Simple inline flex: List | Form side-by-side INSIDE the modal content area -->
<div class="news-split w-full h-full flex overflow-hidden relative">
  <!-- LEFT: Article List (shrinks when form is open) -->
  <div class="news-list-pane flex flex-col overflow-hidden" class:has-form={showDraftForm}>
    <div class="flex flex-col gap-4 px-2 sm:px-4 py-4 sm:py-0">
      <div class="flex items-center justify-between gap-2 overflow-hidden">
        <div class="flex items-center gap-2 shrink-0">
          <Newspaper size={14} class="text-cyan-500" />
          <h2 class="text-[10px] font-black uppercase tracking-[0.2em] text-white/90 hidden sm:block">Intelligence_Archive</h2>
          <h2 class="text-[9px] font-black uppercase tracking-[0.1em] text-white/70 block sm:hidden">INTEL</h2>
        </div>

        <div class="flex items-center gap-2 shrink-0">
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

          <div class="flex items-center gap-1.5">
            <button onclick={openCreate}
              class="px-2.5 sm:px-4 py-2 text-[10px] font-mono uppercase bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-xl hover:bg-cyan-500/20 transition-all shadow-[0_0_15px_rgba(6,182,212,0.1)] flex items-center gap-1.5"
              ><Plus size={12} /> <span class="hidden xs:inline">New_Intel</span><span class="xs:hidden">New</span></button>

            <button onclick={loadArticles} title="Force Resync"
              class="p-2 sm:p-2.5 text-gray-500 hover:text-cyan-400 border border-white/5 hover:border-cyan-500/30 rounded-xl bg-black/40 hover:bg-cyan-500/10 transition-all"
            >
              <RefreshCw size={14} class={isLoading ? "animate-spin text-cyan-400" : ""} />
            </button>
          </div>
        </div>
      </div>
      <div class="flex flex-col xl:flex-row xl:items-center gap-3 sm:gap-4 bg-white/[0.01] border border-white/5 p-3 sm:p-2 rounded-2xl w-full">
        <div class="flex-1 relative group w-full xl:min-w-[250px]">
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

        <div class="flex flex-col sm:flex-row xl:items-center gap-3 sm:gap-4 xl:gap-0 mt-2 xl:mt-0 w-full xl:w-auto">
          <div class="flex items-center gap-1 p-1 bg-black/40 border border-white/5 rounded-xl overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
            <span class="px-3 text-[7px] font-mono text-white/20 uppercase tracking-[0.3em] flex-shrink-0">Category_</span>
            {#each ["all", ...CATEGORIES] as c}
              <button
                onclick={() => handleCategoryChange(c)}
                class="px-4 py-2 text-[8px] font-mono uppercase tracking-[0.2em] rounded-lg transition-all relative overflow-hidden group/btn flex-shrink-0
                  {activeCategoryFilter === c
                  ? 'bg-neon-cyan/10 text-neon-cyan/90 ring-1 ring-neon-cyan/30'
                  : 'text-gray-500 hover:text-white hover:bg-white/5'}"
              >
                {c === "all" ? "Tất cả" : c}
              </button>
            {/each}
          </div>

          <div class="hidden xl:block w-[1px] h-6 bg-white/10 mx-2"></div>

          <div class="flex gap-1 p-1 bg-black/40 border border-white/5 rounded-xl overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
            {#each ["all", "published", "draft"] as t}
              <button
                onclick={() => handleTabChange(t)}
                class="px-4 py-2 text-[8px] font-mono uppercase tracking-[0.2em] rounded-lg transition-all relative overflow-hidden group/btn flex-shrink-0
                  {activeTab === t
                  ? 'bg-cyan-500/10 text-cyan-500/90 ring-1 ring-cyan-500/30'
                  : 'text-gray-500 hover:text-white hover:bg-white/5'}"
              >
                {t === "all" ? "Archive" : t === "published" ? "Live" : "Staging"}
              </button>
            {/each}
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar px-2 sm:px-4">
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

    <div class="px-2 sm:px-4">
      <OrderPagination
        bind:currentPage
        {totalPages}
        {pageSize}
        totalItems={totalArticles}
      />
    </div>
  </div>

  <!-- RIGHT: News Form (slides in from right) -->
  {#if showDraftForm}
    <div class="news-form-pane border-l border-white/10 overflow-y-auto">
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
        bind:formFeaturedImage
        onSave={saveArticle}
        onClose={() => (showDraftForm = false)}
        {generateSlug}
        dbCategories={CATEGORIES}
        {isSaving}
        {errors}
      />
    </div>
  {/if}

  <!-- NEURAL COMMAND BAR (Floating Bulk Actions) -->
  {#if selectedIds.size > 0}
    <div 
      class="absolute bottom-10 left-1/2 -translate-x-1/2 z-50 flex items-center gap-6 p-2 pl-6 bg-[#0a0a0a]/80 backdrop-blur-2xl border border-white/10 rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.5),0_0_20px_rgba(6,182,212,0.1)]"
      transition:fly={{ y: 50, duration: 400 }}
    >
      <div class="flex items-center gap-3 border-r border-white/10 pr-6">
        <div class="w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 text-xs font-bold">
          {selectedIds.size}
        </div>
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

        <div class="relative group/drop">
          <button class="action-btn text-purple-400 hover:bg-purple-500/10">Category</button>
          <div class="absolute bottom-full mb-2 left-0 hidden group-hover/drop:flex flex-col bg-[#111] border border-white/10 rounded-xl overflow-hidden min-w-[120px]">
            {#each CATEGORIES as cat}
              <button onclick={() => bulkUpdate({ category: cat })} class="drop-item">{cat}</button>
            {/each}
          </div>
        </div>

        <button onclick={confirmBulkDelete} class="action-btn text-red-400 hover:bg-red-500/10">Purge</button>
      </div>
    </div>
  {/if}

  <!-- PURGE CONFIRMATION MODAL -->
  {#if showPurgeConfirm}
    <div 
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      transition:fade
    >
      <div 
        class="w-full max-w-md bg-[#0a0a0a] border border-red-500/20 rounded-3xl p-8 shadow-[0_0_50px_rgba(239,68,68,0.1)]"
        transition:fly={{ y: 20, duration: 400 }}
      >
        <div class="flex flex-col items-center text-center gap-6">
          <div class="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 animate-pulse">
            <Trash2 size={32} />
          </div>
          
          <div class="flex flex-col gap-2">
            <h3 class="text-xl font-black uppercase tracking-widest text-white">Xác nhận xóa</h3>
            <p class="text-sm text-gray-500 font-mono italic">
              Dữ liệu sẽ bị xóa vĩnh viễn khỏi Intelligence_Archive. Sếp có chắc chắn không?
            </p>
          </div>

          <div class="flex items-center gap-4 w-full">
            <button 
              onclick={() => (showPurgeConfirm = false)}
              class="flex-1 px-6 py-3 rounded-xl border border-white/5 text-[10px] uppercase font-black tracking-widest text-gray-400 hover:bg-white/5 transition-all"
            >
              Hủy lệnh
            </button>
            <button 
              onclick={executePurge}
              class="flex-1 px-6 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-[10px] uppercase font-black tracking-widest text-red-500 hover:bg-red-500/20 transition-all shadow-[0_0_20px_rgba(239,68,68,0.1)]"
            >
              Kích hoạt xóa
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  @reference "tailwindcss";

  .news-list-pane {
    width: 100%;
    transition: width 0.3s ease;
  }
  .news-list-pane.has-form {
    width: 40%;
  }
  .news-form-pane {
    width: 60%;
    background: rgba(10, 15, 24, 0.98);
  }
  @media (max-width: 768px) {
    .news-list-pane.has-form {
      display: none;
    }
    .news-form-pane {
      width: 100%;
    }
  }
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
  }

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
