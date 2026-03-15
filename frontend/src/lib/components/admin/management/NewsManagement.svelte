<script lang="ts">
  import { fade } from "svelte/transition";
  import Newspaper from "lucide-svelte/icons/newspaper";
  import Plus from "lucide-svelte/icons/plus";
  import Search from "lucide-svelte/icons/search";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Send from "lucide-svelte/icons/send";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import type { Article, BaseWidgetProps } from "$lib/types";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";

  import NewsList from "./NewsList.svelte";
  import OrderPagination from "./OrderPagination.svelte";
  import DraftGenerativeForm from "./DraftGenerativeForm.svelte";

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
  let formExcerpt = $state("");
  let showDraftForm = $state(false);

  let pageSize = $state(10);
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
        (data?.entities as Record<string, unknown>)?.name as string ||
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

  function openCreate() {
    editingId = null; formTitle = ""; formCategory = CATEGORIES[0]; formExcerpt = "";
    showDraftForm = true;
  }
  function openEdit(a: Article) {
    editingId = a.id; formTitle = a.title; formCategory = a.category; formExcerpt = a.excerpt || "";
    showDraftForm = true;
  }
  function toggleSelect(id: string) {
    const n = new Set(selectedIds);
    n.has(id) ? n.delete(id) : n.add(id);
    selectedIds = n;
  }

  async function bulk(v: "del" | "pub") {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    try {
      if (v === "del") await apiClient.post("/api/v1/articles/bulk-delete", { ids });
      else await apiClient.post("/api/v1/articles/bulk-publish", { ids });
      selectedIds = new Set();
      await loadArticles();
    } catch { nanobot.showToast("Thao tác hàng loạt thất bại", "error"); }
  }
</script>

<!-- Simple inline flex: List | Form side-by-side INSIDE the modal content area -->
<div class="news-split w-full h-full flex overflow-hidden">
  <!-- LEFT: Article List (shrinks when form is open) -->
  <div class="news-list-pane flex flex-col overflow-hidden" class:has-form={showDraftForm}>
    <div class="flex flex-col gap-4 px-2 sm:px-4 py-4 sm:py-0">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4"></div>
        <div class="flex items-center gap-3">
          {#if selectedIds.size > 0}
            <button onclick={() => bulk("pub")}
              class="px-4 py-2 text-[10px] font-mono uppercase bg-[#39FF14]/10 border border-[#39FF14]/30 text-[#39FF14] rounded-xl hover:bg-[#39FF14]/20 transition-all shadow-[0_0_15px_rgba(57,255,20,0.1)]"
              ><Send size={12} class="inline mr-1" /> Deploy_Live ({selectedIds.size})</button>
            <button onclick={() => bulk("del")}
              class="px-4 py-2 text-[10px] font-mono uppercase bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl hover:bg-red-500/20 transition-all shadow-[0_0_15px_rgba(239,68,68,0.1)]"
              ><Trash2 size={12} class="inline mr-1" /> Purge ({selectedIds.size})</button>
          {/if}

          <div class="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 uppercase tracking-widest">
            <span>Show</span>
            <select
              value={pageSize}
              onchange={(e) => { pageSize = Number((e.target as HTMLSelectElement).value); currentPage = 1; }}
              class="bg-black/60 border border-white/10 rounded-md px-1.5 py-1 text-[#FF33FF] text-[9px] font-mono font-bold focus:outline-none focus:border-[#FF33FF]/50 cursor-pointer appearance-none text-center w-12"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span>of {totalArticles}</span>
          </div>

          <button onclick={openCreate}
            class="px-4 py-2 text-[10px] font-mono uppercase bg-[#FF33FF]/10 border border-[#FF33FF]/30 text-[#FF33FF] rounded-xl hover:bg-[#FF33FF]/20 transition-all shadow-[0_0_15px_rgba(255,51,255,0.1)]"
            ><Plus size={12} class="inline mr-1" /> New_Intel</button>

          <button onclick={loadArticles} title="Force Resync"
            class="p-2.5 text-gray-500 hover:text-[#FF33FF] border border-white/5 hover:border-[#FF33FF]/30 rounded-xl bg-black/40 hover:bg-[#FF33FF]/10 transition-all"
          >
            <RefreshCw size={14} class={isLoading ? "animate-spin text-[#FF33FF]" : ""} />
          </button>
        </div>
      </div>
      <div class="flex flex-col xl:flex-row xl:items-center gap-3 sm:gap-4 bg-white/[0.01] border border-white/5 p-3 sm:p-2 rounded-2xl w-full">
        <div class="flex-1 relative group w-full xl:min-w-[250px]">
          <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <Search size={14} class="text-gray-600 group-focus-within:text-[#FF33FF] transition-colors" />
          </div>
          <input
            value={searchInput}
            oninput={handleSearchInput}
            type="text"
            placeholder="SEARCH_CONTENT_STREAM..."
            class="w-full bg-black/40 border border-white/5 rounded-xl py-3 pl-11 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#FF33FF]/40 focus:ring-1 focus:ring-[#FF33FF]/10 transition-all uppercase tracking-widest"
          />
        </div>

        <div class="flex flex-col sm:flex-row xl:items-center gap-3 sm:gap-4 xl:gap-0 mt-2 xl:mt-0 w-full xl:w-auto">
          <div class="flex gap-1 p-1 bg-black/40 border border-white/5 rounded-xl overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
            {#each ["all", ...CATEGORIES] as c}
              <button
                onclick={() => handleCategoryChange(c)}
                class="px-4 py-2 text-[8px] font-mono uppercase tracking-[0.2em] rounded-lg transition-all relative overflow-hidden group/btn flex-shrink-0
                  {activeCategoryFilter === c
                  ? 'bg-neon-cyan/10 text-neon-cyan/90 ring-1 ring-neon-cyan/30'
                  : 'text-gray-500 hover:text-white hover:bg-white/5'}"
              >
                {c === "all" ? "All_Nodes" : c}
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
                  ? 'bg-[#FF33FF]/10 text-[#FF33FF]/90 ring-1 ring-[#FF33FF]/30'
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
          <span class="text-[9px] font-mono text-[#FF33FF]/40 uppercase tracking-[0.3em]">Loading Content...</span>
        </div>
      {:else}
        <NewsList
          {articles}
          {selectedIds}
          onToggleSelect={toggleSelect}
          onEdit={openEdit}
          onDelete={async (id) => {
            try {
              await apiClient.post("/api/v1/articles/bulk-delete", { ids: [id] });
              await loadArticles();
            } catch { nanobot.showToast("Xóa bài viết thất bại", "error"); }
          }}
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

  <!-- RIGHT: Draft Form (slides in from right) -->
  {#if showDraftForm}
    <div class="news-form-pane border-l border-white/10 overflow-y-auto">
      <DraftGenerativeForm
        {editingId}
        initialTitle={formTitle}
        onSuccess={async () => { showDraftForm = false; await loadArticles(); }}
        onClose={() => (showDraftForm = false)}
      />
    </div>
  {/if}
</div>

<style>
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
</style>
