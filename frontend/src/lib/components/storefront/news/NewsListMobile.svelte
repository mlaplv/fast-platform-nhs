<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import ImageWithFallback from '../ui/ImageWithFallback.svelte';

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
  }
  let { newsList = [] }: Props = $props();
</script>

<div class="min-h-screen bg-[#F7F8F9] pb-24 pt-4 px-4 space-y-4">
  <div class="flex items-center justify-between mb-6">
    <div class="flex flex-col">
      <span class="text-[10px] font-black uppercase tracking-[0.2em] {newsList[0]?.category === 'Chính sách' ? 'text-gray-400' : 'text-luxury-copper'}">
        {newsList[0]?.category === 'Chính sách' ? 'Hệ thống pháp lý' : 'Hướng dẫn nâng cao'}
      </span>
      <h2 class="text-xl font-bold text-gray-900 tracking-tighter">
        {newsList[0]?.category === 'Chính sách' ? 'Chính sách & Quy định' : 'Bài viết mới nhất'}
      </h2>
    </div>
    <div class="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm border border-gray-100">
       <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
    </div>
  </div>

  {#each newsList as news (news.id)}
    <a 
      href="/{news.slug}"
      class="block bg-white group active:scale-[0.98] transition-all duration-300 shadow-sm hover:shadow-md border border-gray-50 overflow-hidden"
    >
      <div class="flex gap-4 p-3">
        <!-- Thumbnail -->
        <div class="w-32 h-32 flex-shrink-0">
           <ImageWithFallback src={news.featuredImage} alt={news.title} aspectRatio="aspect-square" class="rounded-lg border border-gray-100" />
        </div>

        <!-- Meta -->
        <div class="flex flex-col justify-center flex-1">
          <div class="flex items-center gap-2 mb-2">
            <span class="bg-gray-100 text-gray-500 px-2 py-0.5 text-[8px] font-black uppercase tracking-widest rounded-sm">Micsmo News</span>
            <span class="text-[9px] text-gray-300 font-bold">12 giờ trước</span>
          </div>
          <h3 class="text-[14px] font-bold text-gray-900 leading-snug line-clamp-2 mb-2 group-hover:text-luxury-copper transition-colors">{news.title}</h3>
          <p class="text-[11px] text-gray-400 line-clamp-2 leading-relaxed italic">{news.summary}</p>
        </div>
      </div>
    </a>
  {/each}

  {#if newsList.length === 0}
     <div class="flex flex-col items-center justify-center py-20 text-center" in:fade>
        <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
           <svg class="w-8 h-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10l4 4v10a2 2 0 01-2 2z" /></svg>
        </div>
        <p class="text-xs font-black text-gray-400 uppercase tracking-widest">Không có bài viết nào</p>
     </div>
  {/if}
</div>

<style>
  :global(body) {
    background-color: #F7F8F9;
  }
</style>