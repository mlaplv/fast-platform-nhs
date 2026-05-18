<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { goto } from '$app/navigation';
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import Search from "@lucide/svelte/icons/search";
  import X from "@lucide/svelte/icons/x";
  import ImageWithFallback from '../ui/ImageWithFallback.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';

  interface NewsItem {
     id: string;
     slug: string;
     title: string;
     summary: string;
     featuredImage: string;
     category?: string;
  }
  interface Props {
    newsList: NewsItem[];
    categoryName?: string;
  }
  let { newsList = [], categoryName = "Tin tức" }: Props = $props();

  const searchStore = getSearchStore();
  let searchQuery = $state("");
  let selectedTag = $state<string | null>(null);

  // Hàm phân loại ngữ nghĩa động từ văn bản bài viết (Zero-Migration)
  const getArticleTags = (item: NewsItem): string[] => {
    const title = (item.title || "").toLowerCase();
    const summary = (item.summary || "").toLowerCase();
    const text = `${title} ${summary}`;
    
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

  const enhancedNews = $derived(() => {
    return newsList.map((item, i) => {
      const tags = getArticleTags(item);
      return {
        ...item,
        tags,
        category: tags[0] || 'LÀM ĐẸP',
        date: item.date || 'THÁNG 03, 2026'
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
        n.summary.toLowerCase().includes(q)
      );
    }
    
    return list;
  });

  function toggleTag(tag: string) {
    if (selectedTag === tag) {
      selectedTag = null;
    } else {
      selectedTag = tag;
    }
  }

  function resetFilters() {
    selectedTag = null;
    searchQuery = "";
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
      <button 
        onclick={() => selectedTag = null}
        class="px-5 py-1.5 rounded-none text-[10px] font-black tracking-widest transition-all active:scale-95 {!selectedTag ? 'bg-[#C18F7E] text-white shadow-lg shadow-[#C18F7E]/20' : 'bg-gray-50 text-gray-400 border border-gray-100'}">
        TẤT CẢ
      </button>
      {#each ['DƯỠNG DA', 'CẢM HỨNG', 'XU HƯỚNG', 'ƯU ĐÃI', 'MẸO HAY', 'SỨC KHỎE'] as tag}
        <button 
          onclick={() => toggleTag(tag)}
          class="px-5 py-1.5 rounded-none text-[10px] font-black tracking-widest border transition-all active:scale-95 {selectedTag === tag ? 'bg-[#C18F7E] text-white border-[#C18F7E] shadow-lg shadow-[#C18F7E]/20' : 'bg-gray-50 text-gray-400 border-gray-100'}"
        >
          #{tag}
        </button>
      {/each}
    </div>
  </header>

  <div class="px-4 py-6 space-y-8">
    {#each filteredNewsList() as news, i (news.id)}
      {#if i === 0 && !searchQuery}
        <!-- 2. Hero Spotlight Card (Only show if not searching) -->
        <a 
          href="/{news.slug}"
          class="block group relative bg-white overflow-hidden shadow-2xl shadow-black/10 active:scale-[0.98] transition-all duration-500"
          in:fly={{ y: 20, duration: 600 }}
        >
          <div class="aspect-[16/10] relative overflow-hidden">
             <ImageWithFallback 
                src={news.featuredImage || "/home/lv/.gemini/antigravity/brain/9ea17a17-8f07-46fd-b120-9823cc68a3a5/osmo_news_hero_placeholder_1776682173691.png"} 
                alt={news.title} 
                aspectRatio="aspect-video" 
                class="w-full h-full object-cover scale-105 group-hover:scale-100 transition-transform duration-[8s]" 
             />
             <div class="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent"></div>
          </div>
          <div class="absolute bottom-0 inset-x-0 p-6 space-y-2">
            <div class="flex items-center gap-3">
                <span class="bg-[#C18F7E] text-white px-2.5 py-1 text-[8px] font-black tracking-[0.2em] italic">osmo News</span>
                <span class="text-[9px] text-white/60 font-medium">Trending now</span>
            </div>
            <h3 class="text-2xl font-black text-white leading-tight tracking-tighter italic">{news.title}</h3>
            <p class="text-[12px] text-white/70 line-clamp-2 leading-relaxed font-medium">{news.summary}</p>
          </div>
        </a>
      {:else}
        <!-- 3. Standard Magazine Card -->
        <a 
          href="/{news.slug}"
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
          <button 
            onclick={resetFilters} 
            class="px-8 py-3 bg-[#C18F7E] text-white text-[9px] font-black tracking-widest shadow-lg shadow-[#C18F7E]/20 transition-all active:scale-95">
            XÓA TẤT CẢ BỘ LỌC
          </button>
       </div>
    {/if}
  </div>
</div>

<style>
  :global(body) {
    background-color: #F7F8F9;
  }
</style>