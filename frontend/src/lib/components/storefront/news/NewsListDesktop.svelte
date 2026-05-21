<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import ImageWithFallback from '../ui/ImageWithFallback.svelte';

  interface NewsItem {
    id: string;
    slug: string;
    title: string;
    excerpt?: string;
    featuredImage: string;
    category?: string;
    createdAt?: string;
  }

  interface Props {
    newsList: NewsItem[];
    categoryName?: string;
  }

  let { newsList = [], categoryName = "Bài viết" }: Props = $props();

  // Elite V2.2: Enhanced News Metadata (Viral 2026 Protocol)
  let selectedTag = $state<string | null>(null);

  // Hàm phân loại ngữ nghĩa động từ văn bản bài viết (Zero-Migration)
  const getArticleTags = (item: NewsItem): string[] => {
    const title = (item.title || "").toLowerCase();
    const excerpt = (item.excerpt || "").toLowerCase();
    const text = `${title} ${excerpt}`;
    
    const tags: string[] = [];
    if (text.includes("skin") || text.includes("aging") || text.includes("cleansing") || text.includes("hydration") || text.includes("da") || text.includes("dưỡng") || text.includes("rửa") || text.includes("cổ")) {
      tags.push("DƯỠNG DA");
    }
    if (text.includes("inspiration") || text.includes("story") || text.includes("cảm hứng") || text.includes("hành trình") || text.includes("chia sẻ") || text.includes("lối sống")) {
      tags.push("CẢM HỨNG");
    }
    if (text.includes("trend") || text.includes("strategies") || text.includes("future") || text.includes("xu hướng") || text.includes("2026") || text.includes("mới") || text.includes("lão hóa")) {
      tags.push("XU HƯỚNG");
    }
    if (text.includes("deal") || text.includes("discount") || text.includes("voucher") || text.includes("ưu đãi") || text.includes("khuyến mãi") || text.includes("quà")) {
      tags.push("ƯU ĐÃI");
    }
    if (text.includes("tips") || text.includes("fundamentals") || text.includes("how to") || text.includes("mẹo") || text.includes("hướng dẫn") || text.includes("nguyên tắc") || text.includes("cách")) {
      tags.push("MẸO HAY");
    }
    if (text.includes("health") || text.includes("healthy") || text.includes("sức khỏe") || text.includes("lão hóa") || text.includes("dinh dưỡng")) {
      tags.push("SỨC KHỎE");
    }
    
    if (tags.length === 0) tags.push("MẸO HAY");
    return tags;
  };

  /** Format ISO datetime → "THÁNG MM, YYYY" */
  const formatArticleDate = (iso?: string): string => {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return '';
      const month = String(d.getMonth() + 1).padStart(2, '0');
      return `THÁNG ${month}, ${d.getFullYear()}`;
    } catch { return ''; }
  };

  const enhancedNews = $derived(() => {
    return newsList.map((item, i) => {
      const tags = getArticleTags(item);
      const featImg = item.featuredImage || (item as any).featured_image || "";
      const created = item.createdAt || (item as any).created_at;
      return {
        ...item,
        featuredImage: featImg,
        tags,
        category: tags[0] || 'LÀM ĐẸP',
        date: formatArticleDate(created)
      };
    });
  });

  const filteredNews = $derived(() => {
    const list = enhancedNews();
    const activeTag = selectedTag;
    let result = activeTag 
      ? list.filter(item => item.tags.includes(activeTag))
      : list;

    // Elite V2.2: Option B - Prevent duplication by hiding articles that are already featured
    if (list.length > 5) {
      const featuredIds = featuredNews().map(f => f.id);
      result = result.filter(item => !featuredIds.includes(item.id));
    }
    return result;
  });

  const featuredNews = $derived(() => enhancedNews().slice(0, 5));

  function toggleTag(tag: string) {
    if (selectedTag === tag) {
      selectedTag = null;
    } else {
      selectedTag = tag;
    }
  }
</script>

<div class="bg-[#F5F5F5] min-h-[50vh] pb-12 text-gray-900">
  <!-- BREADCRUMB & TITLE BAR (Standard Elite) -->
  <div class="bg-white border-b border-gray-100">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-6">
      <nav class="flex items-center gap-2 text-[12px] text-gray-400 mb-4 font-medium tracking-wider">
        <a href="/" class="hover:text-[#ee4d2d] transition-colors">Trang chủ</a>
        <span>/</span>
        <span class="text-gray-900">{categoryName}</span>
      </nav>

      <div class="flex items-center gap-6" in:fade={{duration: 800}}>
        <h1 class="text-3xl font-black text-gray-900 tracking-tight italic" in:fly={{x: -20, duration: 1000}}>{categoryName}</h1>
        <div class="h-px w-12 bg-[#ee4d2d]" in:scale={{duration: 1000, delay: 200, start: 0}}></div>
        <span class="text-[10px] font-black text-[#ee4d2d] tracking-[0.1em] animate-pulse">Hướng dẫn nâng cao</span>
      </div>
    </div>
  </div>

  <!-- MAIN CONTENT: Sidebar + News Grid -->
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-8 flex gap-8">
    
    <!-- LEFT SIDEBAR: Featured & Topics -->
    {#if categoryName !== 'CHÍNH SÁCH'}
    <aside class="w-[280px] shrink-0 space-y-8 hidden lg:block">
      <!-- Sidebar Header -->
      <div class="bg-black text-white p-5 rounded-none shadow-xl transform hover:-translate-y-1 transition-all duration-500 overflow-hidden relative group">
        <div class="absolute inset-0 bg-gradient-to-tr from-red-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
        <h2 class="text-[12px] font-black tracking-[0.2em] relative z-10 flex items-center gap-3">
           <div class="w-1.5 h-1.5 bg-red-600 rounded-full animate-pulse"></div>
           Bản tin nổi bật
        </h2>
      </div>

      <!-- Featured List -->
      <div class="space-y-6">
        {#each featuredNews() as news, i}
          <a href="/{news.slug}.html" class="group flex gap-4 items-start" in:fly={{y: 20, duration: 800, delay: 100 * i}}>
            <div class="w-20 h-20 shrink-0">
                <ImageWithFallback src={news.featuredImage} alt={news.title} aspectRatio="aspect-square" class="rounded-none border border-gray-100" />
            </div>
            <div class="flex flex-col gap-1">
                <span class="text-[9px] font-black text-red-600 tracking-widest">{news.category}</span>
                <h3 class="text-[13px] font-bold text-gray-800 line-clamp-2 leading-tight group-hover:text-red-600 transition-colors">
                  {news.title}
                </h3>
            </div>
          </a>
          {#if i < featuredNews().length - 1}
            <div class="h-px w-full bg-gray-100"></div>
          {/if}
        {/each}
      </div>

      <!-- Viral Tag Cloud -->
      <div class="bg-white p-6 border border-gray-100">
          <h4 class="text-[11px] font-black text-gray-400 tracking-widest mb-6">Chủ đề hot</h4>
          <div class="flex flex-wrap gap-2">
            {#each ['DƯỠNG DA', 'CẢM HỨNG', 'XU HƯỚNG', 'ƯU ĐÃI', 'MẸO HAY', 'SỨC KHỎE'] as tag}
              <button 
                onclick={() => toggleTag(tag)}
                class="px-3 py-1.5 text-[10px] font-black tracking-tighter border transition-all active:scale-95 {selectedTag === tag ? 'bg-black text-white border-black shadow-lg shadow-black/10' : 'bg-gray-50 text-gray-500 border-transparent hover:border-black hover:bg-black hover:text-white'}">
                #{tag}
              </button>
            {/each}
          </div>
      </div>
    </aside>
    {/if}

    <!-- MAIN GRID AREA -->
    <main class="flex-1">
      {#if filteredNews().length > 0}
        <div class="grid grid-cols-1 {categoryName === 'CHÍNH SÁCH' ? 'md:grid-cols-3' : 'md:grid-cols-2'} gap-8" in:fade={{duration: 400}}>
          {#each filteredNews() as news, i (news.id)}
            <a href="/{news.slug}.html" 
               in:fly={{y: 40, duration: 1000, delay: 100 + (i * 50)}}
               class="group bg-white border border-gray-100 hover:border-red-600/20 hover:shadow-[0_20px_50px_rgba(0,0,0,0.08)] transition-all duration-500 overflow-hidden flex flex-col h-full transform hover:-translate-y-2">
              <!-- Image Frame -->
              <ImageWithFallback src={news.featuredImage} alt={news.title} aspectRatio="aspect-[16/10]" class="relative">
                  <div class="absolute top-4 left-4 z-10">
                      <span class="bg-black text-white px-3 py-1 text-[9px] font-black tracking-widest shadow-xl">
                        {news.category}
                      </span>
                  </div>
                  <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity z-10"></div>
              </ImageWithFallback>

              <!-- Content -->
              <div class="p-8 flex-1 flex flex-col">
                  <div class="flex items-center gap-2 mb-4">
                    <span class="text-[10px] font-black text-gray-400 tracking-widest">{news.date}</span>
                    <div class="w-1 h-1 bg-gray-300 rounded-full"></div>
                    <span class="text-[10px] font-black text-red-600 tracking-widest animate-pulse">Mới</span>
                  </div>

                  <h2 class="text-xl font-black text-gray-900 mb-4 line-clamp-2 leading-tight tracking-tight group-hover:text-red-600 transition-colors">
                    {news.title}
                  </h2>

                  <p class="text-gray-500 text-sm line-clamp-3 leading-relaxed font-medium mb-6">
                    {news.excerpt || ''}
                  </p>

                  <div class="mt-auto pt-6 border-t border-gray-50 flex items-center justify-between">
                      <div class="flex items-center gap-2 text-[11px] font-black tracking-widest text-gray-900 group-hover:text-red-600 transition-all">
                        Đọc tiếp
                        <svg class="w-4 h-4 transform group-hover:translate-x-2 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                        </svg>
                      </div>
                  </div>
              </div>
            </a>
          {/each}
        </div>
      {:else}
        <!-- Premium Empty State -->
        <div class="bg-white border border-gray-100 p-16 flex flex-col items-center justify-center text-center space-y-6" in:fade={{duration: 600}}>
          <div class="w-16 h-16 rounded-full bg-gray-50 flex items-center justify-center">
            <svg class="w-8 h-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <div class="space-y-2">
            <h3 class="text-lg font-black text-gray-800 tracking-tight">Không tìm thấy bài viết nào</h3>
            <p class="text-sm text-gray-400 font-medium max-w-sm">Hiện tại chưa có bài viết nào thuộc chủ đề #{selectedTag}. Sếp vui lòng chọn chủ đề khác hoặc bấm nút bên dưới để xem lại tất cả bài viết.</p>
          </div>
          <button 
            onclick={() => selectedTag = null}
            class="px-8 py-3 bg-black text-white text-[10px] font-black tracking-widest hover:bg-red-600 transition-all active:scale-95">
            XEM TẤT CẢ BÀI VIẾT
          </button>
        </div>
      {/if}

      <!-- Pagination Placeholder (Elite Style) -->
      {#if categoryName !== 'CHÍNH SÁCH'}
      <div class="mt-16 flex justify-center border-t border-gray-100 pt-10">
          <button class="px-10 py-4 bg-white border border-gray-200 text-[11px] font-black tracking-[0.1em] hover:bg-black hover:text-white hover:border-black transition-all shadow-sm active:scale-95">
            Xem thêm tin bài
          </button>
      </div>
      {/if}
    </main>
  </div>
</div>

<style>
  :global(.line-clamp-2) {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  :global(.line-clamp-3) {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>