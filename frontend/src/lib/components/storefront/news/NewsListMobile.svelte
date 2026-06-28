<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import Search from "@lucide/svelte/icons/search";
  import X from "@lucide/svelte/icons/x";
  import ImageWithFallback from '../ui/ImageWithFallback.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

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
    serverTotal?: number;
  }
  let { newsList = [], categoryName = "Tin tức", serverTotal = 0 }: Props = $props();

  let allNews = $state<NewsItem[]>([]);
  let currentOffset = $state(0);
  let isLoading = $state(false);
  let currentTotal = $state(serverTotal);

  $effect(() => {
    allNews = [...newsList];
    currentOffset = newsList.length;
    currentTotal = serverTotal;
  });

  const ui = getClientUi();
  const hotTopics = $derived(
    ui.settings?.news_tags?.tags_map
      ? Object.keys(ui.settings.news_tags.tags_map)
      : ['DƯỠNG DA', 'CẢM HỨNG', 'XU HƯỚNG', 'ƯU ĐÃI', 'MẸO HAY', 'SỨC KHỎE']
  );

  async function loadMore() {
    if (isLoading) return;
    if (allNews.length > 0 && allNews.length >= currentTotal) return;
    isLoading = true;
    try {
      const tagParam = selectedTag ? `&tag=${encodeURIComponent(selectedTag)}` : '';
      const res = await fetch(`/api/v1/client/news?limit=20&offset=${currentOffset}${tagParam}`);
      if (res.ok) {
        const data = await res.json();
        const newItems = (Array.isArray(data) ? data : ((data.data ?? data.items ?? []) as unknown[])) as NewsItem[];
        allNews = [...allNews, ...newItems];
        currentOffset += newItems.length;
        if (data && typeof data === 'object' && 'total' in data) {
          currentTotal = data.total;
        }
      }
    } catch (e) {
      console.error('[LOAD MORE NEWS FAILED]', e);
    } finally {
      isLoading = false;
    }
  }

  function setupInfiniteScroll(node: HTMLElement) {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        loadMore();
      }
    }, { threshold: 0.1 });
    observer.observe(node);
    return {
      destroy() {
        observer.unobserve(node);
      }
    };
  }

  const searchStore = getSearchStore();
  let searchQuery = $state("");
  const selectedTag = $derived(page.url.searchParams.get('tag'));

  // Hàm phân loại ngữ nghĩa động từ văn bản bài viết (Zero-Migration)
  const getArticleTags = (item: NewsItem): string[] => {
    const title = (item.title || "").toLowerCase();
    const excerpt = (item.excerpt || "").toLowerCase();
    const text = `${title} ${excerpt}`;
    
    const tags_map = ui.settings?.news_tags?.tags_map || {
      "DƯỠNG DA": ["skin", "aging", "cleansing", "hydration", "da", "dưỡng", "rửa", "cổ"],
      "CẢM HỨNG": ["inspiration", "story", "cảm hứng", "hành trình", "chia sẻ", "lối sống"],
      "XU HƯỚNG": ["trend", "strategies", "future", "xu hướng", "2026", "mới", "lão hóa"],
      "ƯU ĐÃI": ["deal", "discount", "voucher", "ưu đãi", "khuyến mãi", "quà"],
      "MẸO HAY": ["tips", "fundamentals", "how to", "mẹo", "hướng dẫn", "nguyên tắc", "cách"],
      "SỨC KHỎE": ["health", "healthy", "sức khỏe", "lão hóa", "dinh dưỡng"]
    };

    const tags: string[] = [];
    for (const [tagKey, keywords] of Object.entries(tags_map)) {
      const tagLower = tagKey.toLowerCase();
      const hasKeywordMatch = keywords.some(kw => text.includes(kw.toLowerCase()));
      const hasTagNameMatch = text.includes(tagLower);
      if (hasKeywordMatch || hasTagNameMatch) {
        tags.push(tagKey);
      }
    }
    
    if (tags.length === 0) {
      const keys = Object.keys(tags_map);
      tags.push(keys.includes("MẸO HAY") ? "MẸO HAY" : (keys[0] || "MẸO HAY"));
    }
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
    return allNews.map((item, i) => {
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

  const filteredNewsList = $derived(() => {
    let list = enhancedNews();
    const activeTag = selectedTag;
    
    // 1. Lọc theo tag
    if (activeTag) {
      list = list.filter(item => item.tags.includes(activeTag));
    }
    
    // 2. Lọc theo thanh tìm kiếm
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(n => 
        n.title.toLowerCase().includes(q) || 
        (n.excerpt || '').toLowerCase().includes(q)
      );
    }
    
    return list;
  });

  function toggleTag(tag: string) {
    const url = new URL(page.url.href);
    if (selectedTag === tag) {
      url.searchParams.delete('tag');
    } else {
      url.searchParams.set('tag', tag);
    }
    goto(url.pathname + url.search, { replaceState: true, noScroll: true });
  }

  function resetFilters() {
    searchQuery = "";
    const url = new URL(page.url.href);
    url.searchParams.delete('tag');
    goto(url.pathname + url.search, { replaceState: true, noScroll: true });
  }
</script>

<div class="min-h-screen bg-[#F7F8F9] pb-24">
  <!-- 1. Synchronized Header (Standard osmo Pattern) -->
  <header class="sticky top-0 z-40 bg-white/95 backdrop-blur-xl border-b border-gray-100 flex flex-col shadow-sm">
    <!-- Row 1: Back + Search (System Trigger) -->
    <div class="px-2 py-1 flex items-center gap-2 h-14">
       <button onclick={() => history.back()} class="p-2 text-gray-900 flex-shrink-0"><ChevronLeft size={24} /></button>
       <div 
          onclick={() => searchStore.isOverlayOpen = true}
          role="presentation"
          class="flex-1 min-w-0 h-[40px] bg-gray-100 rounded-xl flex items-center px-4 gap-2 border border-gray-100 cursor-pointer"
        >
          <Search size={16} class="text-gray-400 flex-shrink-0" />
          <span class="text-[13px] text-gray-400 font-bold truncate">Tìm kiếm kiến thức AI, bài viết...</span>
       </div>
    </div>

    <!-- Row 2: Category Bubble Scroller -->
    <div class="px-4 pb-4 overflow-x-auto scrollbar-hide flex items-center gap-3 whitespace-nowrap pt-1">
      <a 
        href="/bai-viet"
        onclick={(e) => {
          e.preventDefault();
          resetFilters();
        }}
        class="px-5 py-1.5 rounded-none text-[10px] font-black tracking-widest transition-all active:scale-95 inline-block {!selectedTag ? 'bg-[#C18F7E] text-white shadow-lg shadow-[#C18F7E]/20' : 'bg-gray-50 text-gray-400 border border-gray-100'}">
        TẤT CẢ
      </a>
      {#each hotTopics as tag}
        {@const isActive = selectedTag === tag}
        <a 
          href={isActive ? '/bai-viet' : `/bai-viet?tag=${encodeURIComponent(tag)}`}
          onclick={(e) => {
            e.preventDefault();
            toggleTag(tag);
          }}
          class="px-5 py-1.5 rounded-none text-[10px] font-black tracking-widest border transition-all active:scale-95 inline-block {isActive ? 'bg-[#C18F7E] text-white border-[#C18F7E] shadow-lg shadow-[#C18F7E]/20' : 'bg-gray-50 text-gray-400 border-gray-100'}"
        >
          #{tag}
        </a>
      {/each}
    </div>
  </header>

  <div class="px-4 py-6 space-y-8">
    {#each filteredNewsList() as news, i (news.id)}
      {#if i === 0 && !searchQuery}
        <!-- 2. Hero Spotlight Card (Only show if not searching) -->
        <a 
          href="/{news.slug}.html"
          class="block group bg-white overflow-hidden shadow-xl shadow-black/5 active:scale-[0.98] transition-all duration-500 border border-gray-100"
          in:fly={{ y: 20, duration: 600 }}
        >
          <div class="aspect-[16/10] relative overflow-hidden bg-gray-50 border-b border-gray-100">
             <ImageWithFallback 
                src={news.featuredImage || "/home/lv/.gemini/antigravity/brain/9ea17a17-8f07-46fd-b120-9823cc68a3a5/osmo_news_hero_placeholder_1776682173691.png"} 
                alt={news.title} 
                aspectRatio="aspect-[16/10]" 
                class="w-full h-full object-cover scale-105 group-hover:scale-100 transition-transform duration-[8s]" 
             />
             <div class="absolute top-4 left-4 z-10">
                 <span class="bg-[#C18F7E] text-white px-3 py-1 text-[8px] font-black tracking-[0.2em] uppercase">Trending</span>
             </div>
          </div>
          <div class="p-6 space-y-3 bg-white">
            <div class="flex items-center gap-2">
                <span class="text-[9px] font-black text-[#C18F7E] tracking-widest">{news.category || 'LÀM ĐẸP'}</span>
                <div class="w-1 h-1 bg-gray-300 rounded-full"></div>
                <span class="text-[9px] font-black text-gray-400 tracking-widest uppercase">{news.date}</span>
            </div>
            <h3 class="text-[20px] font-black text-gray-900 leading-snug tracking-tight group-hover:text-[#C18F7E] transition-colors italic">{news.title}</h3>
            <p class="text-[12px] text-gray-500 line-clamp-3 leading-relaxed font-medium">{news.excerpt || ''}</p>
          </div>
        </a>
      {:else}
        <!-- 3. Standard Magazine Card -->
        <a 
          href="/{news.slug}.html"
          class="block bg-white group active:scale-[0.98] transition-all duration-300 shadow-xl shadow-black/5 border border-gray-100 p-4"
          in:fly={{ y: 20, delay: i * 50, duration: 500 }}
        >
          <div class="flex gap-4">
            <div class="w-24 h-24 flex-shrink-0 relative overflow-hidden">
               <ImageWithFallback src={news.featuredImage} alt={news.title} aspectRatio="aspect-square" class="object-cover" />
               <div class="absolute inset-0 bg-[#C18F7E]/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            </div>
            <div class="flex flex-col flex-1 justify-between py-1">
              <div class="space-y-1.5">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-black text-[#C18F7E] tracking-widest">{news.category || 'Tin tức'}</span>
                    <span class="text-[8px] text-gray-300 font-bold">1H TRƯỚC</span>
                </div>
                <h3 class="text-[14px] font-black text-gray-900 leading-snug line-clamp-2 group-hover:text-[#C18F7E] transition-colors italic">{news.title}</h3>
              </div>
              <div class="flex items-center gap-4 pt-2 border-t border-gray-50">
                <span class="text-[8px] text-gray-400 font-bold tracking-tighter">4 min read</span>
                <span class="text-[8px] text-gray-400 font-bold tracking-tighter">1.2k views</span>
              </div>
            </div>
          </div>
        </a>
      {/if}
    {/each}

    {#if filteredNewsList().length === 0}
       <div class="bg-white border border-gray-100 p-12 flex flex-col items-center justify-center text-center space-y-6 shadow-sm" in:fade={{duration: 600}}>
          <div class="w-16 h-16 rounded-full bg-gray-50 flex items-center justify-center">
             <svg class="w-8 h-8 text-[#C18F7E]/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
               <path stroke-linecap="round" stroke-linejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10l4 4v10a2 2 0 01-2 2z" />
             </svg>
          </div>
          <div class="space-y-2">
            <p class="text-[12px] font-black text-gray-800 tracking-wider">KHÔNG TÌM THẤY BÀI VIẾT NÀO</p>
            <p class="text-[10px] text-gray-400 font-medium max-w-[240px] mx-auto leading-relaxed">
              Không tìm thấy bài viết nào phù hợp với bộ lọc chủ đề hoặc tìm kiếm hiện tại của Sếp.
            </p>
          </div>
          <a 
            href="/bai-viet"
            onclick={(e) => {
              e.preventDefault();
              resetFilters();
            }} 
            class="px-8 py-3 bg-[#C18F7E] text-white text-[9px] font-black tracking-widest shadow-lg shadow-[#C18F7E]/20 transition-all active:scale-95 inline-block">
            XÓA TẤT CẢ BỘ LỌC
          </a>
       </div>
    {/if}

    <!-- Pagination (Elite Style) -->
    {#if categoryName !== 'CHÍNH SÁCH'}
      {#if allNews.length < (serverTotal || 0)}
        <div class="mt-8 flex flex-col items-center justify-center pt-6 gap-4" use:setupInfiniteScroll>
            <button 
              onclick={loadMore}
              disabled={isLoading}
              class="w-full py-4 bg-white border border-gray-200 text-[11px] font-black tracking-[0.1em] hover:bg-[#C18F7E] hover:text-white transition-all shadow-sm active:scale-95 disabled:opacity-50">
              {#if isLoading}
                ĐANG TẢI...
              {:else}
                XEM THÊM TIN BÀI
              {/if}
            </button>
        </div>
      {:else if (serverTotal || 0) > 0}
        <div class="mt-8 text-center py-6 pt-6">
           <span class="text-[9px] font-black text-gray-400 tracking-widest opacity-60 flex items-center justify-center gap-3">
             <div class="w-8 h-px bg-gray-200"></div>
             ĐÃ HIỂN THỊ TOÀN BỘ {serverTotal} BÀI VIẾT
             <div class="w-8 h-px bg-gray-200"></div>
           </span>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  :global(body) {
    background-color: #F7F8F9;
  }
</style>