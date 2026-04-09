<script lang="ts">
  interface Props {
    newsList: Array<{ id: string; slug: string; title: string; summary: string; image: string }>;
  }
  let { newsList }: Props = $props();
</script>

<div class="h-[calc(100vh-env(safe-area-inset-bottom)-60px)] w-screen overflow-y-scroll snap-y snap-mandatory bg-black">
  {#each newsList as news (news.id)}
    <div class="snap-start h-full w-full relative flex items-center justify-center bg-black">
      <!-- Immersive Image -->
      <img src={news.image} alt={news.title} class="absolute inset-0 w-full h-full object-cover z-0" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent z-0"></div>

      <!-- News Info Overlay -->
      <div class="absolute bottom-0 left-0 w-full p-8 pb-12 z-10 bg-gradient-to-t from-black via-black/90 to-transparent">
        <span class="bg-red-600 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 inline-block shadow-lg shadow-red-600/40">
          Micsmo News
        </span>
        <h3 class="text-3xl font-black mb-4 leading-tight tracking-tighter italic text-white">{news.title}</h3>
        <p class="text-slate-200 text-sm leading-relaxed font-medium line-clamp-3 mb-8">{news.summary}</p>

        <a
          href="/{news.slug}.p{news.id}"
          class="inline-flex items-center gap-3 bg-white text-black px-6 py-3 rounded-full font-black text-xs uppercase tracking-widest hover:bg-red-600 hover:text-white transition-all shadow-xl active:scale-95"
        >
          Đọc bài viết <span>→</span>
        </a>
      </div>

      <!-- Action Overlay (Viral TikTok Style) -->
      <div class="absolute right-4 bottom-32 z-10 flex flex-col items-center gap-6">
        <button class="flex flex-col items-center text-white group">
          <div class="w-12 h-12 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center border border-white/20 mb-1 group-hover:scale-110 transition-transform">
            <span class="text-2xl">❤️</span>
          </div>
          <p class="text-[10px] font-black tracking-widest uppercase opacity-70">1.2k</p>
        </button>
        <button class="flex flex-col items-center text-white group">
          <div class="w-12 h-12 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center border border-white/20 mb-1 group-hover:scale-110 transition-transform">
            <span class="text-2xl">💬</span>
          </div>
          <p class="text-[10px] font-black tracking-widest uppercase opacity-70">89</p>
        </button>
        <button class="flex flex-col items-center text-white group">
          <div class="w-12 h-12 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center border border-white/20 mb-1 group-hover:scale-110 transition-transform">
            <span class="text-2xl">↪️</span>
          </div>
          <p class="text-[10px] font-black tracking-widest uppercase opacity-70">Share</p>
        </button>
      </div>
    </div>
  {/each}
</div>