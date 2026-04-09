<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';

  interface Props {
    article: { 
      title: string; 
      author: string; 
      publishedAt: string; 
      content: string; 
      image: string;
      category?: string;
    };
  }

  let { article }: Props = $props();

  // Mock related news for sidebar
  const relatedNews = [
    { title: "Bí kíp chăm sóc da mùa khô 2026", category: "BEAUTY", image: article.image },
    { title: "Top 5 serum đáng mua nhất năm", category: "TRENDS", image: article.image },
    { title: "Cách tối ưu hóa vận hành AI cho shop", category: "TECH", image: article.image }
  ];
</script>

<div class="news-detail-content pb-8 text-gray-900">
  <!-- BREADCRUMB & ELITE HEADER -->
  <div class="bg-white border-b border-gray-100 mb-8">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-6">
      <nav class="flex items-center gap-2 text-[12px] text-gray-400 mb-4 font-medium uppercase tracking-wider">
        <a href="/" class="hover:text-[#ee4d2d] transition-colors">Trang chủ</a>
        <span>/</span>
        <a href="/tin-tuc" class="hover:text-[#ee4d2d] transition-colors">Tin tức</a>
        <span>/</span>
        <span class="text-gray-900 line-clamp-1">{article.title}</span>
      </nav>

      <div class="flex items-center gap-6" in:fade={{duration: 800}}>
        <div class="h-px w-12 bg-red-600" in:scale={{duration: 1000, start: 0}}></div>
        <span class="text-[10px] font-black text-red-600 uppercase tracking-[0.3em] animate-pulse">Độc quyền Tạp chí Elite</span>
      </div>
    </div>
  </div>

  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 flex gap-8 items-start">
    <!-- MAIN ARTICLE AREA -->
    <main class="flex-1">
      <article 
        class="bg-white border border-gray-100 shadow-[0_20px_60px_rgba(0,0,0,0.04)] overflow-hidden"
        in:fly={{y: 40, duration: 1000}}
      >
        <!-- Hero Section -->
        <div class="p-8 md:p-12 pb-0">
            <div class="flex items-center gap-4 mb-8">
                <span class="bg-black text-white px-3 py-1 text-[10px] font-black uppercase tracking-widest">
                  {article.category || 'TẠP CHÍ ELITE'}
                </span>
                <div class="flex items-center gap-2 text-[11px] font-black text-gray-400 uppercase tracking-widest">
                  <span>{article.author === 'Xohi' || article.author === 'System' ? 'Ban biên tập Elite' : article.author}</span>
                  <div class="w-1 h-1 bg-gray-200 rounded-full"></div>
                  <span>{article.publishedAt}</span>
                </div>
            </div>

            <h1 class="text-4xl md:text-5xl font-black text-gray-900 mb-10 tracking-tighter leading-[1.1] uppercase italic">
              {article.title}
            </h1>
        </div>

        <!-- Featured Image -->
        <div class="px-8 md:px-12 mb-12">
            <div class="aspect-video w-full overflow-hidden bg-gray-50 border border-gray-100 group">
                <img src={article.image} alt={article.title} class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-[2000ms]" />
            </div>
        </div>

        <!-- Content Body (Elite Prose) -->
        <div class="p-8 md:p-12 pt-0 elite-prose">
            {@html article.content}
        </div>

        <!-- Social Share Bar -->
        <div class="px-8 md:px-12 py-8 bg-gray-50/50 border-t border-gray-100 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Chia sẻ bài viết:</span>
                <div class="flex gap-2">
                    {#each ['FB', 'ZL', 'CP'] as btn}
                        <button class="w-10 h-10 bg-white border border-gray-100 flex items-center justify-center text-[10px] font-black hover:bg-black hover:text-white hover:border-black transition-all">
                            {btn}
                        </button>
                    {/each}
                </div>
            </div>
            
            <button 
              onclick={() => window.scrollTo({top: 0, behavior: 'smooth'})}
              class="text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-black transition-colors flex items-center gap-2"
            >
                Quay lên đầu
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 15l7-7 7 7" /></svg>
            </button>
        </div>
      </article>

      <!-- Bottom Navigation -->
      <div class="mt-8 flex justify-between items-center">
          <a href="/tin-tuc" class="text-[11px] font-black uppercase tracking-widest text-[#ee4d2d] flex items-center gap-2 hover:gap-4 transition-all">
             <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M7 16l-4-4m0 0l4-4m-4 4h18" /></svg>
             Quay về trang tin
          </a>
      </div>
    </main>

    <!-- RIGHT SIDEBAR -->
    <aside class="w-[320px] shrink-0 space-y-8 hidden xl:block" in:fade={{duration: 1000, delay: 500}}>
        <!-- Related News -->
        <div class="bg-white border border-gray-100 p-8">
            <h2 class="text-[12px] font-black uppercase tracking-[0.2em] mb-8 flex items-center gap-3">
              <div class="w-1.5 h-1.5 bg-red-600 rounded-full animate-pulse"></div>
              BÀI VIẾT LIÊN QUAN
            </h2>
            
            <div class="space-y-8">
                {#each relatedNews as news}
                    <a href="#" class="group block space-y-3">
                        <div class="aspect-video bg-gray-100 overflow-hidden border border-gray-100">
                            <img src={news.image} alt={news.title} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                        </div>
                        <div>
                            <span class="text-[9px] font-black text-red-600 uppercase tracking-widest">{news.category}</span>
                            <h3 class="text-[14px] font-bold text-gray-800 line-clamp-2 leading-snug group-hover:text-red-600 transition-colors">
                              {news.title}
                            </h3>
                        </div>
                    </a>
                {/each}
            </div>
        </div>

        <!-- Newsletter / Community -->
        <div class="bg-black text-white p-8 relative overflow-hidden group">
            <div class="absolute inset-0 bg-gradient-to-br from-red-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <h3 class="text-[11px] font-black uppercase tracking-[0.3em] mb-4 relative z-10">Cộng đồng Elite</h3>
            <p class="text-[13px] text-gray-400 font-medium mb-6 relative z-10">Đăng ký nhận những tin bài chuyên sâu về chăm sóc da từ các chuyên gia AI.</p>
            <div class="relative z-10 space-y-2">
                <input type="email" placeholder="Email của bạn..." class="w-full bg-white/10 border-none px-4 py-3 text-sm focus:ring-1 focus:ring-red-600 outline-none transition-all placeholder:text-gray-600" />
                <button class="w-full bg-red-600 py-3 text-[10px] font-black uppercase tracking-widest hover:bg-white hover:text-black transition-all">Tham gia ngay</button>
            </div>
        </div>
    </aside>
  </div>
</div>

<style>
  :global(.elite-prose) {
    font-size: 1.125rem;
    line-height: 1.8;
    color: #374151;
  }
  
  :global(.elite-prose p) {
    margin-bottom: 2rem;
  }

  :global(.elite-prose h2) {
    font-size: 1.875rem;
    font-weight: 900;
    color: #111827;
    margin-top: 3rem;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
    letter-spacing: -0.025em;
  }

  :global(.elite-prose h3) {
    font-size: 1.5rem;
    font-weight: 800;
    color: #111827;
    margin-top: 2.5rem;
    margin-bottom: 1rem;
    text-transform: uppercase;
  }

  :global(.elite-prose img) {
    border-radius: 0.5rem;
    margin: 3rem 0;
    width: 100%;
    box-shadow: 0 10px 40px rgba(0,0,0,0.05);
  }

  :global(.elite-prose blockquote) {
    border-left: 4px solid #ee4d2d;
    padding-left: 2rem;
    font-style: italic;
    font-size: 1.25rem;
    color: #1f2937;
    margin: 3rem 0;
  }

  :global(.elite-prose ul) {
    list-style-type: disc;
    padding-left: 1.5rem;
    margin-bottom: 2rem;
  }

  :global(.elite-prose li) {
    margin-bottom: 0.75rem;
  }

  :global(.line-clamp-1) {
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  :global(.line-clamp-2) {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>