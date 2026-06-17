<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import X from "@lucide/svelte/icons/x";
  import Video from "@lucide/svelte/icons/video";
  import type { VideoScriptStyle, Article } from "$lib/types";

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
    products: Product[];
    selectedProductId: string;
    articles: Article[];
    selectedArticleId: string;
    customDescription: string;
    aspectRatio: string;
    targetDuration: number;
    styles: VideoScriptStyle[];
    selectedStyleId: string;
    handleGenerate: (e: Event) => void;
  }

  let {
    isDrawerOpen = $bindable(),
    isGenerating,
    genStep,
    sourceType = $bindable(),
    products,
    selectedProductId = $bindable(),
    articles,
    selectedArticleId = $bindable(),
    customDescription = $bindable(),
    aspectRatio = $bindable(),
    targetDuration = $bindable(),
    styles,
    selectedStyleId = $bindable(),
    handleGenerate
  }: Props = $props();
</script>

<!-- DRAWER: Generate Script Form -->
{#if isDrawerOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 bg-black/80 backdrop-blur-xs flex items-center justify-end z-[110]"
    transition:fade={{ duration: 200 }}
    onclick={() => !isGenerating && (isDrawerOpen = false)}
  >
    <!-- Drawer panel -->
    <div
      class="w-full max-w-md h-full bg-[#080808] border-l border-gray-800 p-6 flex flex-col justify-between"
      transition:slide={{ direction: 'right', duration: 250 }}
      onclick={(e) => e.stopPropagation()}
    >
      <div>
        <!-- Drawer Header -->
        <div class="flex items-center justify-between pb-4 border-b border-gray-900 mb-6">
          <div class="flex items-center gap-2">
            <Sparkles class="w-4 h-4 text-cyan-400" />
            <h3 class="text-sm font-bold text-white tracking-widest uppercase">SINH KỊCH BẢN VIDEO</h3>
          </div>
          <button
            onclick={() => { isDrawerOpen = false; }}
            disabled={isGenerating}
            class="p-1.5 hover:bg-white/5 rounded text-gray-400 hover:text-white transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        {#if isGenerating}
          <!-- Generating Status Loading Screen -->
          <div class="py-12 flex flex-col items-center justify-center gap-6">
            <div class="relative w-16 h-16 flex items-center justify-center">
              <div class="absolute inset-0 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin"></div>
              <Video class="w-6 h-6 text-cyan-400 animate-pulse" />
            </div>

            <div class="w-full space-y-3 mt-4">
              <div class="flex items-center gap-3 text-xs">
                <span class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                             {genStep >= 1 ? 'bg-cyan-950 text-cyan-400 border-cyan-500' : 'text-gray-600 border-gray-800'}">
                  1
                </span>
                <span class={genStep === 1 ? 'text-cyan-400 font-semibold' : genStep > 1 ? 'text-gray-400' : 'text-gray-600'}>
                  Google Search & Phân tích phản biện đối thủ...
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs">
                <span class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                             {genStep >= 2 ? 'bg-cyan-950 text-cyan-400 border-cyan-500' : 'text-gray-600 border-gray-800'}">
                  2
                </span>
                <span class={genStep === 2 ? 'text-cyan-400 font-semibold animate-pulse' : genStep > 2 ? 'text-gray-400' : 'text-gray-600'}>
                  AI Core thiết lập kịch bản phân cảnh & USP...
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs">
                <span class="w-4 h-4 rounded-full border border-cyan-500/30 flex items-center justify-center text-[9px] font-mono
                             {genStep >= 3 ? 'bg-cyan-950 text-cyan-400 border-cyan-500' : 'text-gray-600 border-gray-800'}">
                  3
                </span>
                <span class={genStep === 3 ? 'text-cyan-400 font-semibold' : 'text-gray-600'}>
                  Hoàn thiện và đồng bộ hóa cơ sở dữ liệu...
                </span>
              </div>
            </div>
            
            <p class="text-[9px] font-mono text-gray-500 tracking-wider text-center mt-6">
              Vui lòng không đóng cửa sổ. AI đang tính toán...
            </p>
          </div>
        {:else}
          <!-- Creation Form -->
          <form onsubmit={handleGenerate} class="space-y-5">
            <!-- Source Type selection -->
            <div class="space-y-2">
              <label class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">NGUỒN DỮ LIỆU ĐẦU VÀO</label>
              <div class="grid grid-cols-3 gap-2 p-1 bg-[#111] rounded-lg border border-gray-800">
                <button
                  type="button"
                  onclick={() => { sourceType = "product"; }}
                  class="py-1 text-[11px] rounded transition-all font-semibold
                         {sourceType === 'product' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20' : 'text-gray-400 hover:text-white'}"
                >
                  Sản phẩm
                </button>
                <button
                  type="button"
                  onclick={() => { sourceType = "article"; }}
                  class="py-1 text-[11px] rounded transition-all font-semibold
                         {sourceType === 'article' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20' : 'text-gray-400 hover:text-white'}"
                >
                  Bài viết
                </button>
                <button
                  type="button"
                  onclick={() => { sourceType = "custom"; }}
                  class="py-1 text-[11px] rounded transition-all font-semibold
                         {sourceType === 'custom' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/20' : 'text-gray-400 hover:text-white'}"
                >
                  Nhập tay
                </button>
              </div>
            </div>

            <!-- Dynamic Input Area based on source type -->
            {#if sourceType === "product"}
              <div class="space-y-2">
                <label for="product-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">CHỌN SẢN PHẨM TIÊU ĐIỂM</label>
                <select
                  id="product-select"
                  bind:value={selectedProductId}
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  {#if products.length === 0}
                    <option value="">Không tìm thấy sản phẩm nào</option>
                  {:else}
                    {#each products as prod}
                      <option value={prod.id}>{prod.name} (SKU/Slug: {prod.slug})</option>
                    {/each}
                  {/if}
                </select>
                <p class="text-[9px] font-mono text-gray-500 leading-normal">
                  Hệ thống tự động phân tích ưu điểm sản phẩm để làm chất liệu viết kịch bản.
                </p>
              </div>
            {:else if sourceType === "article"}
              <div class="space-y-2">
                <label for="article-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">CHỌN BÀI VIẾT LÀM NGUỒN</label>
                <select
                  id="article-select"
                  bind:value={selectedArticleId}
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  {#if articles.length === 0}
                    <option value="">Không tìm thấy bài viết nào</option>
                  {:else}
                    {#each articles as art}
                      <option value={art.id}>{art.title}</option>
                    {/each}
                  {/if}
                </select>
                <p class="text-[9px] font-mono text-gray-500 leading-normal">
                  Chuyển hóa nội dung bài viết tin tức/chia sẻ thành kịch bản phân cảnh video sinh động.
                </p>
              </div>
            {:else}
              <div class="space-y-2">
                <label for="custom-desc" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">MÔ TẢ CHI TIẾT Ý TƯỞNG</label>
                <textarea
                  id="custom-desc"
                  bind:value={customDescription}
                  rows="3"
                  placeholder="Nhập ý tưởng video, mô tả sản phẩm dịch vụ, hoặc điểm nổi bật bạn muốn quảng cáo..."
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 resize-none leading-relaxed"
                ></textarea>
                <p class="text-[9px] font-mono text-gray-500 leading-normal">
                  Viết bất kỳ ý tưởng thô nào của bạn, AI sẽ xây dựng thành kịch bản chuyên nghiệp.
                </p>
              </div>
            {/if}

            <!-- Settings Grid: Aspect Ratio & Duration -->
            <div class="grid grid-cols-2 gap-4">
              <!-- Aspect Ratio -->
              <div class="space-y-2">
                <label for="aspect-ratio-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">KHUNG HÌNH (THIẾT BỊ)</label>
                <select
                  id="aspect-ratio-select"
                  bind:value={aspectRatio}
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="9:16">Dọc (9:16) - TikTok/Reels</option>
                  <option value="16:9">Ngang (16:9) - YouTube/PC</option>
                  <option value="1:1">Vuông (1:1) - Instagram</option>
                </select>
              </div>

              <!-- Duration -->
              <div class="space-y-2">
                <label for="duration-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">THỜI LƯỢNG MỤC TIÊU</label>
                <select
                  id="duration-select"
                  bind:value={targetDuration}
                  class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value={15}>15 giây (Cực ngắn)</option>
                  <option value={30}>30 giây (Tiêu chuẩn)</option>
                  <option value={60}>60 giây (Chi tiết)</option>
                  <option value={90}>90 giây (Kể chuyện)</option>
                </select>
              </div>
            </div>

            <!-- Style selection -->
            <div class="space-y-2">
              <label for="style-select" class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">PHONG CÁCH / XU HƯỚNG VIDEO</label>
              <select
                id="style-select"
                bind:value={selectedStyleId}
                class="w-full bg-[#111] border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                {#if styles.length === 0}
                  <option value="">Không tìm thấy phong cách nào</option>
                {:else}
                  {#each styles as style}
                    <option value={style.id}>[{style.platform}] {style.name}</option>
                  {/each}
                {/if}
              </select>
            </div>

            <!-- Style instruction details panel -->
            {#if styles.find(s => s.id === selectedStyleId)}
              {@const currentStyle = styles.find(s => s.id === selectedStyleId)!}
              <div class="bg-[#0c0c0c] border border-cyan-500/10 rounded-lg p-3 space-y-2">
                <span class="text-[9px] font-mono text-cyan-400 font-bold uppercase tracking-widest block font-sans">CHI TIẾT PHONG CÁCH</span>
                <div class="text-[10px] space-y-1 text-gray-400 leading-relaxed font-sans">
                  <p><strong>Cấu trúc Hook:</strong> <span class="text-gray-300 italic">{currentStyle.hook_template}</span></p>
                  <p class="line-clamp-2"><strong>Chỉ dẫn:</strong> {currentStyle.style_instruction}</p>
                </div>
              </div>
            {/if}
          </form>
        {/if}
      </div>

      <!-- Footer Buttons -->
      {#if !isGenerating}
        <div class="flex items-center gap-3 border-t border-gray-900 pt-4 mt-6">
          <button
            onclick={() => { isDrawerOpen = false; }}
            class="flex-1 py-2 bg-gray-900 hover:bg-gray-800 text-gray-300 text-xs font-semibold rounded-lg border border-gray-800 transition-colors"
          >
            Hủy bỏ
          </button>
          <button
            onclick={handleGenerate}
            class="flex-1 py-2 bg-gradient-to-r from-pink-500 to-cyan-500 text-black text-xs font-bold rounded-lg hover:opacity-90 shadow-md shadow-cyan-500/10 transition-all"
          >
            Bắt đầu sinh AI
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}
