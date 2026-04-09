<script lang="ts">
  interface Props {
    newsList: Array<{ id: string; slug: string; title: string; summary: string; image: string }>;
  }
  let { newsList }: Props = $props();
</script>

<div class="max-w-7xl mx-auto p-6 md:p-12">
  <div class="mb-12">
    <span class="bg-red-600 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 inline-block shadow-lg shadow-red-600/20">
      Micsmo Mag
    </span>
    <h1 class="text-5xl font-black text-slate-900 tracking-tighter italic mb-4">GÓC TIN TỨC ELITE</h1>
    <div class="h-1 w-24 bg-red-600 rounded-full"></div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
    {#each newsList as news (news.id)}
      <a href="/{news.slug}.p{news.id}" class="group block bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-2xl transition-all duration-500 border border-slate-100 hover:-translate-y-2">
        <div class="aspect-video w-full overflow-hidden bg-slate-50 relative">
          <img src={news.image} alt={news.title} class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" />
          <div class="absolute inset-0 bg-black/10 group-hover:bg-transparent transition-colors"></div>
        </div>
        <div class="p-8">
          <div class="flex gap-2 mb-4">
            <span class="text-[10px] font-black uppercase tracking-widest text-red-600">Beauty</span>
            <span class="text-[10px] font-black uppercase tracking-widest text-slate-300">•</span>
            <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">Mar 2026</span>
          </div>
          <h2 class="font-black text-slate-900 text-xl mb-4 line-clamp-2 leading-tight group-hover:text-red-600 transition-colors uppercase tracking-tight">{news.title}</h2>
          <p class="text-slate-500 text-sm line-clamp-3 font-medium leading-relaxed">{news.summary}</p>
          <div class="mt-6 flex items-center gap-2 text-slate-900 font-black text-xs uppercase tracking-widest group-hover:gap-4 transition-all">
            Đọc tiếp <span>→</span>
          </div>
        </div>
      </a>
    {/each}
  </div>
</div>