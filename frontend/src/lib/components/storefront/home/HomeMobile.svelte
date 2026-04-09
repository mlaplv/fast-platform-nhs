<script lang="ts">
  interface Props {
    videos: Array<{ id: string; url: string; title: string; likes: number; image: string }>;
  }
  let { videos }: Props = $props();
</script>

<div class="mobile-home-wrapper h-dvh w-screen overflow-y-scroll snap-y snap-mandatory bg-black">
  {#each videos as video (video.id)}
    <div class="snap-start h-full w-full relative flex items-center justify-center bg-black">

      <!-- Immersive Image -->
      <img src={video.image} alt={video.title} class="absolute inset-0 w-full h-full object-cover z-0" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent z-0"></div>

      <!-- Video Info Overlay -->
      <div class="absolute bottom-6 left-4 z-10 text-white p-2 w-[80%]">
        <h3 class="text-lg font-black mb-1 tracking-tight">@{video.title}</h3>
        <p class="text-xs font-medium text-slate-200 line-clamp-2">Trải nghiệm mỹ phẩm Elite V2.2 #skincare #micsmo #viral2026</p>
      </div>

      <!-- Action Overlay (Viral TikTok Style) -->
      <div class="absolute right-4 bottom-12 z-10 flex flex-col items-center gap-6">
        <button class="flex flex-col items-center text-white group">
          <span class="text-3xl drop-shadow-lg group-hover:scale-110 transition-transform">❤️</span>
          <p class="text-[10px] font-bold mt-1">{video.likes.toLocaleString()}</p>
        </button>
        <button class="flex flex-col items-center text-white group">
          <span class="text-3xl drop-shadow-lg group-hover:scale-110 transition-transform">💬</span>
          <p class="text-[10px] font-bold mt-1">128</p>
        </button>
        <button class="flex flex-col items-center text-white group">
          <span class="text-3xl drop-shadow-lg group-hover:scale-110 transition-transform">↪️</span>
          <p class="text-[10px] font-bold mt-1">Share</p>
        </button>
      </div>
    </div>
  {/each}
</div>
