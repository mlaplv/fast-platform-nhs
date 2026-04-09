<script lang="ts">
  interface Props {
    article: { title: string; author: string; publishedAt: string; content: string; image: string };
  }
  let { article }: Props = $props();
</script>

<div class="h-screen w-screen relative bg-black text-white overflow-y-scroll snap-y snap-mandatory">
  <!-- Immersive Image -->
  <img src={article.image} alt={article.title} class="absolute inset-0 w-full h-full object-cover z-0" />
  <div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent/60 z-0"></div>

  <!-- Content Overlay -->
  <div class="absolute bottom-0 left-0 w-full p-8 pb-16 z-10 bg-gradient-to-t from-black via-black/90 to-transparent">
    <span class="bg-red-600 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 inline-block">News</span>
    <h1 class="text-3xl font-black mb-4 leading-tight tracking-tighter">{article.title}</h1>
    <p class="text-xs text-slate-400 mb-6 font-bold uppercase tracking-widest">{article.author} • {article.publishedAt}</p>
    <p class="text-slate-200 text-sm leading-relaxed font-medium line-clamp-4">{article.content}</p>
  </div>
</div>