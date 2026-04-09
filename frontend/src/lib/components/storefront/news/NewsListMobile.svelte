<script lang="ts">
  interface NewsItem {
     id: string;
     slug: string;
     title: string;
     summary: string;
     image: string;
  }
  interface Props {
    newsList: NewsItem[];
  }
  let { newsList = [] }: Props = $props();
</script>

<div class="h-[calc(100vh-env(safe-area-inset-bottom)-60px)] w-screen overflow-y-scroll snap-y snap-mandatory bg-black">
  {#each newsList as news (news.id)}
    <div class="snap-start h-full w-full relative flex items-center justify-center bg-black overflow-hidden">
      <!-- Immersive Image with Parallax-ready feel -->
      <img src={news.image} alt={news.title} class="absolute inset-0 w-full h-full object-cover z-0 opacity-80" />
      <div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent z-0"></div>

      <!-- News Info Overlay (Elite Mobile Style) -->
      <div class="absolute bottom-0 left-0 w-full p-6 pb-20 z-10 bg-gradient-to-t from-black via-black/80 to-transparent">
        <div class="flex items-center gap-3 mb-4">
            <span class="bg-red-600 text-white px-3 py-1 text-[10px] font-black uppercase tracking-widest inline-block shadow-2xl shadow-red-600/40">
              Tạp chí Elite
            </span>
            <div class="h-px w-8 bg-white/20"></div>
            <span class="text-white/40 text-[9px] font-black uppercase tracking-widest">Đang thịnh hành</span>
        </div>

        <h3 class="text-2xl font-black mb-4 leading-tight tracking-tighter italic text-white uppercase">{news.title}</h3>
        <p class="text-slate-300 text-[13px] leading-relaxed font-medium line-clamp-3 mb-8 opacity-80">{news.summary}</p>

        <a
          href="/{news.slug}.p{news.id}"
          class="inline-flex items-center gap-3 bg-white text-black px-8 py-4 text-[11px] font-black uppercase tracking-[0.2em] transition-all shadow-2xl active:scale-95 border-b-4 border-gray-200"
        >
          Đọc bài viết <span>→</span>
        </a>
      </div>

      <!-- Action Overlay (Viral 2026 Mobile) -->
      <div class="absolute right-4 bottom-40 z-20 flex flex-col items-center gap-8">
        <button class="flex flex-col items-center text-white group outline-none">
          <div class="w-14 h-14 bg-white/5 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/10 mb-2 group-hover:scale-110 active:scale-90 transition-all shadow-2xl">
            <svg class="w-6 h-6 text-white fill-current" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          </div>
          <p class="text-[10px] font-black tracking-widest uppercase opacity-60">Thích</p>
        </button>
        
        <button class="flex flex-col items-center text-white group outline-none">
          <div class="w-14 h-14 bg-white/5 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/10 mb-2 group-hover:scale-110 active:scale-90 transition-all shadow-2xl">
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
          </div>
          <p class="text-[10px] font-black tracking-widest uppercase opacity-60">Bình luận</p>
        </button>

        <button class="flex flex-col items-center text-white group outline-none">
          <div class="w-14 h-14 bg-white/5 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/10 mb-2 group-hover:scale-110 active:scale-90 transition-all shadow-2xl">
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
          </div>
          <p class="text-[10px] font-black tracking-widest uppercase opacity-60">Chia sẻ</p>
        </button>
      </div>
    </div>
  {/each}
</div>

<style>
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>