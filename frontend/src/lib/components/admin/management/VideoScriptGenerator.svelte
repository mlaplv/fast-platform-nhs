<script lang="ts">
  import { fade, slide, fly } from "svelte/transition";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import X from "@lucide/svelte/icons/x";
  import Video from "@lucide/svelte/icons/video";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Search from "@lucide/svelte/icons/search";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import type { VideoScriptStyle, Article } from "$lib/types";
  import { apiClient } from "$lib/utils/apiClient";

  interface Product {
    id: string;
    name: string;
    slug: string;
  }

  interface Props {
    isDrawerOpen: boolean;
    isGenerating: boolean;
    genStep: number;
    sourceType: "product" | "article" | "custom";
    selectedProductId: string;
    selectedArticleId: string;
    customDescription: string;
    extraRequirements: string;
    aspectRatio: string;
    targetDuration: number;
    styles: VideoScriptStyle[];
    selectedStyleId: string;
    handleGenerate: (e: Event) => void;
    // Step-wise generation props
    generatorStep: 1 | 2;
    isAnalyzing: boolean;
    competitorAnalysis: {
      competitor_weaknesses: string[];
      our_strengths: string[];
      core_message: string;
    } | null;
    handleAnalyze: () => void;
  }

  let {
    isDrawerOpen = $bindable(),
    isGenerating,
    genStep,
    sourceType = $bindable(),
    selectedProductId = $bindable(),
    selectedArticleId = $bindable(),
    customDescription = $bindable(),
    extraRequirements = $bindable(),
    aspectRatio = $bindable(),
    targetDuration = $bindable(),
    styles,
    selectedStyleId = $bindable(),
    handleGenerate,
    generatorStep = $bindable(),
    isAnalyzing,
    competitorAnalysis = $bindable(),
    handleAnalyze,
  }: Props = $props();

  // Local state for products and articles selection dropdowns
  let products = $state<Product[]>([]);
  let productsSearch = $state("");
  let nextProductsCursor = $state<string | null>(null);
  let hasMoreProducts = $state(true);
  let isProductsLoading = $state(false);

  let articles = $state<Article[]>([]);
  let articlesSearch = $state("");
  let nextArticlesCursor = $state<string | null>(null);
  let hasMoreArticles = $state(true);
  let isArticlesLoading = $state(false);

  // Dropdown active state
  let activeDropdown = $state<
    "product" | "article" | "aspectRatio" | "duration" | "style" | null
  >(null);

  function toggleDropdown(
    name: "product" | "article" | "aspectRatio" | "duration" | "style",
    e: Event,
  ) {
    e.stopPropagation();
    activeDropdown = activeDropdown === name ? null : name;
  }

  function closeAllDropdowns() {
    activeDropdown = null;
  }

  // Fetching logic for products and articles using Keyset Cursor Pagination
  async function fetchProducts(reset = false) {
    if (isProductsLoading) return;
    if (!reset && !hasMoreProducts) return;

    isProductsLoading = true;

    try {
      const params = new URLSearchParams({
        limit: "20",
      });
      if (productsSearch.trim()) {
        params.append("search", productsSearch.trim());
      }
      if (!reset && nextProductsCursor) {
        params.append("cursor", nextProductsCursor);
      }

      const res = await apiClient.get<{
        data: Product[];
        next_cursor: string | null;
        has_more: boolean;
      }>(`/api/v1/products?${params.toString()}`);

      const newItems = res.data || [];

      if (reset) {
        products = newItems;
      } else {
        products = [...products, ...newItems];
      }

      nextProductsCursor = res.next_cursor || null;
      hasMoreProducts = res.has_more ?? newItems.length === 20;

      // Auto-select first item if none is selected
      if (reset && products.length > 0 && !selectedProductId) {
        selectedProductId = products[0].id;
      }
    } catch (err) {
      console.error("Failed to fetch products:", err);
    } finally {
      isProductsLoading = false;
    }
  }

  async function fetchArticles(reset = false) {
    if (isArticlesLoading) return;
    if (!reset && !hasMoreArticles) return;

    isArticlesLoading = true;

    try {
      const params = new URLSearchParams({
        limit: "20",
      });
      if (articlesSearch.trim()) {
        params.append("search", articlesSearch.trim());
      }
      if (!reset && nextArticlesCursor) {
        params.append("cursor", nextArticlesCursor);
      }

      const res = await apiClient.get<{
        data: Article[];
        next_cursor: string | null;
        has_more: boolean;
      }>(`/api/v1/articles?${params.toString()}`);

      const newItems = res.data || [];

      if (reset) {
        articles = newItems;
      } else {
        articles = [...articles, ...newItems];
      }

      nextArticlesCursor = res.next_cursor || null;
      hasMoreArticles = res.has_more ?? newItems.length === 20;

      // Auto-select first item if none is selected
      if (reset && articles.length > 0 && !selectedArticleId) {
        selectedArticleId = articles[0].id;
      }
    } catch (err) {
      console.error("Failed to fetch articles:", err);
    } finally {
      isArticlesLoading = false;
    }
  }

  // Debounced search handlers
  let productsSearchTimeout: ReturnType<typeof setTimeout>;
  function handleProductsSearch(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    productsSearch = val;
    clearTimeout(productsSearchTimeout);
    productsSearchTimeout = setTimeout(() => {
      fetchProducts(true);
    }, 300);
  }

  let articlesSearchTimeout: ReturnType<typeof setTimeout>;
  function handleArticlesSearch(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    articlesSearch = val;
    clearTimeout(articlesSearchTimeout);
    articlesSearchTimeout = setTimeout(() => {
      fetchArticles(true);
    }, 300);
  }

  // Scroll event listeners for pagination
  function handleProductsScroll(e: Event) {
    const target = e.target as HTMLDivElement;
    if (target.scrollHeight - target.scrollTop - target.clientHeight < 20) {
      fetchProducts(false);
    }
  }

  // Scroll event listeners for pagination
  function handleArticlesScroll(e: Event) {
    const target = e.target as HTMLDivElement;
    if (target.scrollHeight - target.scrollTop - target.clientHeight < 20) {
      fetchArticles(false);
    }
  }

  // Trigger loading when drawer opens or sourceType changes
  $effect(() => {
    if (isDrawerOpen) {
      if (products.length === 0) {
        fetchProducts(true);
      }
      if (articles.length === 0) {
        fetchArticles(true);
      }
    }
  });
</script>

<!-- DRAWER: Generate Script Form -->
{#if isDrawerOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 bg-black/80 backdrop-blur-xs flex items-center justify-end z-[110]"
    transition:fade={{ duration: 200 }}
    onclick={() => !isGenerating && !isAnalyzing && (isDrawerOpen = false)}
  >
    <!-- Drawer panel -->
    <div
      class="w-full max-w-md h-full bg-[#080808] border-l border-gray-800 p-6 flex flex-col justify-between overflow-y-auto"
      transition:fly={{ x: 400, duration: 250 }}
      onclick={(e) => e.stopPropagation()}
    >
      <div class="flex-1 flex flex-col justify-between">
        <div>
          <!-- Drawer Header -->
          <div
            class="flex items-center justify-between pb-4 border-b border-gray-900 mb-6"
          >
            <div class="flex items-center gap-2">
              {#if generatorStep === 2 && !isGenerating && !isAnalyzing}
                <button
                  onclick={() => {
                    generatorStep = 1;
                  }}
                  class="p-1 hover:bg-white/5 rounded text-gray-400 hover:text-white transition-colors mr-1"
                  title="Quay lại bước trước"
                >
                  <ArrowLeft class="w-4 h-4" />
                </button>
              {/if}
              <Sparkles class="w-4 h-4 text-cyan-400" />
              <h3
                class="text-xs font-bold text-white tracking-widest uppercase"
              >
                {generatorStep === 1
                  ? "BƯỚC 1: THIẾT LẬP NGUỒN"
                  : "BƯỚC 2: CHIẾN LƯỢC CẠNH TRANH"}
              </h3>
            </div>
            <button
              onclick={() => {
                isDrawerOpen = false;
              }}
              disabled={isGenerating || isAnalyzing}
              class="p-1.5 hover:bg-white/5 rounded text-gray-400 hover:text-white transition-colors"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          {#if isAnalyzing}
            <!-- Analyzing Status Loading Screen -->
            <div class="py-20 flex flex-col items-center justify-center gap-6">
              <div class="relative w-16 h-16 flex items-center justify-center">
                <div
                  class="absolute inset-0 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin"
                ></div>
                <Sparkles class="w-6 h-6 text-cyan-400 animate-pulse" />
              </div>
              <div class="text-center space-y-2">
                <p class="text-xs font-semibold text-cyan-400 animate-pulse">
                  Quét Google Search & Phân tích đối thủ...
                </p>
                <p
                  class="text-[9px] font-mono text-gray-500 leading-relaxed max-w-[280px] mx-auto"
                >
                  Hệ thống đang thu thập chiến dịch của đối thủ trên thị trường
                  và lập luận ưu thế sản phẩm của bạn.
                </p>
              </div>
            </div>
          {:else if isGenerating}
            <!-- Generating Status Loading Screen -->
            <div class="py-20 flex flex-col items-center justify-center gap-6">
              <div class="relative w-16 h-16 flex items-center justify-center">
                <div
                  class="absolute inset-0 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin"
                ></div>
                <Video class="w-6 h-6 text-cyan-400 animate-pulse" />
              </div>

              <div class="w-full max-w-[280px] space-y-3 mt-4 mx-auto">
                <div class="flex items-center gap-3 text-xs">
                  <span
                    class="w-4 h-4 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-500 flex items-center justify-center text-[9px] font-mono"
                  >
                    ✓
                  </span>
                  <span class="text-gray-400 line-through">
                    Google Search & Phân tích phản biện đối thủ
                  </span>
                </div>
                <div class="flex items-center gap-3 text-xs">
                  <span
                    class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                               {genStep >= 2
                      ? 'bg-cyan-950 text-cyan-400 border-cyan-500'
                      : 'text-gray-600 border-gray-800'}"
                  >
                    2
                  </span>
                  <span
                    class={genStep === 2
                      ? "text-cyan-400 font-semibold animate-pulse"
                      : genStep > 2
                        ? "text-gray-400"
                        : "text-gray-600"}
                  >
                    AI Core thiết lập kịch bản phân cảnh & USP...
                  </span>
                </div>
                <div class="flex items-center gap-3 text-xs">
                  <span
                    class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                               {genStep >= 3
                      ? 'bg-cyan-950 text-cyan-400 border-cyan-500'
                      : 'text-gray-600 border-gray-800'}"
                  >
                    3
                  </span>
                  <span
                    class={genStep === 3
                      ? "text-cyan-400 font-semibold"
                      : "text-gray-600"}
                  >
                    Hoàn thiện và đồng bộ hóa cơ sở dữ liệu...
                  </span>
                </div>
              </div>

              <p
                class="text-[9px] font-mono text-gray-500 tracking-wider text-center mt-6"
              >
                Vui lòng không đóng cửa sổ. AI đang soạn thảo...
              </p>
            </div>
          {:else if generatorStep === 1}
            <!-- Step 1: Input Config Form -->
            <div class="space-y-5">
              <!-- Source Type selection -->
              <div class="space-y-2">
                <label
                  class="text-[10px] font-mono tracking-wider text-gray-400 uppercase"
                  >NGUỒN DỮ LIỆU ĐẦU VÀO</label
                >
                <div
                  class="grid grid-cols-3 gap-2 p-1 bg-[#111] rounded-lg border border-gray-800"
                >
                  <button
                    type="button"
                    onclick={() => {
                      sourceType = "product";
                    }}
                    class="py-1 text-[11px] rounded transition-all font-semibold
                           {sourceType === 'product'
                      ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20'
                      : 'text-gray-400 hover:text-white'}"
                  >
                    Sản phẩm
                  </button>
                  <button
                    type="button"
                    onclick={() => {
                      sourceType = "article";
                    }}
                    class="py-1 text-[11px] rounded transition-all font-semibold
                           {sourceType === 'article'
                      ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20'
                      : 'text-gray-400 hover:text-white'}"
                  >
                    Bài viết
                  </button>
                  <button
                    type="button"
                    onclick={() => {
                      sourceType = "custom";
                    }}
                    class="py-1 text-[11px] rounded transition-all font-semibold
                           {sourceType === 'custom'
                      ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20'
                      : 'text-gray-400 hover:text-white'}"
                  >
                    Nhập tay
                  </button>
                </div>
              </div>

              <!-- Dynamic Input Area based on source type -->
              {#if sourceType === "product"}
                <div class="space-y-2">
                  <label
                    for="product-select"
                    class="text-[10px] font-mono tracking-wider text-gray-400 uppercase"
                    >CHỌN SẢN PHẨM TIÊU ĐIỂM</label
                  >
                  <div class="relative">
                    <button
                      type="button"
                      onclick={(e) => toggleDropdown("product", e)}
                      class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 hover:border-gray-750/90 rounded-lg px-3 py-2 text-xs text-white flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                    >
                      <span class="truncate"
                        >{!selectedProductId
                          ? "Chọn sản phẩm..."
                          : products.find((p) => p.id === selectedProductId)
                              ?.name || "Chọn sản phẩm..."}</span
                      >
                      <ChevronDown
                        class="w-4 h-4 text-gray-505 transition-transform duration-200 {activeDropdown ===
                        'product'
                          ? 'rotate-180 text-cyan-400'
                          : ''}"
                      />
                    </button>

                    {#if activeDropdown === "product"}
                      <div
                        transition:fade={{ duration: 100 }}
                        class="absolute z-50 left-0 right-0 mt-1.5 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 max-h-72 flex flex-col overflow-hidden"
                      >
                        <!-- Search Box -->
                        <div
                          class="p-2 border-b border-gray-850 bg-black/40 flex items-center gap-2"
                        >
                          <Search class="w-3.5 h-3.5 text-gray-500" />
                          <input
                            type="text"
                            placeholder="Tìm kiếm sản phẩm..."
                            value={productsSearch}
                            oninput={handleProductsSearch}
                            class="w-full bg-transparent text-xs text-white placeholder-gray-600 focus:outline-none"
                            onclick={(e) => e.stopPropagation()}
                          />
                          {#if productsSearch}
                            <button
                              type="button"
                              onclick={(e) => {
                                e.stopPropagation();
                                productsSearch = "";
                                fetchProducts(true);
                              }}
                              class="p-0.5 hover:bg-white/5 rounded text-gray-500 hover:text-white transition-colors"
                            >
                              <X class="w-3 h-3" />
                            </button>
                          {/if}
                        </div>

                        <!-- Scrollable List -->
                        <div
                          onscroll={handleProductsScroll}
                          class="flex-1 overflow-y-auto py-1 max-h-56 custom-scrollbar"
                        >
                          {#if products.length === 0}
                            <div
                              class="px-3 py-4 text-center text-xs text-gray-500"
                            >
                              {#if isProductsLoading}
                                <div
                                  class="flex items-center justify-center gap-2"
                                >
                                  <Loader2
                                    class="w-3.5 h-3.5 text-cyan-400 animate-spin"
                                  />
                                  <span>Đang tải...</span>
                                </div>
                              {:else}
                                Không tìm thấy sản phẩm nào
                              {/if}
                            </div>
                          {:else}
                            {#each products as prod}
                              <button
                                type="button"
                                onclick={() => {
                                  selectedProductId = prod.id;
                                  activeDropdown = null;
                                }}
                                class="w-full text-left px-3 py-2 text-xs transition-colors truncate block
                                       {selectedProductId === prod.id
                                  ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                                  : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                              >
                                {prod.name} (SKU/Slug: {prod.slug})
                              </button>
                            {/each}

                            {#if isProductsLoading}
                              <div
                                class="px-3 py-2 text-center text-xs text-cyan-400/80 flex items-center justify-center gap-1.5 border-t border-white/5 bg-black/10"
                              >
                                <Loader2 class="w-3 h-3 animate-spin" />
                                <span>Đang tải thêm...</span>
                              </div>
                            {/if}
                          {/if}
                        </div>
                      </div>
                    {/if}
                  </div>
                  <p class="text-[9px] font-mono text-gray-500 leading-normal">
                    Hệ thống sẽ chạy Google Search đối thủ và phân tích ưu điểm
                    sản phẩm để làm định hướng kịch bản.
                  </p>
                </div>
              {:else if sourceType === "article"}
                <div class="space-y-2">
                  <label
                    for="article-select"
                    class="text-[10px] font-mono tracking-wider text-gray-400 uppercase"
                    >CHỌN BÀI VIẾT LÀM NGUỒN</label
                  >
                  <div class="relative">
                    <button
                      type="button"
                      onclick={(e) => toggleDropdown("article", e)}
                      class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 hover:border-gray-750/90 rounded-lg px-3 py-2 text-xs text-white flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                    >
                      <span class="truncate"
                        >{!selectedArticleId
                          ? "Chọn bài viết..."
                          : articles.find((a) => a.id === selectedArticleId)
                              ?.title || "Chọn bài viết..."}</span
                      >
                      <ChevronDown
                        class="w-4 h-4 text-gray-505 transition-transform duration-200 {activeDropdown ===
                        'article'
                          ? 'rotate-180 text-cyan-400'
                          : ''}"
                      />
                    </button>

                    {#if activeDropdown === "article"}
                      <div
                        transition:fade={{ duration: 100 }}
                        class="absolute z-50 left-0 right-0 mt-1.5 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 max-h-72 flex flex-col overflow-hidden"
                      >
                        <!-- Search Box -->
                        <div
                          class="p-2 border-b border-gray-850 bg-black/40 flex items-center gap-2"
                        >
                          <Search class="w-3.5 h-3.5 text-gray-500" />
                          <input
                            type="text"
                            placeholder="Tìm kiếm bài viết..."
                            value={articlesSearch}
                            oninput={handleArticlesSearch}
                            class="w-full bg-transparent text-xs text-white placeholder-gray-600 focus:outline-none"
                            onclick={(e) => e.stopPropagation()}
                          />
                          {#if articlesSearch}
                            <button
                              type="button"
                              onclick={(e) => {
                                e.stopPropagation();
                                articlesSearch = "";
                                fetchArticles(true);
                              }}
                              class="p-0.5 hover:bg-white/5 rounded text-gray-500 hover:text-white transition-colors"
                            >
                              <X class="w-3 h-3" />
                            </button>
                          {/if}
                        </div>

                        <!-- Scrollable List -->
                        <div
                          onscroll={handleArticlesScroll}
                          class="flex-1 overflow-y-auto py-1 max-h-56 custom-scrollbar"
                        >
                          {#if articles.length === 0}
                            <div
                              class="px-3 py-4 text-center text-xs text-gray-500"
                            >
                              {#if isArticlesLoading}
                                <div
                                  class="flex items-center justify-center gap-2"
                                >
                                  <Loader2
                                    class="w-3.5 h-3.5 text-cyan-400 animate-spin"
                                  />
                                  <span>Đang tải...</span>
                                </div>
                              {:else}
                                Không tìm thấy bài viết nào
                              {/if}
                            </div>
                          {:else}
                            {#each articles as art}
                              <button
                                type="button"
                                onclick={() => {
                                  selectedArticleId = art.id;
                                  activeDropdown = null;
                                }}
                                class="w-full text-left px-3 py-2 text-xs transition-colors truncate block
                                       {selectedArticleId === art.id
                                  ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                                  : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                              >
                                {art.title}
                              </button>
                            {/each}

                            {#if isArticlesLoading}
                              <div
                                class="px-3 py-2 text-center text-xs text-cyan-400/80 flex items-center justify-center gap-1.5 border-t border-white/5 bg-black/10"
                              >
                                <Loader2 class="w-3 h-3 animate-spin" />
                                <span>Đang tải thêm...</span>
                              </div>
                            {/if}
                          {/if}
                        </div>
                      </div>
                    {/if}
                  </div>
                  <p class="text-[9px] font-mono text-gray-500 leading-normal">
                    Chuyển hóa nội dung bài viết tin tức/chia sẻ thành kịch bản
                    phân cảnh video.
                  </p>
                </div>
              {:else}
                <div class="space-y-2">
                  <label
                    for="custom-desc"
                    class="text-[10px] font-mono tracking-wider text-gray-400 uppercase"
                    >MÔ TẢ CHI TIẾT Ý TƯỞNG</label
                  >
                  <textarea
                    id="custom-desc"
                    bind:value={customDescription}
                    rows="5"
                    placeholder="Nhập ý tưởng video, mô tả sản phẩm dịch vụ, hoặc điểm nổi bật bạn muốn quảng cáo..."
                    class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 resize-y min-h-[100px] leading-relaxed"
                  ></textarea>
                  <p class="text-[9px] font-mono text-gray-500 leading-normal">
                    Viết bất kỳ ý tưởng thô nào của bạn, AI sẽ xây dựng chiến
                    lược và kịch bản.
                  </p>
                </div>
              {/if}

              <!-- Settings Grid: Aspect Ratio & Duration -->
              <div class="grid grid-cols-2 gap-4">
                <!-- Aspect Ratio -->
                <div class="space-y-2">
                  <label
                    for="aspect-ratio-select"
                    class="text-[10px] font-mono tracking-wider text-gray-400 uppercase"
                    >KHUNG HÌNH (THIẾT BỊ)</label
                  >
                  <div class="relative">
                    <button
                      type="button"
                      onclick={(e) => toggleDropdown("aspectRatio", e)}
                      class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 hover:border-gray-750/90 rounded-lg px-3 py-2 text-xs text-white flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                    >
                      <span class="truncate"
                        >{aspectRatio === "9:16"
                          ? "Dọc (9:16) - TikTok/Reels"
                          : aspectRatio === "16:9"
                            ? "Ngang (16:9) - YouTube/PC"
                            : "Vuông (1:1) - Instagram"}</span
                      >
                      <ChevronDown
                        class="w-4 h-4 text-gray-505 transition-transform duration-200 {activeDropdown ===
                        'aspectRatio'
                          ? 'rotate-180 text-cyan-400'
                          : ''}"
                      />
                    </button>

                    {#if activeDropdown === "aspectRatio"}
                      <div
                        transition:fade={{ duration: 100 }}
                        class="absolute z-50 left-0 right-0 mt-1.5 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 overflow-hidden py-1"
                      >
                        <button
                          type="button"
                          onclick={() => {
                            aspectRatio = "9:16";
                            activeDropdown = null;
                          }}
                          class="w-full text-left px-3 py-2 text-xs transition-colors
                                 {aspectRatio === '9:16'
                            ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                        >
                          Dọc (9:16) - TikTok/Reels
                        </button>
                        <button
                          type="button"
                          onclick={() => {
                            aspectRatio = "16:9";
                            activeDropdown = null;
                          }}
                          class="w-full text-left px-3 py-2 text-xs transition-colors
                                 {aspectRatio === '16:9'
                            ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                        >
                          Ngang (16:9) - YouTube/PC
                        </button>
                        <button
                          type="button"
                          onclick={() => {
                            aspectRatio = "1:1";
                            activeDropdown = null;
                          }}
                          class="w-full text-left px-3 py-2 text-xs transition-colors
                                 {aspectRatio === '1:1'
                            ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                        >
                          Vuông (1:1) - Instagram
                        </button>
                      </div>
                    {/if}
                  </div>
                </div>

                <!-- Duration -->
                <div class="space-y-2">
                  <label
                    for="duration-select"
                    class="text-[10px] font-mono tracking-wider text-gray-400 uppercase"
                    >THỜI LƯỢNG MỤC TIÊU</label
                  >
                  <div class="relative">
                    <button
                      type="button"
                      onclick={(e) => toggleDropdown("duration", e)}
                      class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 hover:border-gray-750/90 rounded-lg px-3 py-2 text-xs text-white flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                    >
                      <span class="truncate"
                        >{targetDuration === 15
                          ? "15 giây (Cực ngắn)"
                          : targetDuration === 30
                            ? "30 giây (Tiêu chuẩn)"
                            : targetDuration === 60
                              ? "60 giây (Chi tiết)"
                              : "90 giây (Kể chuyện)"}</span
                      >
                      <ChevronDown
                        class="w-4 h-4 text-gray-505 transition-transform duration-200 {activeDropdown ===
                        'duration'
                          ? 'rotate-180 text-cyan-400'
                          : ''}"
                      />
                    </button>

                    {#if activeDropdown === "duration"}
                      <div
                        transition:fade={{ duration: 100 }}
                        class="absolute z-50 left-0 right-0 mt-1.5 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 overflow-hidden py-1"
                      >
                        <button
                          type="button"
                          onclick={() => {
                            targetDuration = 15;
                            activeDropdown = null;
                          }}
                          class="w-full text-left px-3 py-2 text-xs transition-colors
                                 {targetDuration === 15
                            ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                        >
                          15 giây (Cực ngắn)
                        </button>
                        <button
                          type="button"
                          onclick={() => {
                            targetDuration = 30;
                            activeDropdown = null;
                          }}
                          class="w-full text-left px-3 py-2 text-xs transition-colors
                                 {targetDuration === 30
                            ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                        >
                          30 giây (Tiêu chuẩn)
                        </button>
                        <button
                          type="button"
                          onclick={() => {
                            targetDuration = 60;
                            activeDropdown = null;
                          }}
                          class="w-full text-left px-3 py-2 text-xs transition-colors
                                 {targetDuration === 60
                            ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                        >
                          60 giây (Chi tiết)
                        </button>
                        <button
                          type="button"
                          onclick={() => {
                            targetDuration = 90;
                            activeDropdown = null;
                          }}
                          class="w-full text-left px-3 py-2 text-xs transition-colors
                                 {targetDuration === 90
                            ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                            : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                        >
                          90 giây (Kể chuyện)
                        </button>
                      </div>
                    {/if}
                  </div>
                </div>
              </div>

              <!-- Style selection -->
              <div class="space-y-2">
                <label
                  for="style-select"
                  class="text-[10px] font-mono tracking-wider text-gray-400 uppercase"
                  >PHONG CÁCH / XU HƯỚNG VIDEO</label
                >
                <div class="relative">
                  <button
                    type="button"
                    onclick={(e) => toggleDropdown("style", e)}
                    class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 hover:border-gray-750/90 rounded-lg px-3 py-2 text-xs text-white flex items-center justify-between transition-all focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                  >
                    <span class="truncate"
                      >{!selectedStyleId
                        ? "Chọn phong cách..."
                        : styles.find((s) => s.id === selectedStyleId)
                          ? `[${styles.find((s) => s.id === selectedStyleId)!.platform}] ${styles.find((s) => s.id === selectedStyleId)!.name}`
                          : "Chọn phong cách..."}</span
                    >
                    <ChevronDown
                      class="w-4 h-4 text-gray-505 transition-transform duration-200 {activeDropdown ===
                      'style'
                        ? 'rotate-180 text-cyan-400'
                        : ''}"
                    />
                  </button>

                  {#if activeDropdown === "style"}
                    <div
                      transition:fade={{ duration: 100 }}
                      class="absolute z-50 left-0 right-0 mt-1.5 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 max-h-60 overflow-y-auto py-1"
                    >
                      {#if styles.length === 0}
                        <button
                          type="button"
                          disabled
                          class="w-full text-left px-3 py-2 text-xs text-gray-505 cursor-not-allowed"
                        >
                          Không tìm thấy phong cách nào
                        </button>
                      {:else}
                        {#each styles as style}
                          <button
                            type="button"
                            onclick={() => {
                              selectedStyleId = style.id;
                              activeDropdown = null;
                            }}
                            class="w-full text-left px-3 py-2 text-xs transition-colors truncate
                                   {selectedStyleId === style.id
                              ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                              : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                          >
                            [{style.platform}] {style.name}
                          </button>
                        {/each}
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>

              <!-- Style instruction details panel -->
              {#if styles.find((s) => s.id === selectedStyleId)}
                {@const currentStyle = styles.find(
                  (s) => s.id === selectedStyleId,
                )!}
                <div
                  class="bg-[#0c0c0c] border border-cyan-500/10 rounded-lg p-3 space-y-2"
                >
                  <span
                    class="text-[9px] font-mono text-cyan-400 font-bold uppercase tracking-widest block font-sans"
                    >CHI TIẾT PHONG CÁCH ĐÃ CHỌN</span
                  >
                  <div
                    class="text-[10px] space-y-1 text-gray-400 leading-relaxed font-sans"
                  >
                    <p>
                      <strong>Cấu trúc Hook:</strong>
                      <span class="text-gray-300 italic"
                        >{currentStyle.hook_template}</span
                      >
                    </p>
                    <p class="line-clamp-2">
                      <strong>Chỉ dẫn:</strong>
                      {currentStyle.style_instruction}
                    </p>
                  </div>
                </div>
              {/if}

              <!-- Extra Requirements: Yêu cầu thêm quan trọng -->
              <div class="space-y-2">
                <label
                  for="extra-req-input"
                  class="flex items-center gap-1.5 text-[10px] font-mono tracking-wider text-amber-400 uppercase"
                >
                  <span
                    class="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"
                  ></span>
                  YÊU CẦU THÊM QUAN TRỌNG
                  <span class="text-gray-500 normal-case font-sans"
                    >(tùy chọn)</span
                  >
                </label>
                <textarea
                  id="extra-req-input"
                  bind:value={extraRequirements}
                  rows="3"
                  placeholder="VD: Video phải có cảnh close-up sản phẩm ít nhất 2 phân cảnh. Nhân vật mặc áo trắng. Nền pastel be/kem nhẹ. Không có cảnh ngoài trời. Mở đầu bằng câu hỏi..."
                  class="w-full bg-[#0c0c10] border border-amber-500/20 hover:border-amber-500/40 focus:border-amber-500/60 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none resize-none min-h-[70px] leading-relaxed placeholder:text-gray-600 transition-colors"
                ></textarea>
                <p class="text-[9px] font-mono text-gray-500 leading-normal">
                  AI sẽ bắt buộc tuân theo các yêu cầu này khi soạn thảo và tối
                  ưu hóa kịch bản.
                </p>
              </div>
            </div>
          {:else if generatorStep === 2 && competitorAnalysis}
            <!-- Step 2: Review and Edit USP & Competitor Analysis -->
            <div class="space-y-5">
              <div
                class="bg-cyan-950/15 border border-cyan-500/10 rounded-lg p-3 space-y-1"
              >
                <p class="text-xs font-semibold text-cyan-300">
                  Đã thiết lập xong định vị chiến lược
                </p>
                <p class="text-[10px] text-gray-400 leading-relaxed">
                  Dưới đây là kết quả phân tích phản biện đối thủ cạnh tranh.
                  Hãy tùy chỉnh theo đúng thực tế trước khi AI viết kịch bản.
                </p>
              </div>

              <!-- Competitor Weaknesses -->
              <div class="space-y-2">
                <span
                  class="text-[9px] font-mono text-pink-500 tracking-wider font-semibold uppercase block"
                  >3 ĐIỂM YẾU CỦA ĐỐI THỦ CẠNH TRANH</span
                >
                {#each competitorAnalysis.competitor_weaknesses as weakness, idx}
                  <div class="flex gap-2 items-center">
                    <span
                      class="text-[10px] font-mono text-pink-500/60 font-bold"
                      >#{idx + 1}</span
                    >
                    <input
                      type="text"
                      bind:value={competitorAnalysis.competitor_weaknesses[idx]}
                      class="flex-1 bg-[#111] border border-gray-800 rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-pink-500/40"
                    />
                  </div>
                {/each}
              </div>

              <!-- Our Strengths / USP -->
              <div class="space-y-2">
                <span
                  class="text-[9px] font-mono text-cyan-400 tracking-wider font-semibold uppercase block"
                  >3 ĐIỂM MẠNH NỔI TRỘI CỦA TA (USP)</span
                >
                {#each competitorAnalysis.our_strengths as strength, idx}
                  <div class="flex gap-2 items-center">
                    <span
                      class="text-[10px] font-mono text-cyan-400/60 font-bold"
                      >#{idx + 1}</span
                    >
                    <input
                      type="text"
                      bind:value={competitorAnalysis.our_strengths[idx]}
                      class="flex-1 bg-[#111] border border-gray-800 rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-cyan-500/40"
                    />
                  </div>
                {/each}
              </div>

              <!-- Core Message -->
              <div class="space-y-2">
                <label
                  for="core-message-input"
                  class="text-[9px] font-mono text-yellow-500 tracking-wider font-semibold uppercase block"
                  >THÔNG ĐIỆP CỐT LÕI (CORE MESSAGE)</label
                >
                <textarea
                  id="core-message-input"
                  bind:value={competitorAnalysis.core_message}
                  rows="4"
                  class="w-full bg-[#111] border border-gray-800 rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-yellow-500/40 resize-y min-h-[80px] leading-relaxed"
                ></textarea>
              </div>
            </div>
          {/if}
        </div>

        <!-- Footer Buttons -->
        {#if !isGenerating && !isAnalyzing}
          <div
            class="flex items-center gap-3 border-t border-gray-900 pt-4 mt-6"
          >
            {#if generatorStep === 1}
              <button
                onclick={() => {
                  isDrawerOpen = false;
                }}
                class="flex-1 py-2 bg-gray-900 hover:bg-gray-800 text-gray-300 text-xs font-semibold rounded-lg border border-gray-800 transition-colors"
              >
                Hủy bỏ
              </button>
              <button
                onclick={handleAnalyze}
                class="flex-1 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-black text-xs font-bold rounded-lg hover:opacity-90 shadow-md shadow-cyan-500/10 transition-all"
              >
                Bước 1: Phân tích đối thủ
              </button>
            {:else if generatorStep === 2}
              <button
                onclick={() => {
                  generatorStep = 1;
                }}
                class="py-2 px-3 bg-gray-900 hover:bg-gray-800 text-gray-300 text-xs font-semibold rounded-lg border border-gray-800 transition-colors"
              >
                Quay lại
              </button>
              <button
                onclick={handleGenerate}
                class="flex-1 py-2 bg-gradient-to-r from-pink-500 to-cyan-500 text-black text-xs font-bold rounded-lg hover:opacity-90 shadow-md shadow-cyan-500/10 transition-all"
              >
                Bước 2: Sinh kịch bản video AI
              </button>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<svelte:window onclick={closeAllDropdowns} />

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }
</style>
