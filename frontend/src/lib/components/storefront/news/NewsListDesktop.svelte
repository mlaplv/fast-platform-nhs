<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import ImageWithFallback from '../ui/ImageWithFallback.svelte';

  interface NewsItem {
    id: string;
    slug: string;
    title: string;
    summary: string;
    featuredImage: string;
    category?: string;
    date?: string;
  }

  interface Props {
    newsList: NewsItem[];
    categoryName?: string;
  }

  let { newsList = [], categoryName = "Bài viết" }: Props = $props();

  // Elite V2.2: Enhanced News Metadata (Viral 2026 Protocol)
  const enhancedNews = $derived(() => {
    return newsList.map((item, i) => ({
      ...item,
      category: item.category || (i % 2 === 0 ? 'LÀM ĐẸP' : 'LỐI SỐNG'),
      date: item.date || 'THÁNG 03, 2026'
    }));
  });

  const featuredNews = $derived(() => enhancedNews().slice(0, 5));
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
          <a href="/{news.slug}" class="group flex gap-4 items-start" in:fly={{y: 20, duration: 800, delay: 100 * i}}>
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
              <button class="px-3 py-1.5 bg-gray-50 text-[10px] font-black text-gray-500 hover:bg-black hover:text-white transition-all tracking-tighter border border-transparent hover:border-black">
                #{tag}
              </button>
            {/each}
          </div>
      </div>
    </aside>
    {/if}

    <!-- MAIN GRID AREA -->
    <main class="flex-1">
      <div class="grid grid-cols-1 {categoryName === 'CHÍNH SÁCH' ? 'md:grid-cols-3' : 'md:grid-cols-2'} gap-8">
        {#each enhancedNews() as news, i (news.id)}
          <a href="/{news.slug}" 
             in:fly={{y: 40, duration: 1000, delay: 200 + (i * 100)}}
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
                  {news.summary}
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